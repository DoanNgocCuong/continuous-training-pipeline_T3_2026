"""Argilla v2 integration — push samples for human review, pull annotations back."""
import logging
import os
from typing import Optional

from finetune.domain.entities import EmotionSample
from finetune.domain.value_objects import AgreementStatus, EmotionLabel

logger = logging.getLogger(__name__)

# 5 emotion labels — used as allowed values in in Argilla question
_EMOTION_LABELS = [
    "happy", "achievement", "thinking", "calm", "surprised",
]


class ArgillaReviewer:
    """Push unlabeled/flagged samples to Argilla UI for human annotation,
    then pull completed annotations back into the pipeline.

    Requires: pip install argilla>=2.0.0
    Requires: ARGILLA_API_URL and ARGILLA_API_KEY env vars
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace: Optional[str] = None,
    ):
        self.api_url = api_url or os.getenv("ARGILLA_API_URL", "http://localhost:6900")
        self.api_key = api_key or os.getenv("ARGILLA_API_KEY", "argilla.apikey")
        self.workspace = workspace
        self._client = None  # lazy init

    # ─────────────────────────────────────────────────────────────────────────
    # Push samples to Argilla for human review
    # ─────────────────────────────────────────────────────────────────────────

    def push_for_review(
        self,
        samples: list[EmotionSample],
        dataset_name: str = "emotion-review",
    ) -> int:
        """Push samples to Argilla dataset for human annotation.

        Returns number of records pushed.
        """
        import argilla as rg

        client = self._get_client()

        # Get or create dataset with LabelQuestion for emotion classification
        dataset = self._get_or_create_dataset(client, dataset_name)

        records = []
        for s in samples:
            # Build metadata for reviewers
            metadata: dict = {"source": s.source, "sample_id": s.id}

            # Pre-fill suggestions - prioritize human_label, then ai_label
            suggestions = []

            # 1. Human label (pre-labeled data) - highest priority
            if s.human_label and s.human_label != EmotionLabel.UNKNOWN:
                metadata["human_label"] = s.human_label.value
                suggestions.append(
                    rg.Suggestion(
                        question_name="emotion_label",
                        value=s.human_label.value,
                        agent="human",
                        score=1.0,
                    )
                )
            # 2. AI label - as fallback/pre-fill
            elif s.ai_label and s.ai_label != EmotionLabel.UNKNOWN:
                metadata["ai_label"] = s.ai_label.value
                suggestions.append(
                    rg.Suggestion(
                        question_name="emotion_label",
                        value=s.ai_label.value,
                        agent=f"gpt-4o-mini",
                        score=0.9,
                    )
                )

            if s.model_output:
                metadata["model_output"] = s.model_output.value

            record = rg.Record(
                fields={"text": s.input_text},
                metadata=metadata,
                suggestions=suggestions,
                id=s.id,
            )
            records.append(record)

        dataset.records.log(records)
        logger.info("Pushed %d records to Argilla dataset '%s'", len(records), dataset_name)
        return len(records)

    # ─────────────────────────────────────────────────────────────────────────
    # Pull reviewed annotations back
    # ─────────────────────────────────────────────────────────────────────────

    def pull_reviewed(
        self,
        dataset_name: str = "emotion-review",
        status_filter: str = "submitted",
    ) -> list[EmotionSample]:
        """Pull completed human annotations from Argilla.

        Args:
            dataset_name: Argilla dataset name.
            status_filter: "submitted" = annotated by human, "pending" = not yet done.

        Returns list of EmotionSamples with human_label set.
        """
        import argilla as rg

        client = self._get_client()

        try:
            dataset = client.datasets(name=dataset_name, workspace=self.workspace)
        except Exception as exc:
            logger.error("Dataset '%s' not found in Argilla: %s", dataset_name, exc)
            return []

        samples = []
        for record in dataset.records(with_responses=True):
            # Skip records without a submitted human response
            responses = [r for r in (record.responses or []) if r.status == status_filter]
            if not responses:
                continue

            # Take first submitted response
            response = responses[0]
            human_label_raw = response.fields.get("emotion_label", "")
            human_label = EmotionLabel.from_string(human_label_raw)

            # Reconstruct minimal EmotionSample with the human annotation
            s = EmotionSample(
                id=str(record.id),
                input_text=record.fields.get("text", ""),
                human_label=human_label,
                ai_label=EmotionLabel.from_string(record.metadata.get("ai_label", "")) if record.metadata else None,
                model_output=EmotionLabel.from_string(record.metadata.get("model_output", "")) if record.metadata else None,
                source=record.metadata.get("source", "argilla") if record.metadata else "argilla",
                agreement_status=AgreementStatus.PENDING,
            )
            samples.append(s)

        logger.info(
            "Pulled %d annotated records from Argilla dataset '%s'",
            len(samples), dataset_name,
        )
        return samples

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _get_client(self):
        if self._client is None:
            try:
                import argilla as rg
            except ImportError as exc:
                raise ImportError(
                    "argilla not installed. Run: pip install 'argilla>=2.0.0'"
                ) from exc
            self._client = rg.Argilla(api_url=self.api_url, api_key=self.api_key)
        return self._client

    def _get_or_create_dataset(self, client, dataset_name: str):
        import argilla as rg

        # Get workspace
        workspace = client.workspaces.default

        # Try to get dataset - if not found, create new
        try:
            ds = client.datasets(name=dataset_name, workspace=workspace.name)
            if ds:
                logger.info("Found existing dataset '%s'", dataset_name)
                return ds
        except Exception:
            pass

        # Dataset does not exist — create with emotion LabelQuestion
        logger.info("Creating new dataset '%s'", dataset_name)
        settings = rg.Settings(
            fields=[
                rg.TextField(name="text", title="Robot Response", required=True),
            ],
            questions=[
                rg.LabelQuestion(
                    name="emotion_label",
                    title="What emotion does the current response express?",
                    labels=_EMOTION_LABELS,
                    required=True,
                ),
            ],
            metadata=[
                rg.TermsMetadataProperty(name="source"),
                rg.TermsMetadataProperty(name="ai_label"),
                rg.TermsMetadataProperty(name="human_label"),
                rg.TermsMetadataProperty(name="model_output"),
                rg.TermsMetadataProperty(name="sample_id"),
            ],
            guidelines=(
                "Classify the emotion expressed in the robot's CURRENT response. "
                "The AI suggestion is pre-filled — override if you disagree."
            ),
        )
        # Create dataset with workspace
        dataset = rg.Dataset(
            name=dataset_name,
            workspace=workspace.name,
            settings=settings,
            client=client,
        )
        dataset.create()
        logger.info("Created Argilla dataset '%s'", dataset_name)
        return dataset
