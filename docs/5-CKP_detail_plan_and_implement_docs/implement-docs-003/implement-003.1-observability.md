# Implementation: Observability System

**ID**: implement-docs-003.1
**Date**: 2026-03-08
**Status**: Implemented

---

## Overview

Implements Langfuse tracing, cost tracking, and notifications for the pipeline.

---

## Files Created

### Infrastructure

- `finetune/infrastructure/observability/langfuse_tracer.py`
- `finetune/infrastructure/observability/cost_tracker.py`
- `finetune/infrastructure/observability/notification_client.py`

### Configuration

- `configs/observability/langfuse.yml`

---

## Features

### 1. Langfuse Tracing

```python
from finetune.infrastructure.observability.langfuse_tracer import get_tracer

tracer = get_tracer()

# Trace a generation
with tracer.trace_generation("labeling") as trace:
    # Do work
    trace.generation(
        input="Hello!",
        output="happy",
    )
```

### 2. Cost Tracking

```python
from finetune.infrastructure.observability.cost_tracker import get_cost_tracker

tracker = get_cost_tracker()

# Track a call
call_id = "call_001"
tracker.start_call(call_id)

# ... make API call ...

tracker.end_call(
    call_id,
    model="gpt-4o-mini",
    input_tokens=100,
    output_tokens=50,
)

# Get summary
summary = tracker.get_summary()
print(f"Total cost: ${summary.total_cost_usd}")
```

### 3. Notifications

```python
from finetune.infrastructure.observability.notification_client import get_notification_client

notification = get_notification_client()

# Send notification
notification.notify_pipeline_start(version="v1.0", steps=["collect", "label"])
notification.notify_promotion(version="v1.0", decision="promote", reason="Metrics exceeded thresholds")
notification.notify_drift_alert(drift_type="performance", metric="accuracy", current=0.35, threshold=0.40)
```

---

## Configuration

```yaml
# configs/observability/langfuse.yml
langfuse:
  public_key: ${LANGFUSE_PUBLIC_KEY:-}
  secret_key: ${LANGFUSE_SECRET_KEY:-}
  host: ${LANGFUSE_HOST:-https://cloud.langfuse.com}

tracing:
  enabled: ${LANGFUSE_ENABLED:-true}
  service_name: emotion-ct-pipeline

cost_tracking:
  enabled: true
  pricing:
    gpt4o_mini:
      input: 0.00015
      output: 0.0006
```

---

## Usage

### Enable in Pipeline

```bash
python -m finetune.main pipeline --version v1.0 --enable-observability
```

### Standalone Usage

```python
from finetune.infrastructure.observability.langfuse_tracer import is_enabled

if is_enabled():
    # Langfuse is configured
    pass
```

---

## Integration Points

1. **Labeling** - Trace AI labeling calls
2. **Training** - Trace training progress
3. **Evaluation** - Trace metrics
4. **GitHub Actions** - Slack notifications

---

## Testing

```bash
# Test notification
python -c "
from finetune.infrastructure.observability.notification_client import NotificationClient
client = NotificationClient()
result = client.notify_pipeline_start('v1.0', ['collect', 'label'])
print(f'Sent: {result}')
"
```

---

## Related

- [SDD - Technology Stack](../3-reference/SDD.md)
- [Deployment Guide](../2-how-to/deployment.md)

---

*Last updated: 2026-03-08*
