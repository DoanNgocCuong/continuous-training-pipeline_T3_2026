# Runbook: Promotion Decision Failure

**Incident ID**: RUNBOOK-003
**Severity**: Medium
**Last Updated**: 2026-03-08

---

## Symptom

Model is rejected by promotion decision (fails thresholds).

---

## Detection

```bash
# Run promotion decision
python -m finetune.main decide
```

Output shows: `REJECT: <reason>`

---

## Diagnosis

### Step 1: Check Evaluation Results

```bash
# View eval results
cat data/artifacts/latest/eval_result.json
```

### Step 2: Compare Against Baseline

```bash
# Compare metrics
cat data/artifacts/baseline/eval_result.json  # baseline
cat data/artifacts/latest/eval_result.json    # current
```

### Step 3: Identify Failed Thresholds

| Threshold | Current | Required | Status |
|-----------|---------|----------|--------|
| accuracy | 0.357 | >= 0.40 | ❌ |
| f1_macro | 0.278 | >= 0.35 | ❌ |
| per_class_f1 | varies | no drop > 2% | ❌ |

---

## Resolution

### Root Cause Analysis

Common causes:
1. **Small dataset**: Only 697 training samples
2. **Class imbalance**: happy 35%, thinking 31%, calm 24%
3. **Insufficient training**: Need more epochs or data

### Fix: Collect More Data

```bash
# Add more raw data
python -m finetune.main collect --source data/raw/more_data.csv

# Re-run pipeline
python -m finetune.main pipeline --version v1.1
```

### Fix: Improve Labeling

```bash
# Review flagged samples
cat data/labeled/agreed/flagged.jsonl | head -20

# Use Argilla for human review
python -m finetune.main review --dataset emotion-review

# Re-label
python -m finetune.main label
```

### Fix: Adjust Thresholds (Temporary)

Edit `configs/evaluation/promotion_rules.yml`:

```yaml
thresholds:
  accuracy:
    min: 0.30  # Lower temporarily
    relative_improvement: 0.003
```

> **Warning**: Lowering thresholds is not recommended long-term.

---

## Verification

```bash
# Re-run decision
python -m finetune.main decide
```

Expected: `PROMOTE: <reason>`

---

## Prevention

- Continuously collect more training data
- Monitor class distribution
- Set realistic thresholds based on baseline
- Use human-in-the-loop for edge cases

---

## Contact

- **On-call**: ML Team
- **Slack**: #ml-incidents

---

## Related

- [RUNBOOK-001: Training Failure](RUNBOOK-001-training-failure.md)
- [RUNBOOK-002: Evaluation Failure](RUNBOOK-002-evaluation-failure.md)
- [ADR-001: Why DDD Structure](../4-explanation/ADR-001-ddd-structure.md)
