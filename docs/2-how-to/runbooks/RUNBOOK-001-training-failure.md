# Runbook: Training Failure

**Incident ID**: RUNBOOK-001
**Severity**: High
**Last Updated**: 2026-03-08

---

## Symptom

Training fails with error during LoRA fine-tuning.

---

## Detection

```bash
# Check training logs
tail -f logs/pipeline.log

# Or check CLI output
python -m finetune.main train --version v1.0
```

---

## Diagnosis

### Step 1: Check Error Type

```bash
# Look for common errors
grep -i "error\|exception\|traceback" logs/pipeline.log
```

### Step 2: Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `CUDA out of memory` | GPU memory insufficient | Reduce batch size in config |
| `ModuleNotFoundError` | Missing dependency | Install required package |
| `FileNotFoundError` | Missing dataset | Run `build` command first |
| `TimeoutError` | Network issue | Check internet connection |

### Step 3: Verify Environment

```bash
# Check Python version
python --version

# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Check installed packages
pip list | grep -E "torch|transformers|trl"
```

---

## Resolution

### Fix: Out of Memory

1. Edit `configs/training/qwen2.5_1.5b_lora.yml`:

```yaml
training:
  batch_size: 2  # Reduce from 4
  gradient_accumulation: 8  # Increase to compensate
```

2. Retry training:

```bash
python -m finetune.main train --version v1.0
```

### Fix: Missing Dependency

```bash
# Install missing package
pip install <package-name>

# Or reinstall all
pip install -r requirements.txt
```

### Fix: Dataset Not Found

```bash
# Check dataset exists
ls -la data/datasets/v1.0/

# If not, rebuild
python -m finetune.main build --version v1.0
```

---

## Verification

```bash
# Check training completed
ls -la data/artifacts/*/lora_adapter/

# Check run metadata
cat data/artifacts/*/run_metadata.json
```

---

## Prevention

- Always check GPU memory before training
- Use `nvidia-smi` to monitor
- Set appropriate batch sizes
- Keep dependencies up to date

---

## Contact

- **On-call**: ML Team
- **Slack**: #ml-incidents

---

## Related

- [Deployment Guide](../deployment.md)
- [RUNBOOK-002: Evaluation Failure](RUNBOOK-002-evaluation-failure.md)
