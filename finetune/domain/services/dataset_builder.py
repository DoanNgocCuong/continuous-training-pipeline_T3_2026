import random
from collections import defaultdict

from ..entities import DatasetVersion, EmotionSample
from ..exceptions import InsufficientDataError


class DatasetBuilderService:
    """Build train/val/test splits từ approved samples."""

    def build(
        self,
        samples: list[EmotionSample],
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        version: str = "v1.0",
        seed: int = 42,
    ) -> tuple[DatasetVersion, list[EmotionSample], list[EmotionSample], list[EmotionSample]]:
        approved = [s for s in samples if s.agreed_label is not None]

        if len(approved) < 100:
            raise InsufficientDataError(
                f"Need >=100 approved samples, got {len(approved)}"
            )

        # Stratified split by agreed_label
        by_label = defaultdict(list)
        for s in approved:
            by_label[s.agreed_label].append(s)

        train, val, test = [], [], []
        rng = random.Random(seed)

        for label_samples in by_label.values():
            rng.shuffle(label_samples)
            n = len(label_samples)
            n_train = max(1, int(n * train_ratio))
            n_val = max(1, int(n * val_ratio))
            train.extend(label_samples[:n_train])
            val.extend(label_samples[n_train:n_train + n_val])
            test.extend(label_samples[n_train + n_val:])

        dataset_version = DatasetVersion(
            version=version,
            train_count=len(train),
            val_count=len(val),
            test_count=len(test),
            label_distribution=self._compute_distribution(approved),
        )
        return dataset_version, train, val, test

    def _compute_distribution(self, samples: list[EmotionSample]) -> dict:
        dist: dict = {}
        for s in samples:
            label = str(s.agreed_label)
            dist[label] = dist.get(label, 0) + 1
        return dist
