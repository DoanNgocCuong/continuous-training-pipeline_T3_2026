"""Push dataset to HuggingFace Hub."""
import logging
import os
from typing import Optional

from finetune.domain.exceptions import ModelPublishError

logger = logging.getLogger(__name__)


class HuggingFaceDatasetPublisher:
    """Push dataset to HuggingFace Hub.

    Requires: pip install huggingface_hub
    Requires: HF_TOKEN env var or huggingface-cli login
    """

    def __init__(
        self,
        repo_prefix: str = "pika-robot",
        dataset_name: str = "emotion-classification",
        private: bool = False,
    ):
        self.repo_prefix = repo_prefix
        self.dataset_name = dataset_name
        self.private = private

    def publish(
        self,
        dataset_path: str,
        version: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Upload dataset to HF Hub.

        Args:
            dataset_path: Local path to dataset directory.
            version: Version tag (e.g., "v1.0").
            metadata: Optional metadata dict.

        Returns:
            HuggingFace Hub URL.
        """
        try:
            from huggingface_hub import HfApi
        except ImportError as exc:
            raise ImportError(
                "huggingface_hub not installed. Run: pip install huggingface_hub"
            ) from exc

        repo_id = f"{self.repo_prefix}/{self.dataset_name}"
        token = os.getenv("HF_TOKEN")

        api = HfApi(token=token)

        try:
            # Create or get dataset repo
            api.create_repo(
                repo_id=repo_id,
                private=self.private,
                exist_ok=True,
                repo_type="dataset",
            )

            # Upload dataset folder
            api.upload_folder(
                folder_path=dataset_path,
                repo_id=repo_id,
                commit_message=f"Upload dataset {version}",
            )

            # Add version tag
            api.create_tag(
                repo_id=repo_id,
                tag=version,
                tag_message=f"Release {version}",
            )

            # Upload metadata if provided
            if metadata:
                import json
                metadata_path = "/tmp/dataset_metadata.json"
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
                api.upload_file(
                    path_or_fileobj=metadata_path,
                    path_in_repo="metadata.json",
                    repo_id=repo_id,
                    commit_message="Add metadata",
                )
                os.remove(metadata_path)

        except Exception as exc:
            raise ModelPublishError(
                f"Failed to publish dataset to HF Hub {repo_id}: {exc}"
            ) from exc

        url = f"https://huggingface.co/datasets/{repo_id}"
        logger.info("Published dataset to %s (tag=%s)", url, version)
        return url
