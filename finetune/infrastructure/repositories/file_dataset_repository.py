"""File-based dataset repository — raw samples and ChatML JSONL for training."""
import json
import os

from finetune.application.repositories.dataset_repository import IDatasetRepository
from finetune.domain.entities import EmotionSample
from finetune.domain.value_objects import AgreementStatus, EmotionLabel

_CHATML_SYSTEM = (
    "You are an emotion classifier for Pika Robot, a children's educational robot. "
    "Given the robot's previous response and current response, classify the emotion "
    "of the CURRENT response into exactly one of these 5 labels: "
    "happy, achievement, thinking, calm, surprised. "
    "Respond with ONLY the emotion label."
)


class FileDatasetRepository(IDatasetRepository):
    """Persist EmotionSamples as JSONL files.

    Two formats:
      save_samples()   → internal JSONL (all fields, for pipeline state)
      save_as_chatml() → ChatML JSONL (for Unsloth SFTTrainer)
    """

    # ─────────────────────────────────────────────────────────────────────────
    # Internal format
    # ─────────────────────────────────────────────────────────────────────────

    def save_samples(self, samples: list[EmotionSample], path: str) -> None:
        """Save all fields as JSONL (internal pipeline format)."""
        _ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            for s in samples:
                record = {
                    "id": s.id,
                    "input_text": s.input_text,
                    "agreed_label": s.agreed_label.value if s.agreed_label else None,
                    "ai_label": s.ai_label.value if s.ai_label else None,
                    "human_label": s.human_label.value if s.human_label else None,
                    "model_output": s.model_output.value if s.model_output else None,
                    "agreement_status": s.agreement_status.value,
                    "source": s.source,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_samples(self, path: str) -> list[EmotionSample]:
        """Load internal JSONL format."""
        samples = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line.strip())
                samples.append(EmotionSample(
                    id=r["id"],
                    input_text=r["input_text"],
                    agreed_label=EmotionLabel.from_string(r["agreed_label"]) if r.get("agreed_label") else None,
                    ai_label=EmotionLabel.from_string(r["ai_label"]) if r.get("ai_label") else None,
                    human_label=EmotionLabel.from_string(r["human_label"]) if r.get("human_label") else None,
                    model_output=EmotionLabel.from_string(r["model_output"]) if r.get("model_output") else None,
                    agreement_status=AgreementStatus(r.get("agreement_status", "pending")),
                    source=r.get("source", "unknown"),
                ))
        return samples

    # ─────────────────────────────────────────────────────────────────────────
    # ChatML format (for Unsloth SFTTrainer)
    # ─────────────────────────────────────────────────────────────────────────

    def save_as_chatml(
        self,
        samples: list[EmotionSample],
        path: str,
        system_prompt: str = _CHATML_SYSTEM,
    ) -> None:
        """Save samples as ChatML JSONL for training.

        Format per line:
        {
          "messages": [
            {"role": "system",    "content": "..."},
            {"role": "user",      "content": "<input_text>"},
            {"role": "assistant", "content": "<agreed_label>"}
          ]
        }
        """
        valid = [s for s in samples if s.agreed_label is not None]
        skipped = len(samples) - len(valid)
        if skipped:
            import logging
            logging.getLogger(__name__).warning(
                "Skipping %d samples with no agreed_label in ChatML export", skipped
            )

        _ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            for s in valid:
                record = {
                    "messages": [
                        {"role": "system",    "content": system_prompt},
                        {"role": "user",      "content": s.input_text},
                        {"role": "assistant", "content": s.agreed_label.value},
                    ]
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ─────────────────────────────────────────────────────────────────────────
    # Eval format (used by SklearnEvaluator)
    # ─────────────────────────────────────────────────────────────────────────

    def save_as_eval_jsonl(self, samples: list[EmotionSample], path: str) -> None:
        """Save as flat eval format: {input_text, expected_label}.

        Used for regression/golden test sets.
        """
        valid = [s for s in samples if s.agreed_label is not None]
        _ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            for s in valid:
                record = {
                    "id": s.id,
                    "input_text": s.input_text,
                    "expected_label": s.agreed_label.value,
                    "source": s.source,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def load_eval_jsonl(path: str) -> list[dict]:
        """Load flat eval format. Returns list of dicts with input_text + expected_label."""
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line.strip()))
        return rows


def _ensure_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
