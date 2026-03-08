# PRD: Emotion Model Continuous Training Pipeline

**Version**: 1.0
**Created**: 2026-03-02
**Author**: AI Engineering Team
**Status**: Draft

---

## 1. Problem Statement

### SCQA Framework

| Element | Description |
|---------|-------------|
| **Situation** | Emotion classification API đang production với Qwen2.5-1.5B-Instruct-AWQ, serving ~53K+ requests. Model base chưa fine-tune, dùng prompt engineering thuần. |
| **Complication** | Model không cải thiện theo thời gian. Không có ground truth data. Không có cơ chế đánh giá chất lượng. Khi ngôn ngữ user thay đổi (slang mới, pattern mới), model không adapt được. |
| **Question** | Làm sao xây pipeline tự động: thu thập data → gán nhãn → fine-tune → đánh giá → quyết định deploy — để model liên tục cải thiện mà không cần can thiệp thủ công? |
| **Answer** | Xây Continuous Training (CT) Pipeline với 5 steps tự động, sử dụng Distilabel + Argilla (labeling), Unsloth (training), sklearn (eval), MLflow (registry). |

### Business Context

- **Product**: Pika Robot — robot giáo dục cho trẻ em
- **Emotion API**: Phân loại cảm xúc từ text → 8 nhóm emotion → robot thể hiện animation tương ứng
- **Current model**: Qwen2.5-1.5B-Instruct-AWQ (base, chưa fine-tune)
- **Serving repo**: VeryFastMoodEmotionClassification_T12_2025

---

## 2. Goals & Non-Goals

### Goals

| # | Goal | Measurable |
|---|------|------------|
| G1 | Xây pipeline thu thập + gán nhãn data tự động | ≥500 labeled samples/tuần |
| G2 | Fine-tune model Qwen2.5-1.5B với LoRA | Model fine-tuned chạy được trên vLLM |
| G3 | Đánh giá model mới so với model cũ tự động | Eval suite chạy ≤5 phút, có report |
| G4 | Quyết định promote/reject dựa trên metrics | Auto-decide với configurable thresholds |
| G5 | Publish model artifact lên registry | Model mới available cho serving repo |

### Non-Goals (Phase 1)

- Auto-deploy lên production (vẫn cần human approve deploy)
- Canary deployment
- Real-time monitoring + drift detection
- ZenML orchestration (dùng scripts + cron)
- Online learning / incremental training

---

## 3. Emotion Classification Spec

### 8 Emotion Groups (production)

| # | Group | Variants | Animation |
|---|-------|----------|-----------|
| 1 | happy | happy, happy_2, happy_3, excited, excited_2, playful, playful_2, playful_3 | Vui vẻ |
| 2 | achievement | celebration, encouraging, encouraging_2, thats_right, thats_right_2, proud, proud_2 | Chúc mừng |
| 3 | thinking | thinking, curious | Suy nghĩ |
| 4 | calm | calm, idle, idle_2, no_problem | Bình thường |
| 5 | sad | sad | Buồn |
| 6 | worried | worry, afraid | Lo lắng |
| 7 | angry | angry, noisy | Tức giận |
| 8 | surprised | surprised | Ngạc nhiên |

### Input Format (from production)

```
Previous Pika Robot's Response: {previous_response}
Now Pika Robot's Response need check: {current_response}
```

Model phải classify emotion của `current_response` trong context `previous_response`.

---

## 4. Pipeline Overview (5 Steps)

```
Step 1          Step 2           Step 2.5         Step 3          Step 4          Step 5
DATA        →   LABEL         →  BUILD         →  TRAIN        →  EVAL         →  DECIDE
COLLECT         + AGREEMENT      DATASETS         (Unsloth)       (Metrics)       + PUBLISH

Datadog/        Distilabel       train.jsonl      LoRA adapter    F1, Accuracy    Promote?
Langfuse        + Argilla        val.jsonl        + metadata      Confusion       → HF Hub
→ raw CSV       + 3-way logic    test.jsonl                       Regression      → MLflow
                                 regression/
                                 golden/
```

---

## 5. User Stories

### P0 — Must Have (Phase 1)

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-01 | ML Engineer | Load raw CSV data (từ Datadog export) vào pipeline | Có starting point để label |
| US-02 | ML Engineer | Chạy AI labeling tự động (GPT-4o-mini) | Không phải gán nhãn tay 53K samples |
| US-03 | ML Engineer | Xem và review AI labels qua UI (Argilla) | Validate chất lượng labels |
| US-04 | ML Engineer | Chạy 3-way agreement check | Biết labels nào đáng tin, labels nào cần review |
| US-05 | ML Engineer | Split data thành train/val/test sets | Data không bị leak giữa train và eval |
| US-06 | ML Engineer | Fine-tune Qwen2.5-1.5B bằng Unsloth LoRA | Có model candidate mới |
| US-07 | ML Engineer | Eval model mới vs model cũ bằng metrics | Biết model mới tốt hơn hay không |
| US-08 | ML Engineer | Xem eval report (F1, accuracy, confusion matrix) | Ra quyết định promote có evidence |
| US-09 | ML Engineer | Push model artifact lên HuggingFace Hub | Serving repo có thể pull model mới |
| US-10 | ML Engineer | Chạy toàn bộ pipeline bằng 1 command | Không phải chạy từng step thủ công |

### P1 — Should Have (Phase 2)

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-11 | ML Engineer | Extract data trực tiếp từ Langfuse API | Không cần export CSV thủ công |
| US-12 | ML Engineer | Tích lũy regression test set | Model mới không quên edge cases đã fix |
| US-13 | ML Engineer | Human-curated golden test set | Có source of truth đáng tin cậy |
| US-14 | ML Engineer | Auto-decide promote/reject dựa trên rules | Giảm human decision fatigue |

### P2 — Could Have (Phase 3)

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-15 | ML Engineer | Schedule pipeline chạy tự động (cron/weekly) | Pipeline tự xoay |
| US-16 | ML Engineer | Monitor model performance drift | Biết khi nào cần retrain |
| US-17 | ML Engineer | Canary deploy model mới | Giảm risk khi deploy |

---

## 6. Success Metrics

| Metric | Current (baseline) | Target (Phase 1) | Target (Phase 2) |
|--------|--------------------|-------------------|-------------------|
| Emotion accuracy (benchmark) | Chưa đo | Đo được, baseline set | +5% so với baseline |
| F1 macro (benchmark) | Chưa đo | Đo được, baseline set | +3% so với baseline |
| Labeled samples | 0 | ≥2000 | ≥10000 |
| Pipeline runtime (full) | N/A | ≤4 giờ (train included) | ≤2 giờ |
| Eval suite runtime | N/A | ≤5 phút | ≤5 phút |
| Model versions tracked | 0 | ≥3 | ≥10 |

---

## 7. Constraints & Assumptions

### Constraints

- GPU: 1x NVIDIA GPU (shared với serving, hoặc separate nếu có)
- Budget: AI labeling (GPT-4o-mini) ~$1-5/tuần cho 5000 samples
- Team: 1 ML Engineer (solo operation)
- Infra: On-prem server, Docker-based

### Assumptions

- CSV data từ Datadog đã có sẵn (đã export ~53K rows)
- Base model: luôn fine-tune từ Qwen2.5-1.5B-Instruct (không incremental)
- Serving repo sẽ pull model từ HuggingFace Hub hoặc local NFS
- Emotion groups (8 nhóm) ít khi thay đổi

---

## 8. Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| AI labeling quality thấp | Garbage training data | Medium | 3-way agreement + human review |
| Catastrophic forgetting | Model mới tệ hơn cũ | Low | Luôn train từ base, eval regression set |
| GPU contention (serving vs training) | Latency spike trên API | Medium | Schedule training off-peak hours |
| Label drift (emotion distribution thay đổi) | Model bias | Medium | Monitor distribution per batch |

---

## 9. Phased Delivery

### Phase 1 (Week 1-2): End-to-end manual

- [US-01] CSV loader
- [US-02] Distilabel AI labeling
- [US-04] 3-way agreement logic
- [US-05] Dataset builder (train/val/test split)
- [US-06] Unsloth training script
- [US-07] Eval metrics (sklearn)
- [US-08] Eval report generator
- [US-10] Full pipeline CLI

### Phase 2 (Week 3-4): Semi-auto

- [US-03] Argilla UI integration
- [US-09] HuggingFace Hub push
- [US-11] Langfuse API extractor
- [US-12] Regression test set
- [US-13] Golden test set
- [US-14] Auto-decide logic

### Phase 3 (Month 2+): Full auto

- [US-15] Scheduled pipeline
- [US-16] Drift monitoring
- [US-17] Canary deployment
- MLflow full integration

---

## 10. Dependencies

### External Services

| Service | Purpose | Required Phase |
|---------|---------|----------------|
| OpenAI API (GPT-4o-mini) | AI labeling | Phase 1 |
| HuggingFace Hub | Model registry + dataset hosting | Phase 2 |
| Argilla (self-hosted) | Human labeling UI | Phase 2 |
| MLflow (self-hosted) | Experiment tracking | Phase 2 |

### Shared with Serving Repo

| Item | How to share |
|------|-------------|
| 8 emotion groups | YAML config file (copy, sync manual) |
| Model artifact | HuggingFace Hub (or local NFS path) |

---

## Appendix: Glossary

| Term | Definition |
|------|-----------|
| CT Pipeline | Continuous Training Pipeline — tự động retrain model khi có data mới |
| LoRA | Low-Rank Adaptation — fine-tune hiệu quả, chỉ train adapter nhỏ |
| AWQ | Activation-aware Weight Quantization — giảm model size cho inference |
| Ground truth | Label chính xác (do human xác nhận) |
| Regression test | Test set tích lũy edge cases đã fix, đảm bảo model mới không quên |
| Golden test | Test set human-curated, source of truth cho evaluation |
| 3-way agreement | Logic so sánh 3 nguồn: AI label, Human label, Model output |
