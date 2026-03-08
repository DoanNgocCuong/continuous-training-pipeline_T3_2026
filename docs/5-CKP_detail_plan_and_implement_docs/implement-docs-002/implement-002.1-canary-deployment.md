# Implementation: Canary Deployment System

**ID**: implement-docs-002.1
**Date**: 2026-03-08
**Status**: Implemented

---

## Overview

Implements gradual rollout and rollback for ML model deployment.

---

## Files Created

### Scripts

- `scripts/deploy_canary.py`

### Infrastructure

- `finetune/infrastructure/deployment/health_checker.py`

### Configuration

- `configs/deployment/canary.yml`

### CLI

- `canary-deploy` command
- `rollback` command

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Canary Deployment Flow                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   MLflow     │───►│  Promote to  │───►│   Health    │
│   Registry   │    │   Staging    │    │   Check     │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                                │
                                                ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Promote    │◄───│  Gradual    │◄───│   Wait for  │
│   to Prod    │    │   Rollout   │    │   Healthy   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Features

### 1. Gradual Rollout

Traffic percentages: 10% → 25% → 50% → 75% → 100%

### 2. Health Checks

- Error rate < 1%
- Latency p95 < 500ms
- Availability > 99%

### 3. Auto Rollback

Triggered when:
- Error rate > 2%
- Latency p95 > 1000ms
- Availability < 98%

### 4. MLflow Integration

- Models promoted through stages: Staging → Production
- Version tracking in registry

---

## Usage

### Deploy Canary

```bash
python -m finetune.main canary-deploy \
  --version v1.0 \
  --traffic 10 \
  --config configs/deployment/canary.yml
```

### Promote

```bash
python -m finetune.main canary-deploy \
  --version v1.0 \
  --promote
```

### Rollback

```bash
python -m finetune.main rollback \
  --version v1.0 \
  --config configs/deployment/canary.yml
```

---

## Configuration

```yaml
# configs/deployment/canary.yml
canary:
  initial_traffic_percent: 10
  traffic_increments: [25, 50, 75, 100]
  increment_interval: 300

health_checks:
  check_interval: 30
  success_threshold: 3
  failure_threshold: 3
  metrics:
    error_rate_threshold: 1.0
    latency_p95_threshold: 500

rollback:
  auto_rollback: true
  grace_period: 60
```

---

## Integration

### Health Checker

```python
from finetune.infrastructure.deployment.health_checker import HealthChecker

checker = HealthChecker(
    health_endpoint="http://localhost:8000/health",
    metrics_endpoint="http://localhost:8000/metrics",
)

# Wait for healthy
is_healthy = checker.wait_for_healthy(
    success_threshold=3,
    failure_threshold=3,
)
```

### MLflow Registry

```python
from finetune.infrastructure.registry.mlflow_registry import MLflowRegistry

registry = MLflowRegistry()

# Promote to staging
registry.promote_to_staging("1")

# Promote to production
registry.promote_to_production("1")
```

---

## Testing

```bash
# Test canary deployment
python scripts/deploy_canary.py --version v1.0 --traffic 10

# Test rollback
python scripts/deploy_canary.py --version v1.0 --rollback
```

---

## Related

- [Deployment Guide](../2-how-to/deployment.md)
- [ADR-003: LoRA Choice](../4-explanation/ADR-003-lora-choice.md)

---

*Last updated: 2026-03-08*
