class FinetuneError(Exception):
    """Base exception cho finetune pipeline."""


class DataSourceError(FinetuneError):
    """Lỗi khi load data từ source."""


class InsufficientDataError(FinetuneError):
    """Không đủ data để train."""


class LabelConflictError(FinetuneError):
    """Conflict không resolve được trong labeling."""


class TrainingFailedError(FinetuneError):
    """Training bị fail."""


class EvalThresholdNotMetError(FinetuneError):
    """Model không đạt threshold để promote."""


class ModelPublishError(FinetuneError):
    """Lỗi khi publish model artifact."""
