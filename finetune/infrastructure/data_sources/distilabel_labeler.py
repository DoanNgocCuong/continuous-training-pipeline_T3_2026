"""AI labeling via Distilabel + OpenAI GPT-4o-mini."""
import logging
import os

from finetune.application.repositories.labeler_repository import ILabelerRepository
from finetune.domain.entities import EmotionSample
from finetune.domain.value_objects import EmotionLabel

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an emotion classifier for a children's educational robot called Pika Robot.

Given the robot's PREVIOUS response and its CURRENT response, classify the emotion
expressed in the CURRENT response into EXACTLY ONE of these 8 labels:

  happy, achievement, thinking, calm, sad, worried, angry, surprised

Rules:
- Respond with ONLY the emotion label — no explanation, no punctuation.
- If the current response expresses joy, excitement, or playfulness → happy
- If it expresses pride, encouragement, or celebration → achievement
- If it is neutral or resting → calm
- When in doubt, choose the closest match.
"""


class DistilabelLabeler(ILabelerRepository):
    """AI labeling via Distilabel pipeline + OpenAI GPT-4o-mini.

    Requires: pip install 'distilabel[openai]'
    Requires: OPENAI_API_KEY env var
    """

    VALID_LABELS = frozenset(e.value for e in EmotionLabel if e != EmotionLabel.UNKNOWN)

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        batch_size: int = 50,
        temperature: float = 0.0,
        max_new_tokens: int = 20,
    ):
        self.model = model
        self.batch_size = batch_size
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def label_batch(self, samples: list[EmotionSample]) -> list[EmotionSample]:
        if not samples:
            return samples

        logger.info(
            "Labeling %d samples with %s (batch_size=%d)",
            len(samples), self.model, self.batch_size,
        )

        # distilabel TextGeneration reads "instruction" field
        data = [{"idx": i, "instruction": s.input_text} for i, s in enumerate(samples)]
        results = self._run_pipeline(data)

        unlabeled = 0
        for row in results:
            idx: int = row["idx"]
            generation: str = row.get("generation") or ""
            label = self._parse_label(generation)
            samples[idx].ai_label = label
            if label == EmotionLabel.UNKNOWN:
                unlabeled += 1
                logger.warning("Cannot parse label from generation: %r", generation[:80])

        if unlabeled:
            logger.warning("%d/%d samples have UNKNOWN label", unlabeled, len(samples))

        return samples

    # ─────────────────────────────────────────────────────────────────────────
    # Internal: distilabel pipeline
    # ─────────────────────────────────────────────────────────────────────────

    def _run_pipeline(self, data: list[dict]) -> list[dict]:
        try:
            from distilabel.llms import OpenAILLM
            from distilabel.pipeline import Pipeline
            from distilabel.steps import LoadDataFromDicts
            from distilabel.steps.tasks import TextGeneration
        except ImportError as exc:
            raise ImportError(
                "distilabel not installed. Run: pip install 'distilabel[openai]'"
            ) from exc

        with Pipeline(
            name="emotion-labeling",
            description="Classify Pika Robot responses into 8 emotion labels",
        ) as pipeline:
            load = LoadDataFromDicts(
                data=data,
                batch_size=self.batch_size,
                name="load_samples",
            )
            task = TextGeneration(
                name="classify_emotion",
                llm=OpenAILLM(
                    model=self.model,
                    api_key=os.getenv("OPENAI_API_KEY"),
                    generation_kwargs={
                        "temperature": self.temperature,
                        "max_tokens": self.max_new_tokens,
                    },
                ),
                system_prompt=_SYSTEM_PROMPT,
            )
            load >> task

        logger.info("Running distilabel pipeline on %d samples...", len(data))
        distiset = pipeline.run(use_cache=False)

        rows = [dict(row) for row in distiset["default"]["train"]]
        logger.info("Distilabel pipeline done. Got %d results.", len(rows))
        return rows

    # ─────────────────────────────────────────────────────────────────────────
    # Internal: label parsing
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_label(self, generation: str) -> EmotionLabel:
        """Parse emotion label from LLM generation.

        1. Exact match after strip + lowercase
        2. Substring scan (longest label first to avoid partial collision)
        3. Fallback: UNKNOWN
        """
        text = generation.strip().lower()

        if text in self.VALID_LABELS:
            return EmotionLabel(text)

        for label in sorted(self.VALID_LABELS, key=len, reverse=True):
            if label in text:
                return EmotionLabel(label)

        return EmotionLabel.UNKNOWN
