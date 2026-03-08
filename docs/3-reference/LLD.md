# LLD: Emotion Finetune Pipeline — Low-Level Design

**Version**: 1.0
**Created**: 2026-03-02
**Status**: Draft

---

## 1. Folder Structure

```
EmotionFinetune/
│
├── finetune/                               ## Main application package
│   ├── __init__.py
│   ├── main.py                             ## CLI entry point (Typer)
│   │
│   ├── domain/                             ## Pure business logic (0 external deps)
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── value_objects.py
│   │   ├── exceptions.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── label_agreement.py
│   │       ├── dataset_builder.py
│   │       └── promotion_decider.py
│   │
│   ├── application/                        ## Use case orchestration
│   │   ├── __init__.py
│   │   ├── dto/
│   │   │   ├── __init__.py
│   │   │   ├── sample_dto.py
│   │   │   ├── training_dto.py
│   │   │   ├── eval_dto.py
│   │   │   └── decision_dto.py
│   │   ├── usecases/
│   │   │   ├── __init__.py
│   │   │   ├── collect_data.py             ## Step 1
│   │   │   ├── label_data.py              ## Step 2
│   │   │   ├── build_datasets.py          ## Step 2.5
│   │   │   ├── run_training.py            ## Step 3
│   │   │   ├── run_evaluation.py          ## Step 4
│   │   │   ├── decide_promotion.py        ## Step 5
│   │   │   └── publish_model.py           ## Step 5.5
│   │   └── repositories/                  ## Abstract interfaces (ABC)
│   │       ├── __init__.py
│   │       ├── data_source_repository.py
│   │       ├── dataset_repository.py
│   │       ├── trainer_repository.py
│   │       ├── evaluator_repository.py
│   │       └── model_registry_repository.py
│   │
│   └── infrastructure/                     ## Concrete implementations
│       ├── __init__.py
│       ├── data_sources/
│       │   ├── __init__.py
│       │   ├── csv_loader.py
│       │   ├── langfuse_extractor.py
│       │   ├── datadog_extractor.py
│       │   ├── distilabel_labeler.py
│       │   └── argilla_reviewer.py
│       ├── training/
│       │   ├── __init__.py
│       │   ├── unsloth_trainer.py
│       │   └── config_loader.py
│       ├── evaluation/
│       │   ├── __init__.py
│       │   ├── sklearn_evaluator.py
│       │   ├── testset_loader.py
│       │   └── report_generator.py
│       ├── registry/
│       │   ├── __init__.py
│       │   ├── mlflow_registry.py
│       │   └── huggingface_publisher.py
│       ├── packaging/
│       │   ├── __init__.py
│       │   └── awq_quantizer.py
│       └── repositories/
│           ├── __init__.py
│           ├── file_dataset_repository.py
│           └── file_data_source_repository.py
│
├── data/
│   ├── raw/                                ## Step 1 output
│   │   └── .gitkeep
│   ├── labeled/                            ## Step 2 output
│   │   ├── ai_labeled/
│   │   ├── human_labeled/
│   │   └── agreed/
│   ├── datasets/                           ## Step 2.5 output
│   │   ├── .gitkeep
│   │   ├── regression/
│   │   │   └── regression_test.jsonl
│   │   └── golden/
│   │       └── golden_test.jsonl
│   └── artifacts/                          ## Step 3 output
│       └── .gitkeep
│
├── configs/
│   ├── emotions.yml                        ## 13 emotion groups (shared with serving)
│   ├── training/
│   │   └── qwen2.5_1.5b_lora.yml
│   ├── evaluation/
│   │   └── promotion_rules.yml
│   └── labeling/
│       ├── distilabel_pipeline.yml
│       └── agreement_rules.yml
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── test_label_agreement.py
│   │   │   ├── test_dataset_builder.py
│   │   │   ├── test_promotion_decider.py
│   │   │   ├── test_entities.py
│   │   │   └── test_value_objects.py
│   │   └── application/
│   │       └── test_usecases.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_csv_loader.py
│   │   ├── test_distilabel_labeler.py
│   │   └── test_training_pipeline.py
│   └── eval_suites/                        ## Chạy mỗi lần eval model
│       ├── __init__.py
│       ├── test_benchmark.py
│       ├── test_regression.py
│       └── test_golden.py
│
├── scripts/
│   ├── run_full_pipeline.sh
│   ├── run_step.sh                         ## Chạy 1 step cụ thể
│   └── promote_model.sh
│
├── docs/
│   ├── PRD.md
│   ├── HLD.md
│   ├── LLD.md
│   ├── DATA_SCHEMA.md
│   └── ADR/
│       ├── ADR-001-separate-repo.md
│       ├── ADR-002-unsloth-over-trl.md
│       ├── ADR-003-sklearn-over-deepeval.md
│       └── ADR-004-mlflow-over-wandb.md
│
├── docker-compose.yml                      ## MLflow + Argilla (Phase 2)
├── Dockerfile                              ## GPU training image
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── Makefile
└── README.md
```

---

## 2. Domain Layer — Entities & Value Objects

### 2.1 entities.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4
from .value_objects import EmotionLabel, ConfidenceScore, AgreementStatus


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
    version: str                        # "v1.0", "v1.1"
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
    adapter_path: str = ""              # output LoRA path
    training_loss: float = 0.0
    training_time_seconds: float = 0.0
    status: str = "pending"             # pending | running | completed | failed
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvalResult:
    """Kết quả evaluation."""
    run_id: str = ""                    # liên kết với TrainingRun
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
    artifact_path: str = ""             # path to AWQ model
    published_to: str = ""              # HF Hub URL hoặc MLflow URI
```

### 2.2 value_objects.py

```python
from enum import Enum
from dataclasses import dataclass


class EmotionLabel(str, Enum):
    HAPPY = "happy"
    ACHIEVEMENT = "achievement"
    THINKING = "thinking"
    CALM = "calm"
    SAD = "sad"
    WORRIED = "worried"
    ANGRY = "angry"
    SURPRISED = "surprised"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "EmotionLabel":
        """Safely parse string to EmotionLabel."""
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.UNKNOWN


class AgreementStatus(str, Enum):
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    FLAGGED = "flagged"
    HUMAN_RESOLVED = "human_resolved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ConfidenceScore:
    value: float

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.value}")

    @property
    def is_high(self) -> bool:
        return self.value >= 0.8

    @property
    def is_low(self) -> bool:
        return self.value < 0.5
```

### 2.3 exceptions.py

```python
class FinetuneError(Exception):
    """Base exception cho finetune pipeline."""

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
```

---

## 3. Domain Services

### 3.1 label_agreement.py

```python
from ..entities import EmotionSample
from ..value_objects import AgreementStatus, EmotionLabel


class LabelAgreementService:
    """3-way agreement logic: AI vs Human vs Model output."""

    def resolve(self, sample: EmotionSample) -> EmotionSample:
        ai = sample.ai_label
        human = sample.human_label
        model = sample.model_output

        # Case 5: chỉ có AI + Model (chưa có human)
        if human is None:
            if ai == model:
                sample.agreed_label = ai
                sample.agreement_status = AgreementStatus.AUTO_APPROVED
            else:
                sample.agreement_status = AgreementStatus.PENDING
            return sample

        # Case 1: all 3 agree
        if ai == human == model:
            sample.agreed_label = human
            sample.agreement_status = AgreementStatus.AUTO_APPROVED
            return sample

        # Case 2: AI == Human != Model (model sai, valuable training data)
        if ai == human and ai != model:
            sample.agreed_label = human
            sample.agreement_status = AgreementStatus.AUTO_APPROVED
            return sample

        # Case 3: AI == Model != Human (trust human)
        if ai == model and ai != human:
            sample.agreed_label = human
            sample.agreement_status = AgreementStatus.HUMAN_RESOLVED
            return sample

        # Case 4: AI != Human (conflict)
        sample.agreement_status = AgreementStatus.FLAGGED
        return sample

    def batch_resolve(
        self, samples: list[EmotionSample]
    ) -> tuple[list[EmotionSample], list[EmotionSample]]:
        """Returns (approved, flagged)."""
        approved, flagged = [], []
        for s in samples:
            resolved = self.resolve(s)
            if resolved.agreement_status in (
                AgreementStatus.AUTO_APPROVED,
                AgreementStatus.HUMAN_RESOLVED,
            ):
                approved.append(resolved)
            else:
                flagged.append(resolved)
        return approved, flagged
```

### 3.2 dataset_builder.py

```python
from ..entities import EmotionSample, DatasetVersion
from ..exceptions import InsufficientDataError


class DatasetBuilderService:
    """Build train/val/test splits từ approved samples."""

    def build(
        self,
        samples: list[EmotionSample],
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        version: str = "v1.0",
    ) -> DatasetVersion:
        # Chỉ dùng samples đã approved
        approved = [
            s for s in samples if s.agreed_label is not None
        ]

        if len(approved) < 100:
            raise InsufficientDataError(
                f"Need ≥100 approved samples, got {len(approved)}"
            )

        # Stratified split by agreed_label
        # (implementation: group by label → split each group)
        ...

        return DatasetVersion(
            version=version,
            train_count=len(train),
            val_count=len(val),
            test_count=len(test),
            label_distribution=self._compute_distribution(approved),
        )
```

### 3.3 promotion_decider.py

```python
from dataclasses import dataclass
from ..entities import EvalResult


@dataclass
class PromotionPolicy:
    min_accuracy_improvement: float = 0.005   # +0.5%
    min_f1_improvement: float = 0.003         # +0.3%
    max_per_class_regression: float = 0.02    # -2%
    min_regression_pass_rate: float = 1.0     # 100%
    min_test_set_size: int = 500


class PromotionDeciderService:

    def __init__(self, policy: PromotionPolicy):
        self.policy = policy

    def decide(
        self,
        candidate: EvalResult,
        baseline: EvalResult,
    ) -> tuple[bool, str]:
        """Returns (should_promote, reason)."""
        p = self.policy

        # Check accuracy
        acc_diff = candidate.accuracy - baseline.accuracy
        if acc_diff < p.min_accuracy_improvement:
            return False, (
                f"Accuracy +{acc_diff:.4f} < threshold +{p.min_accuracy_improvement}"
            )

        # Check F1 macro
        f1_diff = candidate.f1_macro - baseline.f1_macro
        if f1_diff < p.min_f1_improvement:
            return False, (
                f"F1 macro +{f1_diff:.4f} < threshold +{p.min_f1_improvement}"
            )

        # Check per-class regression
        for cls, f1 in candidate.f1_per_class.items():
            baseline_f1 = baseline.f1_per_class.get(cls, 0)
            drop = baseline_f1 - f1
            if drop > p.max_per_class_regression:
                return False, (
                    f"Class '{cls}' F1 dropped {drop:.4f} > max {p.max_per_class_regression}"
                )

        # Check regression tests
        if candidate.regression_pass_rate < p.min_regression_pass_rate:
            return False, (
                f"Regression pass {candidate.regression_pass_rate:.0%} "
                f"< required {p.min_regression_pass_rate:.0%}"
            )

        # Check test set size
        if candidate.benchmark_size < p.min_test_set_size:
            return False, (
                f"Test set {candidate.benchmark_size} < min {p.min_test_set_size}"
            )

        return True, "All criteria passed"
```

---

## 4. Application Layer — Use Cases

### Pattern: mỗi usecase = 1 class, 1 method `execute()`

```python
# usecases/collect_data.py
class CollectDataUseCase:
    def __init__(self, data_source: IDataSourceRepository):
        self.data_source = data_source

    def execute(self, source_path: str) -> list[EmotionSample]:
        raw_records = self.data_source.load(source_path)
        samples = [EmotionSample(
            input_text=r["user_input"],
            source=r.get("source", "csv"),
        ) for r in raw_records]
        return samples
```

```python
# usecases/label_data.py
class LabelDataUseCase:
    def __init__(
        self,
        labeler: ILabelerRepository,
        agreement_service: LabelAgreementService,
    ):
        self.labeler = labeler
        self.agreement = agreement_service

    def execute(
        self, samples: list[EmotionSample]
    ) -> tuple[list[EmotionSample], list[EmotionSample]]:
        labeled = self.labeler.label_batch(samples)
        approved, flagged = self.agreement.batch_resolve(labeled)
        return approved, flagged
```

```python
# usecases/run_training.py
class RunTrainingUseCase:
    def __init__(
        self,
        trainer: ITrainerRepository,
        config_loader: IConfigLoader,
    ):
        self.trainer = trainer
        self.config_loader = config_loader

    def execute(
        self,
        dataset_path: str,
        config_name: str = "qwen2.5_1.5b_lora",
    ) -> TrainingRun:
        config = self.config_loader.load(config_name)
        run = self.trainer.train(dataset_path, config)
        return run
```

```python
# usecases/run_evaluation.py
class RunEvaluationUseCase:
    def __init__(self, evaluator: IEvaluatorRepository):
        self.evaluator = evaluator

    def execute(
        self,
        model_path: str,
        benchmark_path: str,
        regression_path: str | None = None,
    ) -> EvalResult:
        result = self.evaluator.evaluate(
            model_path, benchmark_path, regression_path
        )
        return result
```

```python
# usecases/decide_promotion.py
class DecidePromotionUseCase:
    def __init__(self, decider: PromotionDeciderService):
        self.decider = decider

    def execute(
        self,
        candidate_eval: EvalResult,
        baseline_eval: EvalResult,
    ) -> tuple[bool, str]:
        return self.decider.decide(candidate_eval, baseline_eval)
```

---

## 5. Application Layer — Repository Interfaces

```python
# repositories/data_source_repository.py
from abc import ABC, abstractmethod

class IDataSourceRepository(ABC):
    @abstractmethod
    def load(self, source: str) -> list[dict]:
        """Load raw records from source."""

# repositories/dataset_repository.py
class IDatasetRepository(ABC):
    @abstractmethod
    def save_samples(self, samples: list, path: str) -> None: ...

    @abstractmethod
    def load_samples(self, path: str) -> list: ...

# repositories/trainer_repository.py
class ITrainerRepository(ABC):
    @abstractmethod
    def train(self, dataset_path: str, config: dict) -> TrainingRun: ...

# repositories/evaluator_repository.py
class IEvaluatorRepository(ABC):
    @abstractmethod
    def evaluate(
        self, model_path: str, test_path: str, regression_path: str | None
    ) -> EvalResult: ...

# repositories/model_registry_repository.py
class IModelRegistryRepository(ABC):
    @abstractmethod
    def log_run(self, run: TrainingRun, eval_result: EvalResult) -> None: ...

    @abstractmethod
    def publish(self, model_path: str, version: str) -> str: ...
```

---

## 6. Infrastructure Layer — Key Implementations

### 6.1 csv_loader.py

```python
import pandas as pd
from ...application.repositories.data_source_repository import IDataSourceRepository


class CsvDataSourceLoader(IDataSourceRepository):
    """Load data từ CSV export (Datadog)."""

    MARKER = "Now Pika Robot's Response need check:"

    def load(self, source: str) -> list[dict]:
        df = pd.read_csv(source)
        records = []
        for _, row in df.iterrows():
            text = str(row.get("user_input", ""))
            cleaned = self._clean(text)
            if cleaned:
                records.append({
                    "user_input": cleaned,
                    "source": "datadog_csv",
                })
        return records

    def _clean(self, text: str) -> str:
        text = text.replace("\\n", "\n")
        if self.MARKER in text:
            return text.split(self.MARKER)[-1].strip()[:300]
        return text.strip()[:300]
```

### 6.2 distilabel_labeler.py

```python
class DistilabelLabeler(ILabelerRepository):
    """AI labeling via Distilabel + GPT-4o-mini."""

    def __init__(self, model: str = "gpt-4o-mini", config_path: str = None):
        self.model = model
        self.config = self._load_config(config_path)

    def label_batch(self, samples: list[EmotionSample]) -> list[EmotionSample]:
        # Build Distilabel pipeline
        # For each sample: call LLM → get emotion label
        # Parse response → set sample.ai_label
        ...
        return labeled_samples
```

### 6.3 unsloth_trainer.py

```python
class UnslothTrainer(ITrainerRepository):
    """Fine-tune using Unsloth LoRA."""

    def train(self, dataset_path: str, config: dict) -> TrainingRun:
        run = TrainingRun(
            base_model=config["base_model"],
            config_path=config.get("_source", ""),
            status="running",
        )
        # 1. Load base model with Unsloth
        # 2. Apply LoRA config
        # 3. Load dataset (train.jsonl)
        # 4. Train with SFTTrainer
        # 5. Save adapter
        # 6. Update run status
        ...
        return run
```

### 6.4 sklearn_evaluator.py

```python
from sklearn.metrics import (
    accuracy_score, f1_score, confusion_matrix, classification_report
)


class SklearnEvaluator(IEvaluatorRepository):
    """Evaluate model using sklearn metrics."""

    def evaluate(
        self, model_path: str, test_path: str, regression_path: str | None
    ) -> EvalResult:
        # 1. Load model (Unsloth / vLLM)
        # 2. Load test set
        # 3. Run inference on all test samples
        # 4. Compare predictions vs ground truth
        # 5. Compute metrics
        y_true, y_pred = self._run_inference(model_path, test_path)

        result = EvalResult(
            accuracy=accuracy_score(y_true, y_pred),
            f1_macro=f1_score(y_true, y_pred, average="macro"),
            f1_per_class=self._per_class_f1(y_true, y_pred),
            confusion_matrix=confusion_matrix(y_true, y_pred).tolist(),
            benchmark_size=len(y_true),
        )

        if regression_path:
            result.regression_pass_rate = self._run_regression(
                model_path, regression_path
            )

        return result
```

---

## 7. CLI Entry Point

### main.py (Typer)

```python
import typer
app = typer.Typer(name="finetune", help="Emotion CT Pipeline CLI")


@app.command()
def collect(source: str = "data/raw/extract.csv"):
    """Step 1: Load raw data."""
    ...

@app.command()
def label(input_dir: str = "data/raw", output_dir: str = "data/labeled"):
    """Step 2: AI label + agreement."""
    ...

@app.command()
def build(version: str = "v1.0"):
    """Step 2.5: Build train/val/test splits."""
    ...

@app.command()
def train(config: str = "qwen2.5_1.5b_lora"):
    """Step 3: Fine-tune with Unsloth."""
    ...

@app.command()
def evaluate(run_id: str = "latest"):
    """Step 4: Eval model vs baseline."""
    ...

@app.command()
def decide(run_id: str = "latest"):
    """Step 5: Promote or reject."""
    ...

@app.command()
def pipeline(source: str = "data/raw/extract.csv", config: str = "qwen2.5_1.5b_lora"):
    """Run full pipeline Step 1 → 5."""
    ...

if __name__ == "__main__":
    app()
```

Usage:

```bash
# Chạy từng step
python -m finetune collect --source data/raw/extract.csv
python -m finetune label
python -m finetune build --version v1.0
python -m finetune train --config qwen2.5_1.5b_lora
python -m finetune evaluate
python -m finetune decide

# Chạy full pipeline
python -m finetune pipeline --source data/raw/extract.csv
```

---

## 8. Config Files

### configs/emotions.yml

```yaml
emotion_groups:
  happy: [happy, happy_2, happy_3, excited, excited_2, playful, playful_2, playful_3]
  achievement: [celebration, encouraging, encouraging_2, thats_right, thats_right_2, proud, proud_2]
  thinking: [thinking, curious]
  calm: [calm, idle, idle_2, no_problem]
  sad: [sad]
  worried: [worry, afraid]
  angry: [angry, noisy]
  surprised: [surprised]
```

### configs/training/qwen2.5_1.5b_lora.yml

```yaml
base_model: "Qwen/Qwen2.5-1.5B-Instruct"
output_dir: "data/artifacts"

lora:
  r: 16
  alpha: 32
  target_modules: ["q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj", "gate_proj"]
  dropout: 0.05

training:
  num_epochs: 3
  per_device_batch_size: 8
  learning_rate: 2.0e-4
  warmup_ratio: 0.1
  max_seq_length: 512
  gradient_accumulation_steps: 4
  logging_steps: 10
  save_strategy: "epoch"

data:
  train_file: "data/datasets/{version}/train.jsonl"
  val_file: "data/datasets/{version}/val.jsonl"
  format: "chatml"

quantization:
  enabled: true
  method: "awq"
  bits: 4
```

### configs/evaluation/promotion_rules.yml

```yaml
baseline_model: "Qwen/Qwen2.5-1.5B-Instruct-AWQ"

thresholds:
  min_accuracy_improvement: 0.005
  min_f1_macro_improvement: 0.003
  max_per_class_f1_drop: 0.02
  min_regression_pass_rate: 1.0
  min_benchmark_size: 500
  max_p95_latency_ms: 100

test_sets:
  benchmark: "data/datasets/{version}/test.jsonl"
  regression: "data/datasets/regression/regression_test.jsonl"
  golden: "data/datasets/golden/golden_test.jsonl"

on_reject:
  log: true
  alert: false           # Phase 2: enable Slack notification
```

### configs/labeling/agreement_rules.yml

```yaml
strategy: "three_way"

rules:
  ai_human_model_agree: "auto_approve"
  ai_human_agree_model_disagree: "auto_approve"
  ai_model_agree_human_disagree: "trust_human"
  ai_human_disagree: "flag_for_review"
  no_human_ai_model_agree: "auto_approve_low_confidence"
  no_human_ai_model_disagree: "pending"

minimum_for_training:
  approved_samples: 100
  flagged_ratio_max: 0.3      # nếu >30% flagged → cảnh báo data quality
```

---

## 9. Data Format (JSONL)

### train.jsonl / val.jsonl / test.jsonl

```json
{"messages": [{"role": "system", "content": "Classify emotion..."}, {"role": "user", "content": "Previous Pika Robot's Response: ...\nNow Pika Robot's Response need check: Tớ rất vui!"}, {"role": "assistant", "content": "happy"}]}
{"messages": [{"role": "system", "content": "Classify emotion..."}, {"role": "user", "content": "Previous Pika Robot's Response: ...\nNow Pika Robot's Response need check: Cậu giỏi quá!"}, {"role": "assistant", "content": "achievement"}]}
```

Dùng ChatML format (compatible với Qwen2.5 + Unsloth SFTTrainer).

### regression_test.jsonl

```json
{"input": "...", "expected_label": "worried", "note": "Edge case: lo lắng nhưng giọng calm"}
{"input": "...", "expected_label": "achievement", "note": "Edge case: khen ngợi bằng tiếng Anh"}
```

---

## 10. Testing Strategy

### Unit Tests (domain layer — không cần external deps)

```
tests/unit/domain/
  test_label_agreement.py    → test 5 cases của 3-way agreement
  test_promotion_decider.py  → test các threshold conditions
  test_dataset_builder.py    → test split ratio, stratification
  test_entities.py           → test dataclass initialization
  test_value_objects.py      → test EmotionLabel.from_string(), ConfidenceScore validation
```

### Integration Tests

```
tests/integration/
  test_csv_loader.py         → test load từ file CSV thực
  test_distilabel_labeler.py → test call OpenAI API (mock hoặc real với small batch)
```

### Eval Suites (chạy mỗi lần eval model)

```
tests/eval_suites/
  test_benchmark.py          → load model → infer benchmark set → compute metrics
  test_regression.py         → load model → infer regression set → assert 100% pass
  test_golden.py             → load model → infer golden set → compute metrics
```

### Test Conventions

```python
# Fixtures trong conftest.py
@pytest.fixture
def sample_approved():
    return EmotionSample(
        input_text="Tớ rất vui!",
        ai_label=EmotionLabel.HAPPY,
        human_label=EmotionLabel.HAPPY,
        model_output=EmotionLabel.HAPPY,
    )

# Mock external calls
@pytest.mark.parametrize("ai,human,model,expected_status", [
    (HAPPY, HAPPY, HAPPY, AUTO_APPROVED),
    (HAPPY, HAPPY, SAD, AUTO_APPROVED),
    (HAPPY, SAD, HAPPY, HUMAN_RESOLVED),
    (HAPPY, SAD, CALM, FLAGGED),
])
def test_agreement_cases(ai, human, model, expected_status):
    ...
```

---

## 11. Error Handling Strategy

### Layered error handling

```
Infrastructure errors → wrapped as domain exceptions
Domain exceptions → caught in usecases → logged + re-raised or handled
CLI → catch domain exceptions → print user-friendly message + exit code
```

### Example

```python
# csv_loader.py (infrastructure)
try:
    df = pd.read_csv(source)
except FileNotFoundError:
    raise DataSourceError(f"CSV not found: {source}")

# collect_data.py (usecase)
try:
    samples = self.data_source.load(source_path)
except DataSourceError as e:
    logger.error(f"Failed to load data: {e}")
    raise  # re-raise for CLI to handle

# main.py (CLI)
try:
    samples = collect_use_case.execute(source)
    typer.echo(f"Loaded {len(samples)} samples")
except DataSourceError as e:
    typer.echo(f"Error: {e}", err=True)
    raise typer.Exit(1)
```

---

## 12. Logging Strategy

```python
import logging

# Root logger config (set in main.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/pipeline.log"),
    ]
)

# Per-module loggers
logger = logging.getLogger(__name__)
```

### Log levels

| Level | When |
|-------|------|
| DEBUG | Intermediate steps, loop iterations |
| INFO | Step start/end, count summaries |
| WARNING | Flagged samples, threshold warnings |
| ERROR | Failed operations (recoverable) |
| CRITICAL | Pipeline abort conditions |

---

## 13. Dependency Injection Pattern

```python
# main.py — wire everything together
def make_collect_usecase(source_type: str = "csv") -> CollectDataUseCase:
    if source_type == "csv":
        loader = CsvDataSourceLoader()
    elif source_type == "langfuse":
        loader = LangfuseExtractor(api_key=os.getenv("LANGFUSE_API_KEY"))
    else:
        raise ValueError(f"Unknown source: {source_type}")
    return CollectDataUseCase(data_source=loader)


def make_label_usecase() -> LabelDataUseCase:
    labeler = DistilabelLabeler(model="gpt-4o-mini")
    agreement = LabelAgreementService()
    return LabelDataUseCase(labeler=labeler, agreement_service=agreement)
```

Không dùng DI framework (Phase 1). Manual wiring trong `main.py`.
