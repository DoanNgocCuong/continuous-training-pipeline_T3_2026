# Project Plan — Emotion Continuous Training Pipeline

## Project Overview
- **Product**: Pika Robot (robot giáo dục cho trẻ em)
- **Model**: Qwen2.5-1.5B-Instruct → fine-tune LoRA → quantize AWQ
- **13 emotions**: happy, achievement, thinking, calm, sad, worried, angry, surprised, sending_heart, sun_glassed, dizzy, sobbing, superhero

---

## Pipeline Stages Overview

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Collect │ → │  Label  │ → │ Build   │ → │ Train   │ → │Evaluate │ → │ Decide │
│  CSV    │   │ OpenAI  │  │Dataset  │   │ TRL     │   │ Sklearn │   │Promote │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
      ✅           ✅           ✅           ✅           ☐            ☐
  data/raw    data/labeled  data/datasets  data/artifacts  eval_result  publish
```

---

## Phase 1: Core Pipeline (Manual End-to-End)

### ✅ 1.1 Domain Layer
- [x] Entities: `EmotionSample`, `TrainingRun`, `EvalResult`
- [x] Value Objects: `EmotionLabel`, `ConfidenceScore`, `AgreementStatus`
- [x] Exceptions: Custom exceptions
- [x] Services: `LabelAgreementService`, `DatasetBuilderService`, `PromotionDeciderService`

**Files**: `finetune/domain/`

### ✅ 1.2 Application Layer (Use Cases)
- [x] `CollectDataUseCase` — Load raw data
- [x] `LabelDataUseCase` — AI labeling + 3-way agreement
- [x] `BuildDatasetsUseCase` — Train/val/test split (70/15/15 stratified)
- [x] `RunTrainingUseCase` — Fine-tune execution
- [x] `RunEvaluationUseCase` — Metrics calculation
- [x] `DecidePromotionUseCase` — Promotion decision

**Files**: `finetune/application/usecases/`

### ✅ 1.3 Infrastructure — Data Sources
- [x] `CsvDataSourceLoader` — Load from CSV (Datadog export)
- [x] `OpenAILabeler` — Direct OpenAI labeling (bypasses distilabel async issues)
- [x] `DistilabelLabeler` — (stub) AI labeling via GPT-4o-mini
- [x] `ArgillaReviewer` — (stub) Human review interface

**Files**: `finetune/infrastructure/data_sources/`

### ✅ 1.4 Infrastructure — Training
- [x] `ConfigLoader` — Load training configs
- [x] `UnslothTrainer` — LoRA fine-tuning code (Unsloth has torch version conflict)
- [x] `TRLTrainer` — Alternative using transformers+trl directly ✅ WORKING

**Files**: `finetune/infrastructure/training/`

### ✅ 1.5 Infrastructure — Evaluation
- [x] `SklearnEvaluator` — Metrics: accuracy, F1 macro, per-class F1, confusion matrix
- [x] `ReportGenerator` — Generate eval_report.md

**Files**: `finetune/infrastructure/evaluation/`

### ✅ 1.6 Infrastructure — Packaging & Registry
- [x] `AWQQuantizer` — Merge LoRA + AWQ 4-bit quantization
- [x] `HuggingFacePublisher` — (stub) Push to HF Hub
- [x] `MLflowRegistry` — (stub) Register in MLflow

**Files**: `finetune/infrastructure/packaging/`, `finetune/infrastructure/registry/`

### ✅ 1.7 CLI & Scripts
- [x] `finetune/main.py` — Typer CLI with all commands
- [x] `scripts/run_full_pipeline.sh` — Run end-to-end
- [x] `scripts/run_step.sh` — Run individual step
- [x] `scripts/promote_model.sh` — Promote after eval
- [x] `scripts/train_simple.py` — Simple training script ✅ WORKING

### ✅ 1.8 Configuration
- [x] `configs/emotions.yml` — 13 emotion groups
- [x] `configs/training/qwen2.5_1.5b_lora.yml` — LoRA config
- [x] `configs/evaluation/promotion_rules.yml` — Promotion thresholds
- [x] `configs/labeling/agreement_rules.yml` — 3-way agreement rules
- [x] `configs/labeling/distilabel_pipeline.yml` — Distilabel config

### ✅ 1.9 Testing
- [x] Unit tests: 16/16 passing
- [x] Domain logic: `LabelAgreementService`, `PromotionDeciderService`
- [x] Value objects: `EmotionLabel`, `ConfidenceScore`

### ✅ 1.10 Documentation
- [x] `docs/PRD.md` — Problem statement, user stories
- [x] `docs/HLD.md` — System architecture, data flow
- [x] `docs/LLD.md` — Folder structure, interfaces
- [x] `docs/Plan.md` — Project plan with progress tracking
- [x] `CLAUDE.md` — AI agent instructions

---

## Phase 2: Enhanced Pipeline

### ☐ 2.1 Argilla UI (Human-in-the-Loop)
- [ ] Install Argilla
- [ ] Create labeling workspace
- [ ] Integrate with pipeline for human review
- [ ] UI for resolving flagged samples

### ☐ 2.2 HuggingFace Hub Integration
- [x] Configure HF token (in .env)
- [ ] Push dataset to Hub
- [ ] Push model after promotion
- [ ] Add model card generation

### ☐ 2.3 MLflow Integration
- [ ] Install MLflow
- [ ] Log training metrics
- [ ] Log evaluation results
- [ ] Model versioning

### ☐ 2.4 Langfuse Observability
- [ ] Install Langfuse
- [ ] Track pipeline runs
- [ ] Cost tracking (OpenAI API)
- [ ] Latency metrics

---

## Phase 3: Production Pipeline

### ☐ 3.1 Scheduled Pipeline
- [ ] GitHub Actions / Airflow DAG
- [ ] Cron schedule for daily/weekly training
- [ ] Slack/Discord notifications

### ☐ 3.2 Drift Monitoring
- [ ] Data drift detection
- [ ] Model performance monitoring
- [ ] Alerting thresholds

### ☐ 3.3 Canary Deployment
- [ ] A/B testing setup
- [ ] Gradual rollout
- [ ] Rollback mechanism

---

## Pipeline Progress — March 6, 2026

### ✅ Completed Steps

| Step | Status | Details |
|------|--------|---------|
| 1. Collect | ✅ | 1000 samples from xlsx → CSV |
| 2. Label | ✅ | GPT-4o-mini labeling (~$0.009) |
| 3. Build | ✅ | train=697, val=149, test=154 |
| 4. Train | ✅ | Qwen2.5-1.5B + LoRA (3 epochs, 3.5 min) |
| 5. Evaluate | ☐ | Pending - need run evaluation |
| 6. Decide | ☐ | Pending evaluation |

### Label Distribution (1000 samples)
```
happy          354 (35.4%)
thinking       310 (31.0%)
calm           243 (24.3%)
worried         46 (4.6%)
surprised       19 (1.9%)
sad             14 (1.4%)
achievement     10 (1.0%)
angry           2 (0.2%)
unknown         2 (0.2%)
```

### Training Results
```
Epochs: 3
Train samples: 697
Final loss: 0.09227
Training time: ~3.5 minutes
GPU: RTX 3090 24GB
Model saved: data/artifacts/training/lora_adapter/
```

### Cost Tracking
- Labeling 1000 samples: ~$0.009 (GPT-4o-mini)
- Total cost so far: ~$0.009 / $5 budget

---

## Prerequisites to Run Pipeline

### ✅ Available Now

| Item | Status | Notes |
|------|--------|-------|
| Raw CSV data | ✅ | 1000 samples from xlsx |
| OPENAI_API_KEY | ✅ | Available in .env |
| GPU with CUDA | ✅ | 2x RTX 3090 24GB |
| Labeling | ✅ | 1000 samples labeled |
| Dataset built | ✅ | train=697, val=149, test=154 |
| Training | ✅ | Model trained successfully |

### ☐ Needed Later

| Item | Status | Notes |
|------|--------|-------|
| Argilla setup | ☐ | For human labeling UI |
| HuggingFace push | ☐ | For model sharing |
| MLflow server | ☐ | For experiment tracking |
| Langfuse project | ☐ | For observability |

---

## How to Run

### Quick Start

```bash
# Activate venv
source .venv/bin/activate

# Set environment
export OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d= -f2-)

# Run training (already done)
python scripts/train_simple.py

# Run evaluation
python -m finetune.main evaluate --version v1.0

# Run promotion decision
python -m finetune.main decide

# Check results
cat data/artifacts/latest/eval_result.json
```

---

## Current Status

✅ **Phase 1 Core Pipeline - COMPLETE**

- Collect: ✅
- Label: ✅
- Build: ✅
- Train: ✅
- Evaluate: ☐ (Run with: `python -m finetune.main evaluate --version v1.0`)
- Decide: ☐

---

*Last updated: 2026-03-06 02:10*
