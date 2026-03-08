# High-Level Design: Continuous Training Pipeline — PIKA Emotion

**Project:** PIKA Emotion Classification (8 emotions)
**Model:** Qwen2.5-1.5B-Instruct → Fine-tuned → AWQ 4-bit → vLLM Serving
**Target:** MLOps Level 1 (Automated CT Pipeline)
**Version:** 2.0 — Date: 2026-03-03

---

## 1. Tổng quan Pipeline

### 1.1. Bức tranh toàn cục — Data Flywheel

Pipeline hoạt động như một **vòng lặp khép kín (closed-loop)**, trong đó model production liên tục tạo ra data → data được label → train model mới → eval → deploy → lặp lại.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FLYWHEEL                                │
│                                                                     │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │ SERVING  │───▶│ LOGGING  │───▶│ LABELING │───▶│ TRAINING │     │
│   │ (vLLM)   │    │(Langfuse)│    │(AI+Human)│    │(Unsloth) │     │
│   └────▲─────┘    └──────────┘    └──────────┘    └────┬─────┘     │
│        │                                               │           │
│        │          ┌──────────┐    ┌──────────┐         │           │
│        └──────────│  DEPLOY  │◀───│   EVAL   │◀────────┘           │
│                   │(AWQ+vLLM)│    │ (Gate)   │                     │
│                   └──────────┘    └──────────┘                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2. Hai hệ thống tách biệt

```
┌─────────────────────────────┐          ┌─────────────────────────────┐
│   SERVING SYSTEM            │          │   TRAINING SYSTEM           │
│   Repo: VeryFastMoodEmotion │          │   Repo: EmotionFinetune     │
│                             │          │                             │
│   • FastAPI :30030          │  ◀─HF──  │   • Data Ingestion          │
│   • vLLM :30029             │  Hub──▶  │   • Labeling (AI + Human)   │
│   • Langfuse tracing        │          │   • Dataset Construction    │
│   • Datadog APM             │          │   • Training (Unsloth)      │
│                             │          │   • Evaluation & Promotion  │
│   GPU #1: Inference         │          │   • MLflow Server           │
│                             │          │   • Argilla Server          │
│                             │          │                             │
│   Nhiệm vụ: SERVE ONLY     │          │   Nhiệm vụ: TRAIN + EVAL   │
└─────────────────────────────┘          └─────────────────────────────┘
                │                                       ▲
                │         ┌───────────────┐             │
                └────────▶│  HuggingFace  │─────────────┘
                  logs     │  Model Hub    │   pull model
                           │  (AWQ 4-bit)  │
                           └───────────────┘
```

**Tại sao tách?**
- Serving system cần **ổn định**, không bị ảnh hưởng bởi training
- Training system cần **GPU riêng**, chạy batch, có thể fail mà không ảnh hưởng production
- Model Registry (HF Hub + MLflow) là **contract** duy nhất giữa 2 hệ thống

---

## 2. Luồng Pipeline Chi tiết (Stage 0 → 6)

```
                    ┌─────────────────────────────────────────┐
                    │         PRODUCTION (đang chạy)          │
                    │                                         │
  User (trẻ 6-12)  │  PIKA Robot ──▶ FastAPI ──▶ vLLM        │
  nói tiếng Anh    │                    │      (Qwen2.5-AWQ) │
                    │                    ▼                    │
                    │              Langfuse / Datadog          │
                    └────────────────┬────────────────────────┘
                                     │
                         ┌───────────▼───────────┐
                         │  STAGE 0: LOGGING     │
                         │  user_input,          │
                         │  model_output,         │
                         │  confidence_score,     │
                         │  latency_ms            │
                         └───────────┬───────────┘
                                     │
          ┌──────────────────────────▼──────────────────────────┐
          │              TRAINING PIPELINE (EmotionFinetune)     │
          │                                                     │
          │  ┌─────────────────────────────────────────────┐    │
          │  │  STAGE 1: DATA INGESTION                    │    │
          │  │  collect_data.py                             │    │
          │  │  Langfuse API / Datadog CSV → Clean → Dedup  │    │
          │  │  Output: data/raw/{date}_raw.jsonl           │    │
          │  └─────────────────────┬───────────────────────┘    │
          │                        │                            │
          │  ┌─────────────────────▼───────────────────────┐    │
          │  │  STAGE 2: CURATION & LABELING               │    │
          │  │  label_data.py                               │    │
          │  │                                             │    │
          │  │  ┌──────────────────┐                       │    │
          │  │  │ Distilabel       │ GPT-4o-mini           │    │
          │  │  │ AI Labeling      │ → emotion + reasoning  │    │
          │  │  └────────┬─────────┘                       │    │
          │  │           ▼                                 │    │
          │  │  ┌──────────────────┐                       │    │
          │  │  │ 3-Way Agreement  │                       │    │
          │  │  │ Production vs AI │──▶ ≥2/3 agree?       │    │
          │  │  │ vs User Feedback │       │               │    │
          │  │  └──────────────────┘       │               │    │
          │  │                        YES  │  NO           │    │
          │  │                        ▼    │  ▼            │    │
          │  │               AUTO_APPROVED │  FLAGGED      │    │
          │  │                             │  → ARGILLA UI │    │
          │  │                             ▼       ▼       │    │
          │  │                    data/labeled/*.jsonl      │    │
          │  └─────────────────────┬───────────────────────┘    │
          │                        │                            │
          │  ┌─────────────────────▼───────────────────────┐    │
          │  │  STAGE 3: DATASET CONSTRUCTION              │    │
          │  │  build_datasets.py                           │    │
          │  │  Stratified split → 70/15/15                │    │
          │  │  Format ChatML (Qwen2.5)                    │    │
          │  │  + regression_test + golden_test             │    │
          │  │  Output: data/datasets/v1.1.0/              │    │
          │  └─────────────────────┬───────────────────────┘    │
          │                        │                            │
          │  ┌─────────────────────▼───────────────────────┐    │
          │  │  STAGE 4: MODEL TRAINING                    │    │
          │  │  run_training.py                             │    │
          │  │  LUÔN từ BASE MODEL GỐC                     │    │
          │  │  Qwen/Qwen2.5-1.5B-Instruct                │    │
          │  │  Unsloth + QLoRA (r=16, 7 modules)          │    │
          │  │  → LoRA Adapter + MLflow log                │    │
          │  └─────────────────────┬───────────────────────┘    │
          │                        │                            │
          │  ┌─────────────────────▼───────────────────────┐    │
          │  │  STAGE 5: EVALUATION & PROMOTION GATE       │    │
          │  │  run_evaluation.py + decide_promotion.py     │    │
          │  │                                             │    │
          │  │  Candidate vs Baseline on 3 test sets:      │    │
          │  │  • Benchmark (accuracy, F1-macro, F1/class) │    │
          │  │  • Regression (100% pass required)          │    │
          │  │  • Golden (expert-curated)                   │    │
          │  │                                             │    │
          │  │  Promotion rules:                           │    │
          │  │  • accuracy  ≥ +0.5%                        │    │
          │  │  • f1_macro  ≥ +0.3%                        │    │
          │  │  • per_class drop ≤ 2%                      │    │
          │  │  • regression = 100%                        │    │
          │  │  • p95 latency < 100ms                      │    │
          │  │                                             │    │
          │  │  ALL PASS → MLflow "Staging"                │    │
          │  │  ANY FAIL → Log reason, giữ model cũ       │    │
          │  └───────────┬────────────────────────────────┘    │
          │              │                                      │
          │  ┌───────────▼────────────────────────────────┐    │
          │  │  STAGE 6: DEPLOY & CLOSE LOOP              │    │
          │  │  publish_model.py                            │    │
          │  │                                             │    │
          │  │  ★ HUMAN APPROVE ★                         │    │
          │  │  1. Merge LoRA vào base                     │    │
          │  │  2. AutoAWQ Quantize → 4-bit                │    │
          │  │  3. Push HF Hub                             │    │
          │  │  4. CI/CD → restart vLLM                    │    │
          │  └─────────────────────────────────────────────┘    │
          └─────────────────────────────────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │  Model mới live trên vLLM       │
                    │  → thu data mới → REPEAT        │
                    └────────────────────────────────┘
```

---

## 3. Chi tiết từng Stage

### Stage 0: Logging & Monitoring (ĐÃ CÓ trong Serving Repo)

| Thành phần   | Vai trò                                            |
| :----------- | :------------------------------------------------- |
| **Langfuse** | Trace: input, prompt, output, latency, token count |
| **Datadog**  | APM: p50/p95 latency, error rate, GPU utilization  |

**Trigger conditions sang Stage 1:**
- **Schedule:** Weekly (mỗi thứ 2)
- **Data threshold:** Tích lũy ≥ 500 samples mới
- **Drift alert:** Confidence mean drop > 5%
- **Manual:** ML Engineer kick pipeline

### Stage 1: Data Ingestion — `finetune/application/usecases/collect_data.py`

**Input:** Langfuse API / Datadog CSV
**Output:** `data/raw/{date}_raw.jsonl`

Xử lý: Remove system prefix, dedup (user_input + session_id), normalize, filter (3-500 words).

### Stage 2: Curation & Labeling — `finetune/application/usecases/label_data.py`

**8 Emotion Labels:**

| #    | Emotion     | Animation   | Ví dụ                  |
| :--- | :---------- | :---------- | :--------------------- |
| 1    | happy       | Vui vẻ      | "Yay I got it right!"  |
| 2    | achievement | Chúc mừng   | "Cậu giỏi quá!"        |
| 3    | thinking    | Suy nghĩ    | "How do you say that?" |
| 4    | calm        | Bình thường | "OK" / "Next"          |
| 5    | sad         | Buồn        | "I'm not good at this" |
| 6    | worried     | Lo lắng     | "I'm scared to try"    |
| 7    | angry       | Tức giận    | "I hate this!"         |
| 8    | surprised   | Ngạc nhiên  | "Wow really?!"         |

**3-Way Agreement:**
- AI == Human == Model → AUTO_APPROVED
- AI == Human != Model → AUTO_APPROVED (valuable training data)
- AI == Model != Human → HUMAN_RESOLVED (trust human)
- AI != Human → FLAGGED → Argilla review
- No human + AI == Model → AUTO_APPROVED (low confidence)
- No human + AI != Model → PENDING

### Stage 3: Dataset Construction — `finetune/application/usecases/build_datasets.py`

```
data/datasets/v1.1.0/
├── train.jsonl           # 70%
├── val.jsonl             # 15%
├── test.jsonl            # 15% (benchmark)
├── regression_test.jsonl # Edge cases (CHỈ TĂNG)
└── golden_test.jsonl     # Expert-curated
```

Format: ChatML (Qwen2.5 compatible).

### Stage 4: Model Training — `finetune/application/usecases/run_training.py`

**Nguyên tắc: LUÔN train từ base model gốc** (Qwen/Qwen2.5-1.5B-Instruct).

Training config:
- QLoRA: r=16, alpha=32, 7 target modules
- Epochs: 3, LR: 2e-4, cosine scheduler
- VRAM: ~6-8 GB (Unsloth optimization)
- MLflow: log params, loss curves, adapter weights

### Stage 5: Evaluation & Promotion Gate

Candidate vs Baseline trên 3 test sets. Promotion rules (ALL phải pass):

| Rule                 | Threshold |
| :------------------- | :-------- |
| Accuracy improvement | ≥ +0.5%   |
| F1-macro improvement | ≥ +0.3%   |
| Per-class F1 drop    | ≤ 2.0%    |
| Regression pass rate | = 100%    |
| p95 latency          | < 100ms   |

### Stage 6: Deploy & Close Loop

MLflow "Staging" → **Human approve** → Merge LoRA → AutoAWQ 4-bit → Push HF Hub → CI/CD restart vLLM.

---

## 4. Infrastructure Stack

### 4.1. Serving System (giữ nguyên)

| Component | Config                     |
| :-------- | :------------------------- |
| vLLM      | v0.6.6, GPU #1, port 30029 |
| FastAPI   | emotion-api, port 30030    |
| Langfuse  | Trace publishing           |
| Datadog   | APM agent                  |

### 4.2. Training System (docker-compose-infra.yml)

```
┌─────────────────────────────────────────────────────────────────┐
│  HOST MACHINE                                                    │
│  python -m finetune pipeline                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DistilabelLabeler ──── HTTP ──────► OpenAI API          │  │
│  │  ArgillaReviewer ──────── HTTP ──┐                       │  │
│  │  MLflowRegistry ──────── HTTP ──┤ → Docker services      │  │
│  │  UnslothTrainer (local GPU)      │   (localhost)          │  │
│  └──────────────────────────────────┼───────────────────────┘  │
└─────────────────────────────────────┼───────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────┐
│  DOCKER (docker-compose-infra.yml)                                │
│  ct-argilla      :6900  ← Human review UI                        │
│  ct-mlflow       :5000  ← Experiment tracking + Registry          │
│  ct-minio        :9000  ← MLflow artifact storage (S3)           │
│  ct-postgres     :5432  ← Argilla + MLflow metadata              │
│  ct-elasticsearch:9200  ← Argilla search backend                  │
│  ct-argilla-redis:6379    ← Argilla job queue                      │
└──────────────────────────────────────────────────────────────────┘
```

### 4.3. Repo Structure

```
EmotionFinetune/
├── finetune/                         # Main package
│   ├── domain/                       # Pure business logic
│   │   ├── entities.py
│   │   ├── value_objects.py          # 8 EmotionLabel enum
│   │   ├── exceptions.py
│   │   └── services/
│   │       ├── label_agreement.py    # 3-way agreement
│   │       ├── dataset_builder.py    # Stratified split
│   │       └── promotion_decider.py  # Promotion rules
│   │
│   ├── application/                  # Use case orchestration
│   │   ├── usecases/
│   │   │   ├── collect_data.py       # Stage 1
│   │   │   ├── label_data.py         # Stage 2
│   │   │   ├── build_datasets.py     # Stage 3
│   │   │   ├── run_training.py       # Stage 4
│   │   │   ├── run_evaluation.py     # Stage 5
│   │   │   ├── decide_promotion.py   # Stage 5b
│   │   │   └── publish_model.py      # Stage 6
│   │   └── repositories/            # Abstract interfaces (ABC)
│   │
│   ├── infrastructure/               # Concrete implementations
│   │   ├── data_sources/
│   │   │   ├── csv_loader.py
│   │   │   ├── distilabel_labeler.py
│   │   │   └── argilla_reviewer.py
│   │   ├── training/
│   │   │   ├── unsloth_trainer.py
│   │   │   └── config_loader.py
│   │   ├── evaluation/
│   │   │   ├── sklearn_evaluator.py
│   │   │   └── report_generator.py
│   │   ├── registry/
│   │   │   ├── mlflow_registry.py
│   │   │   └── huggingface_publisher.py
│   │   └── packaging/
│   │       └── awq_quantizer.py
│   │
│   └── main.py                       # CLI (Typer)
│
├── configs/
│   ├── emotions.yml                  # 8 emotion groups
│   ├── training/qwen2.5_1.5b_lora.yml
│   ├── evaluation/promotion_rules.yml
│   └── labeling/
│
├── data/
│   ├── raw/                          # Stage 1 output
│   ├── labeled/                      # Stage 2 output
│   ├── datasets/                     # Stage 3 output
│   └── artifacts/                    # Stage 4 output
│
├── docker-compose-infra.yml          # MLflow + Argilla
├── docker/                           # Dockerfiles
├── tests/
├── scripts/
└── docs/
```

---

## 5. Lộ trình Triển khai (Rollout)

```
Tuần 1─2          Tuần 3─4          Tuần 5─6          Tuần 7─8
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ PHASE 1  │      │ PHASE 2  │      │ PHASE 3  │      │ PHASE 4  │
│ Nền tảng │─────▶│ Eval &   │─────▶│ Data     │─────▶│ Auto     │
│ Pipeline │      │ MLflow   │      │ Flywheel │      │ Deploy   │
│          │      │          │      │          │      │          │
│ Stage 1  │      │ Stage 5  │      │ Stage 2  │      │ Stage 6  │
│ Stage 3  │      │ Eval     │      │ AI +     │      │ CI/CD    │
│ Stage 4  │      │ MLflow   │      │ Human    │      │ AWQ      │
│ Train    │      │ Server   │      │ Argilla  │      │ HF Hub   │
│          │      │ Model    │      │ Distilabel│     │ vLLM     │
│ Input:   │      │ Registry │      │ Auto     │      │ restart  │
│ CSV file │      │ Promotion│      │ trigger  │      │          │
│ (manual) │      │ rules    │      │ Langfuse │      │ MLOps    │
│          │      │          │      │          │      │ Level 1  │
│ Model v1 │      │ Gate tự  │      │ Flywheel │      │ đầy đủ   │
│ fine-tuned│     │ động     │      │ hoàn chỉnh│     │          │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
```

---

## 6. Quyết định Thiết kế Quan trọng

| Quyết định                      | Lựa chọn                             | Lý do                                               |
| :------------------------------ | :----------------------------------- | :-------------------------------------------------- |
| Luôn train từ base model gốc    | Qwen2.5-1.5B-Instruct (HF)           | Tránh catastrophic forgetting, reproducibility 100% |
| LoRA thay vì full fine-tune     | r=16, QLoRA 4-bit, 7 modules         | Tiết kiệm VRAM (6-8GB), đủ cho classification       |
| GPT-4o-mini làm teacher labeler | Không dùng model tự label chính mình | Tránh bias reinforcement                            |
| Human-in-the-loop bắt buộc      | Argilla cho FLAGGED samples          | Data quality > data quantity                        |
| Regression test = hard gate     | 100% pass required                   | Không chấp nhận regression                          |
| Human approve trước deploy      | Staging → Production manual          | Safety net, target user là trẻ em                   |
| AWQ quantization                | AutoAWQ 4-bit                        | Compatible với vLLM, giảm VRAM 4x                   |
| 2 repo tách biệt                | Serving vs Training                  | Isolation, lifecycle riêng                          |

---

## 7. Risks & Mitigations

| Risk                      | Impact                       | Mitigation                             |
| :------------------------ | :--------------------------- | :------------------------------------- |
| AI labeling sai           | Model train trên data sai    | 3-way agreement + human review         |
| Catastrophic forgetting   | Model quên language ability  | Luôn train từ base, regression test    |
| Label imbalance           | Model bias towards class lớn | Stratified split + oversample minority |
| Concept drift             | Performance giảm dần         | Monitor confidence + weekly retrain    |
| Deploy model lỗi          | Production downtime          | Human gate + health check + rollback   |
| Data privacy (PII trẻ em) | Legal/compliance risk        | Anonymize, không log PII               |
| GPU contention            | Training block inference     | Tách GPU hoặc off-peak hours           |
