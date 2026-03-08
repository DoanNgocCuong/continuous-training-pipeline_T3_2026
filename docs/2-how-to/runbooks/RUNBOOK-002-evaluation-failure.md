# Runbook: Evaluation Failure

**Incident ID**: RUNBOOK-002
**Severity**: High
**Last Updated**: 2026-03-08

---

## Symptom

Evaluation fails or produces unexpected results.

---

## Detection

```bash
# Run evaluation
python -m finetune.main evaluate --version v1.0
```

---

## Diagnosis

### Step 1: Check Error

```bash
# Check logs
tail -f logs/pipeline.log

# Look for specific errors
grep -i "error\|exception" logs/pipeline.log
```

### Step 2: Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `Model not found` | Wrong path | Check model path |
| `Empty test set` | No test data | Rebuild dataset |
| `NaN metrics` | Model issue | Check model quality |
| `Import error` | Missing deps | Install packages |

### Step 3: Verify Model

```bash
# Check model files exist
ls -la data/artifacts/latest/

# Check model can load
python -c "from transformers import AutoModel; print('OK')"
```

---

## Resolution

### Fix: Model Not Found

```bash
# List available models
ls -la data/artifacts/

# Use correct path
python -m finetune.main evaluate --model-path data/artifacts/{run_id}
```

### Fix: Empty Metrics

```bash
# Check test dataset
wc -l data/datasets/v1.0/test.jsonl

# Rebuild if needed
python -m finetune.main build --version v1.0
```

---

## Verification

```bash
# Run evaluation again
python -m finetune.main evaluate --version v1.0

# Check results
cat data/artifacts/latest/eval_result.json
```

Expected fields:
- `accuracy`: float 0-1
- `f1_macro`: float 0-1
- `f1_per_class`: dict
- `confusion_matrix`: list

---

## Prevention

- Always verify model exists before evaluation
- Check test dataset is not empty
- Monitor for NaN values in training

---

## Contact

- **On-call**: ML Team
- **Slack**: #ml-incidents

---

## Related

- [RUNBOOK-001: Training Failure](RUNBOOK-001-training-failure.md)
- [RUNBOOK-003: Promotion Decision Failure](RUNBOOK-003-promotion-decision-failure.md)
