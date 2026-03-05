from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from .value_objects import AgreementStatus, ConfidenceScore, EmotionLabel


@dataclass
class EmotionSample:
    """1 sample data từ production logs."""
    id: str = field(default_factory=lambda: str(uuid4()))
    input_text: str = ""
    model_output: Optional[EmotionLabel] = None
    model_confidence: Optional[ConfidenceScore] = None
    ai_label: Optional[EmotionLabel] = None
    human_label: Optional[EmotionLabel] = None
    user_feedback: Optional[EmotionLabel] = None
    agreed_label: Optional[EmotionLabel] = None
    agreement_status: AgreementStatus = AgreementStatus.PENDING
    source: str = "unknown"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DatasetVersion:
    """1 phiên bản dataset (snapshot tại thời điểm build)."""
    version: str
    train_count: int = 0
    val_count: int = 0
    test_count: int = 0
    label_distribution: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    source_description: str = ""


@dataclass
class TrainingRun:
    """1 lần chạy training."""
    run_id: str = field(default_factory=lambda: str(uuid4()))
    base_model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    dataset_version: str = ""
    config_path: str = ""
    adapter_path: str = ""
    training_loss: float = 0.0
    training_time_seconds: float = 0.0
    status: str = "pending"  # pending | running | completed | failed
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvalResult:
    """Kết quả evaluation."""
    run_id: str = ""
    accuracy: float = 0.0
    f1_macro: float = 0.0
    f1_per_class: dict = field(default_factory=dict)
    confusion_matrix: list = field(default_factory=list)
    regression_pass_rate: float = 0.0
    benchmark_size: int = 0
    eval_time_seconds: float = 0.0


@dataclass
class ModelCandidate:
    """Model sau khi train + eval, chờ quyết định promote."""
    run_id: str = ""
    eval_result: Optional[EvalResult] = None
    promoted: bool = False
    rejection_reason: str = ""
    artifact_path: str = ""
    published_to: str = ""
