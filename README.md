# 🎓 Emotion Continuous Training Pipeline

**Pika Robot** - Hệ thống training model phân loại cảm xúc cho robot giáo dục trẻ em.

---

## 📖 Tổng Quan (Non-Technical)

### 🤖 Pika Robot là gì?
Pika Robot là robot giáo dục thông minh cho trẻ em. Robot này cần nhận biết và phản hồi với **13 loại cảm xúc** khác nhau:

| STT | Cảm xúc | Mô tả |
|-----|----------|--------|
| 1 | happy | Vui, hào hứng, chơi đùa |
| 2 | achievement | Tự hào, khích lệ, ăn mừng |
| 3 | thinking | Suy nghĩ, tò mò |
| 4 | calm | Bình tĩnh, nghỉ ngơi |
| 5 | sad | Buồn |
| 6 | worried | Lo lắng |
| 7 | angry | Tức giận |
| 8 | surprised | Ngạc nhiên |
| 9 | sending_heart | Gửi trái tim |
| 10 | sun_glassed | Đeo kính râm |
| 11 | dizzy | Chóng mặt |
| 12 | sobbing | Khóc |
| 13 | superhero | Siêu nhân |

### 🔄 Pipeline Hoạt Động Như Thế Nào?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EMOTION CT PIPELINE FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
     │  1.      │     │  2.      │     │  3.      │     │  4.      │
     │ COLLECT  │────▶│  LABEL   │────▶│  BUILD   │────▶│  TRAIN   │
     │          │     │          │     │          │     │          │
     │ CSV Data │     │ AI gán   │     │ Chia     │     │ Fine-tune│
     │          │     │ nhãn     │     │ train/   │     │ LoRA     │
     └──────────┘     └──────────┘     │ val/test │     └──────────┘
          │                │            └──────────┘           │
          ▼                ▼                 │                  ▼
     data/raw/     data/labeled/    data/datasets/    data/artifacts/
                                                     (Model đã train)

     ┌──────────┐     ┌──────────┐
     │  5.      │     │  6.      │
     │EVALUATE  │────▶│  DECIDE  │
     │          │     │          │
     │ Đo       │     │ Quyết    │
     │ accuracy │     │ định    │
     │ F1 score │     │ promote  │
     └──────────┘     │ /reject  │
                      └──────────┘
```

### 📝 Chi Tiết Từng Bước

| Bước | Tên | Mô Tả |
|-------|-----|--------|
| 1 | **Collect** | Lấy data từ Datadog (CSV) |
| 2 | **Label** | AI (GPT-4o-mini) gán nhãn cảm xúc |
| 3 | **Build** | Chia data: 70% train, 15% val, 15% test |
| 4 | **Train** | Fine-tune model Qwen2.5-1.5B với LoRA |
| 5 | **Evaluate** | Đo lường: accuracy, F1 score |
| 6 | **Decide** | Quyết định có promote model không |

---

## 🛠️ Công Nghệ Sử Dụng

| Công Nghệ | Mục Đích | Link |
|-----------|----------|------|
| **Qwen2.5-1.5B** | Base model LLM | [HuggingFace](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) |
| **LoRA** | Fine-tuning hiệu quả (chỉ train 0.28% params) | [Paper](https://arxiv.org/abs/2106.09685) |
| **Transformers** | HuggingFace ML library | [Docs](https://huggingface.co/docs/transformers) |
| **PEFT** | Parameter-Efficient Fine-Tuning | [GitHub](https://github.com/huggingface/peft) |
| **GPT-4o-mini** | AI gán nhãn cảm xúc | [OpenAI](https://openai.com/index/gpt-4o-mini/) |
| **scikit-learn** | Đánh giá model (accuracy, F1, confusion matrix) | [Docs](https://scikit-learn.org/) |
| **PyTorch** | Deep learning framework | [Website](https://pytorch.org/) |
| **Clean Architecture** | Code structure (Domain → Application → Infrastructure) | |

---

## 🚀 Quick Start

### Yêu Cầu
- Python 3.11+
- GPU với CUDA (tối thiểu 16GB VRAM)
- API Key: OpenAI, HuggingFace

### Cài Đặt

```bash
# Clone repo
git clone https://github.com/DoanNgocCuong/continuous-training-pipeline_T3_2026.git
cd continuous-training-pipeline_T3_2026

# Tạo virtual environment
uv venv .venv
source .venv/bin/activate

# Cài đặt dependencies
pip install torch transformers peft datasets accelerate scikit-learn

# Set API key
export OPENAI_API_KEY="sk-..."
export HF_TOKEN="hf-..."
```

### Chạy Pipeline

```bash
# 1. Collect - Lấy data từ CSV
python -m finetune.main collect --source data/raw/extract.csv

# 2. Label - AI gán nhãn
python -m finetune.main label

# 3. Build - Chia train/val/test
python -m finetune.main build --version v1.0

# 4. Train - Fine-tune model
python scripts/train_simple.py

# 5. Evaluate - Đánh giá
python -m finetune.main evaluate --version v1.0

# 6. Decide - Quyết định promote
python -m finetune.main decide
```

---

## 📁 Cấu Trúc Project

```
continuous-training-pipeline/
├── finetune/                  # Main application code
│   ├── domain/               # Business logic (entities, services)
│   ├── application/          # Use cases
│   └── infrastructure/       # Implementations (training, evaluation)
├── configs/                   # YAML configuration files
├── data/                     # Data directories
│   ├── raw/                  # Raw CSV data
│   ├── labeled/              # Labeled samples
│   └── datasets/             # Train/val/test splits
├── scripts/                   # Utility scripts
├── docs/                     # Documentation (PRD, HLD, LLD, Plan)
├── tests/                     # Unit tests
├── CLAUDE.md                  # AI agent instructions
└── README.md                  # This file
```

---

## 📊 Kết Quả Demo (với 1000 samples)

### Training
- **Model**: Qwen2.5-1.5B-Instruct + LoRA
- **Epochs**: 3
- **Train samples**: 697
- **Training time**: ~3.5 phút
- **Final loss**: 0.092
- **Trainable parameters**: 4.3M / 1.5B (0.28%)

### Evaluation
- **Accuracy**: 35.7%
- **F1 Macro**: 27.8%

### Per-Class F1
| Class | F1 Score |
|-------|-----------|
| sad | 50.0% |
| thinking | 45.8% |
| calm | 44.4% |
| worried | 42.9% |
| surprised | 25.0% |
| happy | 14.1% |
| achievement | 0% |
| angry | 0% |

### Chi Phí
- **Labeling**: ~$0.01 / 1000 samples (GPT-4o-mini)

> **Note**: Accuracy thấp do dataset nhỏ (697 train samples). Với 100K samples sẽ tốt hơn nhiều.

---

## 📚 Tài Liệu Chi Tiết

| File | Mô Tả |
|------|--------|
| [docs/PRD.md](docs/PRD.md) | Product Requirements - Bài toán, mục tiêu |
| [docs/HLD.md](docs/HLD.md) | High-Level Design - Kiến trúc hệ thống |
| [docs/LLD.md](docs/LLD.md) | Low-Level Design - Thiết kế chi tiết |
| [docs/Plan.md](docs/Plan.md) | Project Plan - Kế hoạch, tiến độ |
| [CLAUDE.md](CLAUDE.md) | AI Agent Instructions - Hướng dẫn cho Claude |

---

## 🔗 Links

- **GitHub**: https://github.com/DoanNgocCuong/continuous-training-pipeline_T3_2026
- **Model**: Qwen2.5-1.5B-Instruct
- **HuggingFace**: (sẽ push sau khi promote)

---

*Last updated: 2026-03-06*
