# Postmortem: Initial Model Accuracy Too Low

**Incident ID**: PM-001
**Date**: 2026-03-06
**Severity**: Medium
**Status**: Resolved

---

## Summary

The initial trained model achieved only 35.7% accuracy on the test set, below the 40% promotion threshold.

---

## What Happened

1. First full pipeline run completed successfully
2. Training finished in 3.5 minutes with loss 0.092
3. Evaluation showed 35.7% accuracy (below 40% threshold)
4. Model was rejected by promotion decision

---

## Timeline

| Time | Event |
|------|-------|
| 2026-03-06 02:00 | Pipeline started |
| 2026-03-06 02:05 | Data collection complete (1000 samples) |
| 2026-03-06 02:07 | AI labeling complete (GPT-4o-mini) |
| 2026-03-06 02:10 | Dataset split complete |
| 2026-03-06 02:14 | Training complete |
| 2026-03-06 02:15 | Evaluation complete |
| 2026-03-06 02:15 | Promotion rejected |

---

## Root Cause

1. **Small dataset**: Only 697 training samples
2. **Class imbalance**:
   - happy: 35.4%
   - thinking: 31.0%
   - calm: 24.3%
   - Other 10 emotions: < 10% combined

---

## Impact

- Model cannot be promoted to production
- Requires more data collection
- Delays deployment timeline by 1-2 weeks

---

## Detection

- Automated: Promotion decision step
- Manual: Review of eval results

---

## Recovery

1. Identify need for more data
2. Document threshold failures
3. Plan data collection

---

## Prevention

1. **Increase data collection**:
   - Target: 10,000+ samples
   - Stratified sampling to balance classes

2. **Class balancing**:
   - Oversample minority classes
   - Use class weights in training

3. **Better thresholds**:
   - Set realistic thresholds for initial iterations
   - Adjust based on baseline capabilities

---

## Lessons Learned

- Start with realistic expectations for small datasets
- Class imbalance is a major issue for 13-class problems
- Need stratified sampling for minority classes

---

## Action Items

| Item | Owner | Due |
|------|-------|-----|
| Collect 5000+ more samples | Data Team | 2026-03-15 |
| Implement class balancing | ML Team | 2026-03-20 |
| Update promotion thresholds | ML Team | 2026-03-20 |

---

## Related

- [RUNBOOK-003: Promotion Decision Failure](../2-how-to/runbooks/RUNBOOK-003-promotion-decision-failure.md)
- [Evaluation Results](../3-reference/SDD.md)
