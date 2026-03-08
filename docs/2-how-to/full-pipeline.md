# Full Pipeline Guide

Hướng dẫn chạy toàn bộ pipeline từ đầu đến cuối.

---

## Overview

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Collect   │ → │    Label    │ → │   Build     │ → │   Train     │
│  CSV Data   │   │  AI + Human │   │   Split     │   │  LoRA       │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
       │                 │                │                 │
       ▼                 ▼                ▼                 ▼
  data/raw/      data/labeled/      data/datasets/    data/artifacts/
                                                                    │
┌─────────────┐   ┌─────────────┐                              │
│  Evaluate   │ → │   Decide    │ ────────────────────────────┘
│   Sklearn   │   │  Promote?  │
└─────────────┘   └─────────────┘
       │
       ▼
  data/artifacts/
```

---

## Bước 1: Chuẩn bị Môi trường

### 1.1 Khởi động Infrastructure

```bash
# Start all services (Argilla, MLflow, PostgreSQL, etc.)
docker compose -f docker-compose-infra.yml --profile all up -d
```

**Services:**
| Service | URL | Credentials |
|---------|-----|-------------|
| Argilla UI | http://localhost:6900 | admin / adminpassword |
| MLflow | http://localhost:5010 | (no auth) |
| MinIO | http://localhost:9011 | minioadmin / minioadmin |

### 1.2 Cài đặt Python dependencies

```bash
# Activate venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 1.3 Cấu hình Environment Variables

Đảm bảo `.env` có:
```bash
OPENAI_API_KEY=sk-...
HF_TOKEN=hf-...
MLFLOW_TRACKING_URI=http://localhost:5010
```

---

## Bước 2: Collect Data

### Từ CSV (Datadog export)

```bash
python -m finetune.main collect --source data/raw/unlabeled/extract_1k.csv
```

**Output:** `data/labeled/raw_samples.jsonl`

### Từ Excel

```bash
# Convert xlsx to csv first
python -c "
import pandas as pd
df = pd.read_excel('data/raw/results_v3_grouped_100kRequests.xlsx')
df.to_csv('data/raw/extract.csv', index=False)
"

# Then collect
python -m finetune.main collect --source data/raw/unlabeled/extract_1k.csv
```

### Data Files Convention

```
data/
├── raw/
│   ├── unlabeled/                    # Chưa có nhãn - cần qua Label step
│   │   ├── extract.csv
│   │   ├── extract_2026.csv
│   │   └── results_v3_grouped_100kRequests.xlsx
│   └── labeled/                     # Đã có nhãn sẵn (human expert)
│       └── prelabeled.xlsx
```

**2 Loại Data:**

| Loại | Location | Format | Flow |
|------|----------|--------|------|
| Unlabeled | `data/raw/unlabeled/` | CSV/XLSX (chỉ có `text`) | Collect → Label → Push to Argilla → Build |
| Pre-labeled | `data/raw/labeled/` | XLSX (có `text` + `label`) | Collect → Audit in Argilla → Build |

> **Lưu ý**: Sau khi chạy Collect/Label, cần push lên Argilla UI để xem và review.

### Pre-labeled Data (đã có nhãn)

```bash
# Convert pre-labeled xlsx to csv
python -c "
import pandas as pd
df = pd.read_excel('data/raw/labeled/prelabeled.xlsx')
df.to_csv('data/raw/labeled/prelabeled.csv', index=False)
"

# Collect với pre-labeled flag
python -m finetune.main collect --source data/raw/labeled/prelabeled.csv --prelabeled
```

**Output:** `data/labeled/agreed/approved.jsonl` (đi thẳng vào approved)

### Audit Pre-labeled Data (kiểm tra chất lượng)

```bash
# Push lên Argilla để human audit
python -m finetune.main audit --input-path data/labeled/agreed/approved.jsonl --dataset emotion-audit

# View in UI: http://localhost:6900
# Dataset: emotion-audit
```

---

## Bước 3: Label Data

### AI Labeling (GPT-4o-mini)

```bash
python -m finetune.main label \
  --input-path data/labeled/raw_samples.jsonl \
  --model gpt-4o-mini
```

**Output:**
- `data/labeled/agreed/approved.jsonl` - Đã approve
- `data/labeled/agreed/flagged.jsonl` - Cần review

### Xem labels trong Argilla UI

#### Unlabeled Data Flow (cần AI label trước)

```bash
# Bước 1: Collect + AI Label
python -m finetune.main collect --source data/raw/unlabeled/extract_1k.csv
python -m finetune.main label --input-path data/labeled/raw_samples.jsonl

# Bước 2: Push lên Argilla UI để view/review
python -m finetune.main label --push-to-argilla

# Bước 3: Mở browser
# http://localhost:6900
# Login: admin / adminpassword
# Dataset: emotion-review

# Bước 4: Sau khi annotate trong UI, pull về
python -m finetune.main review --dataset emotion-review

# Bước 5: Merge với approved data
# (Đang implement...)
```

#### Pre-labeled Data Flow (đã có nhãn sẵn)

```bash
# Bước 1: Collect pre-labeled data
python -m finetune.main collect --source data/raw/labeled/prelabeled.csv --prelabeled

# Bước 2: Push lên Argilla UI để audit/verify
python -m finetune.main audit

# Bước 3: Mở browser
# http://localhost:6900
# Login: admin / adminpassword
# Dataset: emotion-audit
```

**Argilla Credentials:**
- URL: http://localhost:6900
- Username: admin
- Password: adminpassword

**Trong Argilla UI:**
- Dataset `emotion-review` - Cho unlabeled data cần review
- Dataset `emotion-audit` - Cho pre-labeled data cần audit
- Cột `text` = nội dung cần xem
- Metadata `ai_label` = gợi ý từ AI (có thể override)
- Sau khi annotate, record sẽ có status "submitted"

### Xem nhanh label distribution

```bash
python -c "
import json
with open('data/labeled/agreed/approved.jsonl') as f:
    labels = {}
    for line in f:
        d = json.loads(line)
        label = d.get('agreed_label', 'unknown')
        labels[label] = labels.get(label, 0) + 1
    for k, v in sorted(labels.items(), key=lambda x: -x[1]):
        print(f'{k:15} {v:4} ({v*100/1000:.1f}%)')
"
```

---

## Bước 4: Build Dataset

```bash
python -m finetune.main build --version v1.0
```

**Output:** `data/datasets/v1.0/`
```
v1.0/
├── train.jsonl          (70%)
├── val.jsonl            (15%)
├── test.jsonl           (15%)
├── train_chatml.jsonl   (for training)
└── val_chatml.jsonl    (for training)
```

---

## Bước 5: Train Model

```bash
python -m finetune.main train \
  --version v1.0 \
  --config qwen2.5_1.5b_lora
```

**Output:** `data/artifacts/{run_id}/lora_adapter/`

**Training logs:**
```bash
# Xem logs
tail -f logs/pipeline.log
```

**Kiểm tra GPU:**
```bash
nvidia-smi
```

---

## Bước 6: Evaluate

```bash
python -m finetune.main evaluate \
  --version v1.0 \
  --model-path data/artifacts/latest
```

**Output:** `data/artifacts/latest/eval_result.json`

**Xem kết quả:**
```bash
cat data/artifacts/latest/eval_result.json | python -m json.tool
```

**Metrics:**
```json
{
  "accuracy": 0.357,
  "f1_macro": 0.278,
  "f1_per_class": {
    "happy": 0.141,
    "thinking": 0.458,
    "calm": 0.444
  }
}
```

---

## Bước 7: Decide (Promotion)

```bash
python -m finetune.main decide
```

**Output:**
- Exit 0 = Promote ✅
- Exit 1 = Reject ❌

---

## Bước 8: Publish

### MLflow (Experiment Tracking)

```bash
python -m finetune.main publish \
  --version v1.0 \
  --model-path data/artifacts/quantized \
  --mlflow-log
```

**View:** http://localhost:5010

### HuggingFace Hub

```bash
python -m finetune.main publish \
  --version v1.0 \
  --model-path data/artifacts/quantized \
  --hf
```

---

## Pipeline Từng Bước

### Chạy từng bước một

```bash
# Bước 1: Collect
python -m finetune.main collect --source data/raw/unlabeled/extract_1k.csv

# Bước 2: Label
python -m finetune.main label

# Bước 3: Build
python -m finetune.main build --version v1.0

# Bước 4: Train
python -m finetune.main train --version v1.0

# Bước 5: Evaluate
python -m finetune.main evaluate --version v1.0

# Bước 6: Decide
python -m finetune.main decide
```

### Chạy Full Pipeline

```bash
# Đơn giản
python -m finetune.main pipeline --version v1.0

# Với MLflow
python -m finetune.main pipeline --version v1.0 --enable-mlflow

# Với Observability
python -m finetune.main pipeline --version v1.0 --enable-observability
```

---

## Xem Data và Kết Quả

### Xem Data Labels

```bash
# Xem 10 samples đầu tiên
head -10 data/labeled/agreed/approved.jsonl

# Đếm số lượng theo label
python -c "
import json
with open('data/labeled/agreed/approved.jsonl') as f:
    labels = {}
    for line in f:
        d = json.loads(line)
        label = d.get('agreed_label', 'unknown')
        labels[label] = labels.get(label, 0) + 1
    print('Label Distribution:')
    for k, v in sorted(labels.items(), key=lambda x: -x[1]):
        print(f'  {k:15} {v:4}')
"
```

### Xem Evaluation Results

```bash
# Xem metrics
cat data/artifacts/latest/eval_result.json | python -m json.tool

# Xem report
cat data/artifacts/latest/eval_report.md
```

### Xem trong MLflow

```bash
# Mở browser
open http://localhost:5010
```

### Xem trong Argilla

```bash
# Mở browser
open http://localhost:6900
# Login: admin / adminpassword
```

---

## Monitoring & Alerts

### Drift Monitoring

```bash
# Lưu baseline trước
python -c "
from finetune.infrastructure.monitoring.baseline_store import BaselineStore
store = BaselineStore()
store.save_eval_result_as_baseline('v1.0', 'data/artifacts/latest/eval_result.json')
print('Baseline saved!')
"

# Monitor drift
python -m finetune.main monitor-drift --baseline-version v1.0 --alert
```

### Check Logs

```bash
# Pipeline logs
tail -f logs/pipeline.log

# Docker logs
docker compose -f docker-compose-infra.yml logs -f argilla
docker compose -f docker-compose-infra.yml logs -f mlflow
```

---

## Troubleshooting

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách fix |
|------|-------------|----------|
| CUDA out of memory | GPU không đủ | Giảm batch_size trong config |
| API key error | OpenAI key không đúng | Kiểm tra .env |
| Dataset not found | Chưa chạy build | Chạy `python -m finetune.main build` |
| Model not found | Training thất bại | Kiểm tra logs/ |

### Xem lỗi

```bash
# Xem full logs
cat logs/pipeline.log

# Xem lỗi gần nhất
grep -i error logs/pipeline.log | tail -20
```

---

## Commands Tổng hợp

```bash
# Full pipeline với tất cả features
python -m finetune.main pipeline \
  --version v1.0 \
  --enable-mlflow \
  --enable-observability

# Chỉ train lại (data đã có)
python -m finetune.main train --version v1.0

# Chỉ evaluate lại
python -m finetune.main evaluate --version v1.0

# Monitor drift
python -m finetune.main monitor-drift

# Deploy canary
python -m finetune.main canary-deploy --version v1.0 --traffic 10
```

---

## Next Steps

Sau khi pipeline chạy thành công:

1. **Thu thập thêm data** - Để cải thiện accuracy
2. **Review trong Argilla** - Label thủ công các samples khó
3. **Push lên HuggingFace** - Chia sẻ model
4. **Setup GitHub Actions** - Tự động hóa pipeline

---

*Last updated: 2026-03-08*
