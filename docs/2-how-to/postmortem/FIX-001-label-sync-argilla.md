# Fix: Label Sync và Argilla UI Labels

**Ngày**: 2026-03-08
**Người thực hiện**: Claude
**Trạng thái**: ✅ Completed

## Vấn đề

1. **Không nhất quán số labels**:
   - Distilabel config: 8 labels
   - Argilla config: 13 labels
   - Domain: 5 labels

2. **Argilla UI không hiển thị labels cho bộ 5K**:
   - Khi push prelabeled data lên Argilla, labels được set vào `metadata` nhưng không hiển thị trong UI distribution
   - Labels chỉ nằm trong file local `prelabeled.xlsx`, không được push đúng cách

## Giải pháp

### 1. Đồng bộ về 5 labels

Quyết định: Dùng 5 labels (happy, achievement, thinking, calm, surprised) - phù hợp với business context của Pika Robot.

**Files đã update:**
- `configs/emotions.yml` - 5 emotion groups
- `configs/labeling/distilabel_pipeline.yml` - 5 valid labels
- `configs/labeling/argilla_config.yml` - 5 labels
- `finetune/domain/value_objects.py` - EmotionLabel enum
- `finetune/infrastructure/data_sources/argilla_reviewer.py`
- `finetune/infrastructure/data_sources/openai_labeler.py`
- `finetune/infrastructure/evaluation/sklearn_evaluator.py`
- `finetune/infrastructure/repositories/file_dataset_repository.py`
- `finetune/infrastructure/registry/model_card_generator.py`

### 2. Fix Argilla labels hiển thị đúng

**Before:**
```python
# Labels chỉ set vào metadata, không set vào suggestions
metadata["ai_label"] = s.ai_label.value
```

**After:**
```python
# Ưu tiên human_label (prelabeled), rồi mới đến ai_label
if s.human_label and s.human_label != EmotionLabel.UNKNOWN:
    metadata["human_label"] = s.human_label.value
    suggestions.append(
        rg.Suggestion(
            question_name="emotion_label",
            value=s.human_label.value,
            agent="human",
            score=1.0,
        )
    )
elif s.ai_label and s.ai_label != EmotionLabel.UNKNOWN:
    metadata["ai_label"] = s.ai_label.value
    suggestions.append(...)
```

**Thêm metadata property:**
```python
rg.TermsMetadataProperty(name="human_label"),
```

## Kết quả

- ✅ Labels hiển thị đúng trên Argilla UI
- ✅ Bộ 5K (prelabeled.xlsx) push lên Argilla với 5000 samples, labels distribution đúng
- ✅ Code nhất quán giữa các components

## Data sau fix

| Dataset | Records | Labels |
|---------|---------|--------|
| emotion-audit | 5000 | happy:1000, achievement:1000, thinking:1000, calm:1000, surprised:1000 |
| emotion-review | 1000 | thinking:536, happy:235, calm:135, achievement:61, surprised:33 |

## Lessons Learned

1. **Best practice**: Set labels as Argilla `Suggestion` để hiển thị trong UI
2. **Metadata property**: Cần khai báo metadata properties trong dataset settings trước khi push data
3. **Pre-labeled data**: Nên set `agent="human"`, `score=1.0` để phân biệt với AI labels
