# CLAUDE.md — AI Agent Instructions for Emotion CT Pipeline

## Project Overview

- **Project**: Emotion Continuous Training Pipeline for Pika Robot
- **Goal**: Fine-tune Qwen2.5-1.5B-Instruct model for emotion classification
- **13 Emotions**: happy, achievement, thinking, calm, sad, worried, angry, surprised, sending_heart, sun_glassed, dizzy, sobbing, superhero

---

## Quick Start

```bash
# 1. Load API key
export OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d= -f2-)
export HF_TOKEN=$(grep HF_TOKEN .env | cut -d= -f2-)

# 2. Run pipeline steps
python -m finetune.main collect --source data/raw/extract_1k.csv
python -m finetune.main build --version v1.0
python -m finetune.main train --version v1.0
python -m finetune.main evaluate --version v1.0
python -m finetune.main decide

# 3. Check results
cat data/artifacts/latest/eval_result.json
```

---

## Project Structure

```
Continuous_Traning_Pipeline/
├── finetune/                    # Main application code
│   ├── domain/                  # Entities, Value Objects, Services
│   ├── application/             # Use Cases
│   ├── infrastructure/          # Concrete implementations
│   │   ├── data_sources/       # CSV loader, Labelers
│   │   ├── training/           # Trainers
│   │   ├── evaluation/         # Evaluators
│   │   └── registry/           # HuggingFace, MLflow
│   └── main.py                 # CLI entry point
├── configs/                     # YAML configs
│   ├── emotions.yml             # Emotion definitions
│   ├── training/                # Training configs
│   └── evaluation/              # Promotion rules
├── data/                        # Data directories
│   ├── raw/                    # Raw CSV data
│   ├── labeled/                # Labeled samples
│   └── datasets/               # Train/val/test splits
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
└── tests/                       # Unit tests
```

---

## Pipeline Steps

### Step 1: Collect
Load raw data from CSV export (Datadog format).

```bash
python -m finetune.main collect --source data/raw/extract.csv
```
Output: `data/labeled/raw_samples.jsonl`

### Step 2: Label
AI labeling via OpenAI GPT-4o-mini + 3-way agreement logic.

```bash
python -m finetune.main label
```
Output: `data/labeled/agreed/approved.jsonl`

**Cost**: ~$0.01 per 1000 samples (GPT-4o-mini)

### Step 3: Build
Create train/val/test splits (70/15/15 stratified).

```bash
python -m finetune.main build --version v1.0
```
Output: `data/datasets/v1.0/{train,val,test}.jsonl`

### Step 4: Train
Fine-tune with LoRA via Unsloth or TRL.

```bash
python -m finetune.main train --version v1.0
```
Output: `data/artifacts/{run_id}/lora_adapter/`

### Step 5: Evaluate
Calculate metrics: accuracy, F1 macro, per-class F1, confusion matrix.

```bash
python -m finetune.main evaluate --version v1.0
```
Output: `data/artifacts/latest/eval_result.json`

### Step 6: Decide
Promotion decision based on thresholds.

```bash
python -m finetune.main decide
```

---

## Key Files

| File | Purpose |
|------|---------|
| `finetune/domain/services/label_agreement.py` | 3-way agreement logic (5 cases) |
| `finetune/domain/services/promotion_decider.py` | Promotion thresholds |
| `finetune/infrastructure/training/unsloth_trainer.py` | LoRA training code |
| `finetune/infrastructure/evaluation/sklearn_evaluator.py` | Metrics calculation |
| `configs/evaluation/promotion_rules.yml` | Promotion thresholds |

---

## Common Tasks

### Run Tests
```bash
python -m pytest tests/unit/ -v
```

### Add New Emotion
1. Update `configs/emotions.yml`
2. Update `finetune/domain/value_objects.py` - add to EmotionLabel enum

### Modify Training Config
Edit `configs/training/qwen2.5_1.5b_lora.yml`

### Check GPU Availability
```bash
nvidia-smi
```

---

## Environment Requirements

### Python
- Python 3.10+ recommended
- Use virtual environment to avoid conflicts

### Dependencies
```bash
pip install -r requirements.txt
pip install unsloth  # For training (GPU required)
```

### API Keys (in .env)
- `OPENAI_API_KEY` - For labeling
- `HF_TOKEN` - For model push

---

## Known Issues

1. **Unsloth import error**: May have torch version conflict. Use TRL as alternative.
2. **Distilabel async issues**: Use `OpenAILabeler` instead for simpler pipeline.

---

## Architecture Notes

- **Clean Architecture**: Domain → Application → Infrastructure
- **DDD Patterns**: Entities, Value Objects, Services
- **Dependency Rule**: Inner layers don't know about outer layers

---

*Last updated: 2026-03-06*
