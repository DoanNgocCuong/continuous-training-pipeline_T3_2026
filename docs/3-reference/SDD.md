# System Design Document (SDD)

## Emotion CT Pipeline - High-Level Design

---

## 1. Overview

**Project**: Emotion Continuous Training Pipeline for Pika Robot
**Purpose**: Fine-tune Qwen2.5-1.5B-Instruct model for emotion classification
**Target Users**: ML Engineers, Data Scientists at Pika Robotics

---

## 2. System Architecture

### 2.1 C4 Level 1 - System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                    Emotion CT Pipeline                          │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   Datadog   │    │  OpenAI API  │    │   Hugging    │   │
│  │  (CSV Data) │    │  (GPT-4o)   │    │     Face     │   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                    │                    │            │
│         ▼                    ▼                    ▼            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Emotion CT Pipeline                        │   │
│  │  Collect → Label → Build → Train → Evaluate → Decide  │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Pika Robot (Serving)                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 C4 Level 2 - Containers

```
┌──────────────────────────────────────────────────────────────────┐
│                     Emotion CT Pipeline                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    CLI (main.py)                           │  │
│  │              Typer commands: collect, label, train...    │  │
│  └─────────────────────────────┬──────────────────────────────┘  │
│                                │                                 │
│  ┌──────────────┬──────────────┼──────────────┬──────────────┐  │
│  │              │              │              │              │  │
│  ▼              ▼              ▼              ▼              ▼  │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│ │Collect  │ │ Label   │ │ Build   │ │ Train   │ │Evaluate │  │
│ │UseCase  │ │UseCase  │ │UseCase  │ │UseCase  │ │UseCase  │  │
│ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
│      │           │           │           │           │         │
│      ▼           ▼           ▼           ▼           ▼         │
│ ┌──────────────────────────────────────────────────────────┐   │
│  │              Infrastructure Layer                       │   │
│  │  CsvLoader | Distilabel | TRL Trainer | Sklearn      │   │
│  │  MLflowRegistry | HuggingFacePublisher | Argilla     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│ ──┐   ┌──────────────────────────────────────────────────────── │
│  │              Domain Layer (Pure Python)                  │   │
│  │  Entities: EmotionSample, TrainingRun, EvalResult       │   │
│  │  Services: LabelAgreement, PromotionDecider, DriftDetector│  │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Data Flow

```
CSV (Datadog)
    │
    ▼
CsvDataSourceLoader.load()
    │
    ▼
[Raw Samples] ──► DistilabelLabeler.label_batch() ──► [AI Labels]
    │                                                        │
    │                                                        ▼
    │                                              LabelAgreementService
    │                                                        │
    ▼                                                        ▼
[Approved Samples]                                    [Flagged Samples]
    │                                                        │
    ▼                                                        ▼
FileDatasetRepository.save_as_chatml()              ArgillaReviewer
    │                                                   │
    ▼                                                   ▼
[ChatML Format] ──────────────────────────────► [Human Reviewed]
                                                          │
                                                          ▼
                                                  FileDatasetRepository
                                                          │
                                                          ▼
TRLTrainer.train()
    │
    ▼
[LoRA Adapter]
    │
    ▼
SklearnEvaluator.evaluate()
    │
    ▼
[EvalResult] ──► PromotionDecider ──► [Promote/Reject]
    │
    ▼
MLflowRegistry.log_run()
    │
    ▼
HuggingFacePublisher.publish()
```

---

## 3. Technology Stack

### 3.1 Core Technologies

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Language** | Python 3.11+ | Primary language |
| **CLI** | Typer | Command-line interface |
| **LLM** | Qwen2.5-1.5B-Instruct | Base model |
| **Fine-tuning** | TRL/Unsloth | LoRA fine-tuning |
| **Quantization** | AWQ | Model compression |
| **Evaluation** | scikit-learn | Metrics calculation |

### 3.2 Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Labeling** | OpenAI GPT-4o-mini | AI labeling |
| **Human Review** | Argilla | Review interface |
| **Experiment Tracking** | MLflow | Metrics logging |
| **Model Registry** | MLflow + HuggingFace | Model versioning |
| **Observability** | Langfuse | Tracing & cost tracking |
| **CI/CD** | GitHub Actions | Automated pipeline |

### 3.3 Dependencies

```txt
# Core
typer>=0.9.0
pyyaml>=6.0

# ML/AI
torch>=2.0
transformers>=4.35
trl>=0.7
unsloth>=2024.4

# Evaluation
scikit-learn>=1.3
numpy>=1.24

# Infrastructure
huggingface_hub>=0.19
mlflow>=2.10

# Optional
langfuse>=2.0
argilla>=2.0
```

---

## 4. Domain Model

### 4.1 Entities

```python
EmotionSample:
  - id: str
  - input_text: str
  - ai_label: Optional[EmotionLabel]
  - human_label: Optional[EmotionLabel]
  - model_label: Optional[EmotionLabel]
  - confidence: ConfidenceScore
  - agreement_status: AgreementStatus

TrainingRun:
  - run_id: str
  - status: RunStatus
  - base_model: str
  - dataset_version: str
  - training_loss: float
  - adapter_path: Optional[str]
  - training_time_seconds: float

EvalResult:
  - accuracy: float
  - f1_macro: float
  - f1_per_class: dict[str, float]
  - confusion_matrix: list[list[int]]
  - benchmark_size: int
```

### 4.2 Value Objects

```python
EmotionLabel: Enum
  - happy, achievement, thinking, calm, sad, worried
  - angry, surprised, sending_heart, sun_glassed
  - dizzy, sobbing, superhero

ConfidenceScore: float (0.0 - 1.0)

AgreementStatus: Enum
  - auto_approved (AI==Human==Model)
  - auto_approved_gold (AI==Human!=Model)
  - human_resolved (AI==Model!=Human)
  - flagged (all different)
  - pending (no human label)
```

### 4.3 Domain Services

| Service | Responsibility |
|---------|---------------|
| `LabelAgreementService` | 3-way agreement logic (5 cases) |
| `DatasetBuilderService` | Stratified train/val/test split |
| `PromotionDeciderService` | Promotion thresholds check |
| `DataDriftDetector` | KL divergence, PSI detection |
| `PerformanceDriftDetector` | Accuracy/F1 trend analysis |

---

## 5. Pipeline Stages

### 5.1 Stage 1: Collect

**Input**: CSV from Datadog export
**Output**: `data/labeled/raw_samples.jsonl`

```
CsvDataSourceLoader.load(source: str) -> list[EmotionSample]
```

### 5.2 Stage 2: Label

**Input**: Raw samples
**Output**: `data/labeled/agreed/approved.jsonl`

```
DistilabelLabeler.label_batch(samples) -> list[EmotionSample]
LabelAgreementService.resolve(ai_label, human_label, model_label) -> AgreementStatus
```

### 5.3 Stage 3: Build

**Input**: Approved samples
**Output**: `data/datasets/{version}/{train,val,test}.jsonl`

```
DatasetBuilderService.build(samples, version, 0.7/0.15/0.15) -> DatasetVersion
```

### 5.4 Stage 4: Train

**Input**: Train/val datasets
**Output**: `data/artifacts/{run_id}/lora_adapter/`

```
TRLTrainer.train(dataset_path, config) -> TrainingRun
```

### 5.5 Stage 5: Evaluate

**Input**: Model + Test dataset
**Output**: `data/artifacts/latest/eval_result.json`

```
SklearnEvaluator.evaluate(model_path, test_path) -> EvalResult
```

### 5.6 Stage 6: Decide

**Input**: EvalResult
**Output**: promote/reject decision

```
PromotionDeciderService.decide(candidate, baseline) -> (bool, reason)
```

---

## 6. Integration Points

### 6.1 External APIs

| API | Purpose | Authentication |
|-----|---------|---------------|
| OpenAI | GPT-4o-mini labeling | `OPENAI_API_KEY` |
| HuggingFace Hub | Model/dataset push | `HF_TOKEN` |
| MLflow | Experiment tracking | `MLFLOW_TRACKING_URI` |
| Langfuse | Observability | `LANGFUSE_PUBLIC_KEY/SECRET_KEY` |
| Argilla | Human review | `ARGILLA_API_KEY` |

### 6.2 Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
HF_TOKEN=hf_...
MLFLOW_TRACKING_URI=http://localhost:5000
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
ARGILLA_API_KEY=admin.apikey
SLACK_WEBHOOK_URL=https://...
DISCORD_WEBHOOK_URL=https://...
```

---

## 7. Configuration

### 7.1 Training Config

```yaml
# configs/training/qwen2.5_1.5b_lora.yml
model:
  name: Qwen/Qwen2.5-1.5B-Instruct
  max_seq_length: 512

lora:
  r: 16
  lora_alpha: 32
  target_modules: [q_proj, k_proj, v_proj, o_proj]

training:
  learning_rate: 2e-4
  num_epochs: 3
  batch_size: 4
  gradient_accumulation: 4
```

### 7.2 Promotion Rules

```yaml
# configs/evaluation/promotion_rules.yml
thresholds:
  accuracy:
    min: 0.40
    relative_improvement: 0.005
  f1_macro:
    min: 0.35
    relative_improvement: 0.003
  per_class_f1:
    max_drop: 0.02
  regression_pass_rate:
    min: 1.0
```

---

## 8. Monitoring & Alerting

### 8.1 Metrics Tracked

| Category | Metrics |
|----------|---------|
| **Training** | loss, epoch, time |
| **Evaluation** | accuracy, f1_macro, f1_per_class |
| **Data** | label_distribution, sample_count |
| **System** | latency, error_rate |

### 8.2 Alert Conditions

| Alert | Condition |
|-------|-----------|
| Data Drift | KL divergence > 0.1 |
| Performance Drift | Accuracy drop > 5% |
| Canary Failure | Error rate > 1% |
| Pipeline Failure | Any stage error |

---

## 9. Security

- **API Keys**: Stored in `.env`, never committed
- **HF Token**: Fine-grained token with repo access only
- **MLflow**: Local server for internal use
- **Data**: No PII in sample text

---

## 10. Scalability

| Component | Current | Future |
|-----------|---------|--------|
| Dataset Size | 1K samples | 100K+ samples |
| Training | Single GPU | Multi-GPU (DeepSpeed) |
| Labeling | Sequential | Parallel batches |
| Evaluation | CPU | GPU inference |

---

*Last updated: 2026-03-08*
