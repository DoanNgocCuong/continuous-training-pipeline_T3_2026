"""Model evaluation using transformers inference + scikit-learn metrics."""
import json
import logging
import os
import time
from typing import Iterable, List

from finetune.application.repositories.evaluator_repository import IEvaluatorRepository
from finetune.domain.entities import EvalResult
from finetune.domain.value_objects import EmotionLabel

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an emotion classifier for Pika Robot. "
    "Classify the emotion of the CURRENT response into exactly one of: "
    "happy, achievement, thinking, calm, surprised. "
    "Respond with only the emotion label."
)


class SklearnEvaluator(IEvaluatorRepository):
    """Evaluate a candidate model on benchmark/regression sets.

    Responsibilities (single): run model inference and compute metrics.
    - Loads local model (HF/Unsloth/AWQ) via transformers pipeline
    - Computes accuracy, macro F1, per-class F1, confusion matrix
    - Optionally computes regression pass rate on fixed edge-case set
    """

    def __init__(
        self,
        system_prompt: str = _SYSTEM_PROMPT,
        max_new_tokens: int = 8,
        device_map: str | None = "auto",
    ):
        self.system_prompt = system_prompt
        self.max_new_tokens = max_new_tokens
        self.device_map = device_map
        self._pipe = None
        self._loaded_model_path: str | None = None
        self._valid_labels = [e.value for e in EmotionLabel if e != EmotionLabel.UNKNOWN]

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def evaluate(
        self,
        model_path: str,
        test_path: str,
        regression_path: str | None = None,
    ) -> EvalResult:
        """Run eval on benchmark + (optional) regression set."""
        from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

        start = time.time()
        pipe = self._get_pipeline(model_path)

        test_rows = self._load_eval_jsonl(test_path)
        if not test_rows:
            raise ValueError(f"No test rows found at {test_path}")

        y_true = [self._extract_expected_label(r) for r in test_rows]
        prompts = [self._build_prompt(r["input_text"]) for r in test_rows]
        y_pred = self._predict_batch(pipe, prompts)

        acc = accuracy_score(y_true, y_pred)
        f1_macro = f1_score(y_true, y_pred, average="macro", labels=self._valid_labels)
        f1_per_class = dict(
            zip(
                self._valid_labels,
                f1_score(
                    y_true,
                    y_pred,
                    labels=self._valid_labels,
                    average=None,
                    zero_division=0.0,
                ),
            )
        )
        cm = confusion_matrix(y_true, y_pred, labels=self._valid_labels).tolist()

        regression_pass_rate = 0.0
        if regression_path:
            regression_pass_rate = self._run_regression(pipe, regression_path)

        elapsed = time.time() - start

        return EvalResult(
            accuracy=acc,
            f1_macro=f1_macro,
            f1_per_class=f1_per_class,
            confusion_matrix=cm,
            regression_pass_rate=regression_pass_rate,
            benchmark_size=len(test_rows),
            eval_time_seconds=elapsed,
        )

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _get_pipeline(self, model_path: str):
        """Lazy-load transformers pipeline for text-generation."""
        if self._pipe and self._loaded_model_path == model_path:
            return self._pipe

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except ImportError as exc:
            raise ImportError(
                "transformers not installed. Install per requirements.txt"
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map=self.device_map,
        )
        self._pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            return_full_text=False,
        )
        self._loaded_model_path = model_path
        return self._pipe

    def _build_prompt(self, input_text: str) -> str:
        return f"{self.system_prompt}\n\n{input_text}\nEmotion:"

    def _predict_batch(self, pipe, prompts: Iterable[str]) -> List[str]:
        preds: List[str] = []
        for prompt in prompts:
            outputs = pipe(
                prompt,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=0.0,
            )
            generation = outputs[0]["generated_text"]
            preds.append(self._parse_label(generation))
        return preds

    def _parse_label(self, generation: str) -> str:
        text = generation.strip().lower()

        # Exact match
        if text in self._valid_labels:
            return text

        # Substring scan (longest first to avoid collisions)
        for label in sorted(self._valid_labels, key=len, reverse=True):
            if label in text:
                return label

        return EmotionLabel.UNKNOWN.value

    def _load_eval_jsonl(self, path: str) -> list[dict]:
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rows.append(json.loads(line))
        return rows

    def _extract_expected_label(self, row: dict) -> str:
        raw = row.get("expected_label") or row.get("label")
        if not raw:
            raise KeyError("expected_label is required in eval JSONL")
        label = EmotionLabel.from_string(raw)
        if label == EmotionLabel.UNKNOWN:
            raise ValueError(f"Invalid expected_label: {raw}")
        return label.value

    def _run_regression(self, pipe, regression_path: str) -> float:
        if not os.path.exists(regression_path):
            logger.warning("Regression path %s not found; skipping", regression_path)
            return 0.0

        rows = self._load_eval_jsonl(regression_path)
        if not rows:
            logger.warning("Regression file %s is empty; pass_rate=0", regression_path)
            return 0.0

        prompts = [
            self._build_prompt(r.get("input_text") or r.get("input", ""))
            for r in rows
        ]
        expected = [self._extract_expected_label(r) for r in rows]
        predicted = self._predict_batch(pipe, prompts)

        correct = sum(1 for y_hat, y in zip(predicted, expected) if y_hat == y)
        return correct / len(rows)
