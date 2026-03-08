# API Reference

## CLI Commands

All commands are accessed via `python -m finetune.main`.

---

## Pipeline Commands

### collect

Load raw data from CSV export.

```bash
python -m finetune.main collect --source data/raw/extract.csv
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source` | str | `data/raw/extract.csv` | Path to CSV file |

**Output**: `data/labeled/raw_samples.jsonl`

---

### label

AI label + 3-way agreement logic.

```bash
python -m finetune.main label \
  --input-path data/labeled/raw_samples.jsonl \
  --model gpt-4o-mini
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--input-path` | str | `data/labeled/raw_samples.jsonl` | Input JSONL file |
| `--model` | str | `gpt-4o-mini` | Labeling model |

**Output**:
- `data/labeled/agreed/approved.jsonl`
- `data/labeled/agreed/flagged.jsonl`

---

### build

Build train/val/test splits (70/15/15 stratified).

```bash
python -m finetune.main build --version v1.0
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | str | `v1.0` | Dataset version tag |

**Output**: `data/datasets/{version}/{train,val,test}.jsonl`

---

### train

Fine-tune with LoRA via TRL.

```bash
python -m finetune.main train \
  --version v1.0 \
  --config qwen2.5_1.5b_lora
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | str | `v1.0` | Dataset version |
| `--config` | str | `qwen2.5_1.5b_lora` | Training config name |

**Output**: `data/artifacts/{run_id}/lora_adapter/`

---

### evaluate

Calculate metrics: accuracy, F1 macro, per-class F1, confusion matrix.

```bash
python -m finetune.main evaluate \
  --model-path data/artifacts/latest \
  --version v1.0 \
  --regression true \
  --report-dir data/artifacts/latest
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--model-path` | str | `data/artifacts/latest` | Path to model |
| `--version` | str | `v1.0` | Dataset version |
| `--regression` | bool | `true` | Run regression tests |
| `--report-dir` | str | `data/artifacts/latest` | Report output dir |

**Output**: `data/artifacts/latest/eval_result.json`

---

### decide

Promotion decision based on thresholds.

```bash
python -m finetune.main decide \
  --candidate-path data/artifacts/latest/eval_result.json \
  --baseline-path data/artifacts/baseline/eval_result.json
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--candidate-path` | str | `data/artifacts/latest/eval_result.json` | Candidate eval result |
| `--baseline-path` | str | `data/artifacts/baseline/eval_result.json` | Baseline eval result |

**Output**: Exit code 0 (promote) or 1 (reject)

---

## Publishing Commands

### publish

Publish promoted model to HuggingFace Hub and/or MLflow.

```bash
python -m finetune.main publish \
  --model-path data/artifacts/quantized \
  --version v1.0 \
  --eval-report data/artifacts/latest/eval_report.md \
  --hf true \
  --mlflow-log true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--model-path` | str | **required** | Path to quantized model |
| `--version` | str | **required** | Version tag |
| `--eval-report` | str | None | Path to eval report |
| `--hf` | bool | `true` | Push to HuggingFace |
| `--mlflow-log` | bool | `false` | Register in MLflow |

**Output**:
- HuggingFace: `https://huggingface.co/{repo}/{model}`
- MLflow: `models:/{name}/{version}`

---

### quantize

Merge LoRA adapter + AWQ 4-bit quantization.

```bash
python -m finetune.main quantize \
  --adapter-path data/artifacts/{run_id}/lora_adapter \
  --base-model Qwen/Qwen2.5-1.5B-Instruct \
  --output-dir data/artifacts/quantized
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--adapter-path` | str | **required** | LoRA adapter path |
| `--base-model` | str | `Qwen/Qwen2.5-1.5B-Instruct` | Base model |
| `--output-dir` | str | `data/artifacts/quantized` | Output directory |

**Output**: Quantized model at `--output-dir`

---

### push-dataset

Push dataset to HuggingFace Hub.

```bash
python -m finetune.main push-dataset \
  --version v1.0 \
  --dataset-type train
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | str | **required** | Dataset version |
| `--dataset-type` | str | `train` | Dataset split |

**Output**: `https://huggingface.co/datasets/{repo}/{dataset}`

---

## Enhanced Pipeline Commands

### review

Pull human-reviewed annotations from Argilla.

```bash
python -m finetune.main review \
  --dataset emotion-review \
  --output-path data/labeled/argilla_reviewed.jsonl
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dataset` | str | `emotion-review` | Argilla dataset name |
| `--output-path` | str | `data/labeled/argilla_reviewed.jsonl` | Output file |

**Output**: JSONL file with human-reviewed samples

---

### monitor-drift

Monitor data and performance drift.

```bash
python -m finetune.main monitor-drift \
  --baseline-version v1.0 \
  --current-version latest \
  --alert true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--baseline-version` | str | `v1.0` | Baseline version |
| `--current-version` | str | `latest` | Current version |
| `--alert` | bool | `false` | Send alert if drift detected |

**Output**: Drift detection results to stdout

---

## Production Commands

### canary-deploy

Deploy model to canary with gradual rollout.

```bash
python -m finetune.main canary-deploy \
  --version v1.0 \
  --traffic 10 \
  --config configs/deployment/canary.yml
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | str | **required** | Model version |
| `--traffic` | int | `10` | Initial traffic % |
| `--config` | str | `configs/deployment/canary.yml` | Config path |

**Output**: Deployment status to stdout

---

### rollback

Rollback to previous model version.

```bash
python -m finetune.main rollback \
  --version v1.0 \
  --config configs/deployment/canary.yml
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | str | **required** | Version to rollback from |
| `--config` | str | `configs/deployment/canary.yml` | Config path |

**Output**: Rollback status to stdout

---

## Full Pipeline

### pipeline

Run full pipeline with optional MLflow and observability.

```bash
python -m finetune.main pipeline \
  --source data/raw/extract.csv \
  --config qwen2.5_1.5b_lora \
  --version v1.0 \
  --enable-mlflow true \
  --enable-observability true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source` | str | `data/raw/extract.csv` | Input CSV |
| `--config` | str | `qwen2.5_1.5b_lora` | Training config |
| `--version` | str | `v1.0` | Pipeline version |
| `--enable-mlflow` | bool | `false` | Enable MLflow logging |
| `--enable-observability` | bool | `false` | Enable Langfuse tracing |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for labeling |
| `HF_TOKEN` | No | HuggingFace token for model push |
| `MLFLOW_TRACKING_URI` | No | MLflow server URL |
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret key |
| `ARGILLA_API_KEY` | No | Argilla API key |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for alerts |
| `DISCORD_WEBHOOK_URL` | No | Discord webhook for alerts |

---

*Last updated: 2026-03-08*
