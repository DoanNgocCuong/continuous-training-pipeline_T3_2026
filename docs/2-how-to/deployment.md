# Deployment Guide

How to deploy the Emotion CT Pipeline to production environments.

---

## Overview

This guide covers:
1. Local deployment for testing
2. Production deployment with GitHub Actions
3. Canary deployment for ML models
4. Rollback procedures

---

## Prerequisites

- [ ] Trained model with satisfactory metrics
- [ ] Model promoted (passed `decide` step)
- [ ] HuggingFace token configured (for cloud deployment)
- [ ] MLflow server running (for model registry)

---

## Step 1: Quantize the Model

Before deploying, quantize the model to reduce size and improve inference speed:

```bash
python -m finetune.main quantize \
  --adapter-path data/artifacts/{run_id}/lora_adapter \
  --base-model Qwen/Qwen2.5-1.5B-Instruct \
  --output-dir data/artifacts/quantized
```

---

## Step 2: Publish to Registries

### Push to HuggingFace Hub

```bash
python -m finetune.main publish \
  --model-path data/artifacts/quantized \
  --version v1.0 \
  --eval-report data/artifacts/latest/eval_report.md \
  --hf true
```

### Register in MLflow

```bash
python -m finetune.main publish \
  --model-path data/artifacts/quantized \
  --version v1.0 \
  --mlflow-log true
```

---

## Step 3: Deploy to Production

### Option A: GitHub Actions (Recommended)

The pipeline automatically deploys on promotion:

```yaml
# Workflow already configured in .github/workflows/ct-pipeline.yml
# Triggers on: schedule, manual dispatch, data changes
```

### Option B: Manual Deployment

```bash
# Deploy using canary
python -m finetune.main canary-deploy \
  --version v1.0 \
  --traffic 10 \
  --config configs/deployment/canary.yml
```

---

## Step 4: Verify Deployment

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model": "qwen2.5-1.5b-emotion-v1.0",
  "timestamp": "2026-03-08T10:30:00Z"
}
```

### Test Inference

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "I am so happy today!"}'
```

Expected response:
```json
{
  "label": "happy",
  "confidence": 0.95
}
```

---

## Canary Deployment

### Overview

Canary deployment rolls out the model gradually:

1. Deploy to 10% traffic
2. Monitor health metrics
3. Gradually increase to 25%, 50%, 75%, 100%
4. Rollback if issues detected

### Configuration

Edit `configs/deployment/canary.yml`:

```yaml
canary:
  initial_traffic_percent: 10
  traffic_increments: [25, 50, 75, 100]
  increment_interval: 300  # 5 minutes

health_checks:
  error_rate_threshold: 1.0
  latency_p95_threshold: 500
  availability_threshold: 99.0
```

### Manual Canary

```bash
# Deploy to canary
python -m finetune.main canary-deploy --version v1.0 --traffic 10

# Check status
python -m finetune.main canary-deploy --version v1.0 --traffic 25

# Promote to production
python -m finetune.main canary-deploy --version v1.0 --traffic 100 --promote
```

---

## Rollback

### When to Rollback

- Error rate > 2%
- Latency p95 > 1000ms
- Availability < 98%
- Significant accuracy regression

### Rollback Command

```bash
python -m finetune.main rollback --version v1.0
```

This will:
1. Stop traffic to current version
2. Restore previous version from MLflow
3. Promote previous version to production

---

## Monitoring

### View Metrics

```bash
# Check MLflow
open http://localhost:5000

# Check drift
python -m finetune.main monitor-drift --baseline-version v1.0 --alert
```

### Set Up Alerts

Configure in `configs/monitoring/drift_thresholds.yml`:

```yaml
alerts:
  channels:
    - slack
    - email
  alert_on:
    - data_drift
    - performance_drift
```

---

## Infrastructure Setup

### MLflow Server

```bash
# Start MLflow
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlflow-artifacts \
  --port 5000
```

### Optional: Langfuse

```bash
# Set environment variables
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...

# Run pipeline with observability
python -m finetune.main pipeline --enable-observability
```

---

## Troubleshooting

### Model Not Loading

```bash
# Check model files exist
ls -la data/artifacts/quantized/

# Verify quantization worked
python -c "import autoawq; print('AWQ installed')"
```

### Inference Errors

```bash
# Check GPU availability
nvidia-smi

# Check logs
tail -f logs/pipeline.log
```

### High Latency

1. Check model size (should be ~1GB for AWQ)
2. Enable quantization if not already
3. Use GPU inference
4. Check batch size settings

---

## Next Steps

- [Runbooks](../2-how-to/runbooks/) - Incident procedures
- [Postmortems](../2-how-to/postmortem/) - After-action reports

---

*Last updated: 2026-03-08*
