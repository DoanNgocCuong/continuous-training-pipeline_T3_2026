"""Push model artifacts to HuggingFace Hub."""
import logging
import os
from typing import Optional

from finetune.domain.exceptions import ModelPublishError

logger = logging.getLogger(__name__)


class HuggingFacePublisher:
    """Push a quantized (AWQ) model to HuggingFace Hub.

    Requires: pip install huggingface_hub
    Requires: HF_TOKEN env var or huggingface-cli login
    """

    def __init__(
        self,
        repo_prefix: str = "pika-ai",
        model_base_name: str = "Qwen2.5-1.5B-Emotion",
        private: bool = True,
    ):
        self.repo_prefix = repo_prefix
        self.model_base_name = model_base_name
        self.private = private

    def publish(
        self,
        model_path: str,
        version: str,
        eval_report_path: Optional[str] = None,
    ) -> str:
        """Upload model directory to HF Hub.

        Args:
            model_path: Local path to the quantized model directory.
            version: Version tag (e.g. "v1.1.0").
            eval_report_path: Optional path to eval report markdown.

        Returns:
            HuggingFace Hub URL.
        """
        try:
            from huggingface_hub import HfApi
        except ImportError as exc:
            raise ImportError(
                "huggingface_hub not installed. Run: pip install huggingface_hub"
            ) from exc

        repo_id = f"{self.repo_prefix}/{self.model_base_name}-{version}-AWQ"
        token = os.getenv("HF_TOKEN")

        api = HfApi(token=token)

        try:
            api.create_repo(
                repo_id=repo_id,
                private=self.private,
                exist_ok=True,
                repo_type="model",
            )

            api.upload_folder(
                folder_path=model_path,
                repo_id=repo_id,
                commit_message=f"Upload model {version}",
            )

            if eval_report_path and os.path.exists(eval_report_path):
                api.upload_file(
                    path_or_fileobj=eval_report_path,
                    path_in_repo="eval_report.md",
                    repo_id=repo_id,
                    commit_message=f"Add eval report for {version}",
                )

            api.create_tag(
                repo_id=repo_id,
                tag=version,
                tag_message=f"Release {version}",
            )

        except Exception as exc:
            raise ModelPublishError(
                f"Failed to publish to HF Hub {repo_id}: {exc}"
            ) from exc

        url = f"https://huggingface.co/{repo_id}"
        logger.info("Published model to %s (tag=%s)", url, version)
        return url
