# Implementation: Drift Detection System

**ID**: implement-docs-001.1
**Date**: 2026-03-08
**Status**: Implemented

---

## Overview

Implements data drift and performance drift detection for the continuous training pipeline.

---

## Files Created

### Domain Layer

- `finetune/domain/services/data_drift_detector.py`
- `finetune/domain/services/performance_drift_detector.py`

### Infrastructure Layer

- `finetune/infrastructure/monitoring/baseline_store.py`

### Configuration

- `configs/monitoring/drift_thresholds.yml`

### CLI

- `monitor-drift` command in `finetune/main.py`

---

## Algorithm

### Data Drift Detection

#### KL Divergence

$$D_{KL}(P || Q) = \sum_i P(i) \log\frac{P(i)}{Q(i)}$$

Used to measure distribution shift between baseline and current label distributions.

#### Population Stability Index (PSI)

$$PSI = \sum_i (Actual_i - Expected_i) \times \ln\frac{Actual_i}{Expected_i}$$

| PSI Value | Interpretation |
|-----------|----------------|
| < 0.1 | No change |
| 0.1 - 0.2 | Some change |
| > 0.2 | Major shift |

#### Chi-Squared Test

Statistical test to determine if distributions are significantly different.

### Performance Drift Detection

```python
# Accuracy drift
if baseline_accuracy - current_accuracy > threshold:
    has_drift = True

# F1 macro drift
if baseline_f1 - current_f1 > threshold:
    has_drift = True
```

---

## Usage

### CLI Command

```bash
python -m finetune.main monitor-drift \
  --baseline-version v1.0 \
  --current-version latest \
  --alert
```

### Programmatic

```python
from finetune.domain.services.data_drift_detector import DataDriftDetector
from finetune.domain.services.performance_drift_detector import PerformanceDriftDetector
from finetune.infrastructure.monitoring.baseline_store import BaselineStore

# Load baselines
store = BaselineStore()
baseline = store.load_baseline("v1.0")
current = store.load_baseline("latest")

# Detect data drift
data_detector = DataDriftDetector()
data_results = data_detector.detect(
    baseline.get("label_distribution", {}),
    current.get("label_distribution", {}),
)

# Detect performance drift
perf_detector = PerformanceDriftDetector()
perf_results = perf_detector.detect(
    baseline.get("metrics", {}),
    current.get("metrics", {}),
)
```

---

## Integration Points

1. **BaselineStore** - Stores historical metrics
2. **NotificationClient** - Sends alerts when drift detected
3. **GitHub Actions** - Scheduled drift checks

---

## Testing

```bash
# Run tests
python -m pytest tests/unit/test_drift_detector.py -v
```

---

## Related

- [ADR-001: DDD Structure](../4-explanation/ADR-001-ddd-structure.md)
- [Runbook: Performance Drift](../2-how-to/runbooks/RUNBOOK-004-performance-drift.md)

---

*Last updated: 2026-03-08*
