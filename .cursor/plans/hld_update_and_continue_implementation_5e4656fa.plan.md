---
name: HLD update and continue implementation
overview: Update HLD.md with new version, reduce emotion labels from 13 to 8, update training config (7 LoRA modules), adopt Stage 0-6 naming, then continue implementing remaining infrastructure components following pipeline stage order.
todos:
  - id: reduce-labels
    content: Reduce emotion labels from 13 to 8 across all files (value_objects, configs, prompts, tests, docs)
    status: completed
  - id: replace-hld
    content: Replace docs/HLD.md with new version (fix src/ to finetune/, 8 labels, Stage 0-6)
    status: completed
  - id: update-training-config
    content: "Update qwen2.5_1.5b_lora.yml: 7 target_modules + new training params"
    status: completed
  - id: stage-naming
    content: Update main.py docstrings and comments from Step to Stage naming
    status: completed
  - id: implement-unsloth
    content: Implement UnslothTrainer (Unsloth + QLoRA + SFTTrainer) replacing NotImplementedError stub
    status: completed
  - id: implement-report
    content: "Create ReportGenerator: Markdown eval report with confusion matrix, metrics, comparison"
    status: completed
  - id: implement-mlflow
    content: "Create MLflowRegistry: log runs, metrics, artifacts, model stage management"
    status: completed
  - id: implement-hf-publisher
    content: "Create HuggingFacePublisher: push merged+quantized model to HF Hub"
    status: completed
  - id: implement-awq
    content: "Create AWQ Quantizer: merge LoRA into base + AutoAWQ 4-bit quantize"
    status: completed
  - id: wire-cli
    content: Update main.py CLI to integrate new components (MLflow, publish command)
    status: completed
  - id: run-tests
    content: Run all tests, fix any regressions from label/naming changescontinue
    status: in_progress
isProject: false
---

# Update HLD + Sync Code + Continue Infrastructure Implementation

## Context

Project at `/home/ubuntu/cuong_dn/Continuous_Traning_Pipeline/` has initial structure from previous session. Need to: (1) replace HLD, (2) reduce 8 emotion labels, (3) update training config, (4) adopt Stage naming, (5) implement remaining infrastructure stubs.

---

## Part 1: Emotion Labels -- 13 to 8

Remove 5 labels: `sending_heart`, `sun_glassed`, `dizzy`, `sobbing`, `superhero`.
Keep 8: `happy`, `achievement`, `thinking`, `calm`, `sad`, `worried`, `angry`, `surprised`.

**Files to change:**

- `[finetune/domain/value_objects.py](finetune/domain/value_objects.py)` -- Remove 5 enum members from `EmotionLabel`
- `[configs/emotions.yml](configs/emotions.yml)` -- Remove 5 emotion groups
- `[finetune/infrastructure/evaluation/sklearn_evaluator.py](finetune/infrastructure/evaluation/sklearn_evaluator.py)` -- Update `_SYSTEM_PROMPT` to list 8 labels
- `[finetune/infrastructure/data_sources/distilabel_labeler.py](finetune/infrastructure/data_sources/distilabel_labeler.py)` -- Update `_SYSTEM_PROMPT` to list 8 labels
- `[finetune/infrastructure/data_sources/argilla_reviewer.py](finetune/infrastructure/data_sources/argilla_reviewer.py)` -- Update `_EMOTION_LABELS` list
- `[finetune/infrastructure/repositories/file_dataset_repository.py](finetune/infrastructure/repositories/file_dataset_repository.py)` -- Update `_CHATML_SYSTEM`
- `[tests/conftest.py](tests/conftest.py)` -- Update fixtures if they use removed labels
- `[tests/unit/domain/test_value_objects.py](tests/unit/domain/test_value_objects.py)` -- Update test cases
- `[docs/PRD.md](docs/PRD.md)` -- Update "13 Emotion Groups" table to 8

---

## Part 2: Replace HLD.md

Replace `[docs/HLD.md](docs/HLD.md)` with new content from user, with these corrections:

- `src/` references changed to `finetune/`
- 13 emotion labels changed to 8
- Stage 0-6 naming adopted
- Keep infrastructure architecture diagrams accurate to current docker-compose-infra.yml

---

## Part 3: Training Config Update

`[configs/training/qwen2.5_1.5b_lora.yml](configs/training/qwen2.5_1.5b_lora.yml)`:

```yaml
# Before: target_modules: ["q_proj", "k_proj", "v_proj", "o_proj"]
# After:
target_modules: ["q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj", "gate_proj"]
# Keep alpha: 32
```

Also add fields from new HLD: `load_in_4bit`, `lr_scheduler`, `weight_decay`, `eval_strategy`, `eval_steps`, `save_steps`.

---

## Part 4: Stage Naming Update

`[finetune/main.py](finetune/main.py)` -- Update docstrings from "Step X" to "Stage X":

- `collect` = Stage 1, `label` = Stage 2, `build` = Stage 3, `train` = Stage 4, `evaluate` = Stage 5, `decide` = Stage 5, `publish` = Stage 6

CLI command names stay the same (`collect`, `label`, `build`, etc.).

---

## Part 5: Implement Infrastructure -- Pipeline Stage Order

### Stage 1: Data Ingestion (DONE)

- `[csv_loader.py](finetune/infrastructure/data_sources/csv_loader.py)` -- implemented
- `langfuse_extractor.py`, `datadog_extractor.py` -- Phase 2, skip for now

### Stage 2: Labeling (DONE)

- `[distilabel_labeler.py](finetune/infrastructure/data_sources/distilabel_labeler.py)` -- implemented
- `[argilla_reviewer.py](finetune/infrastructure/data_sources/argilla_reviewer.py)` -- implemented

### Stage 3: Dataset Construction (DONE)

- `[file_dataset_repository.py](finetune/infrastructure/repositories/file_dataset_repository.py)` -- implemented (save_samples, save_as_chatml, save_as_eval_jsonl)

### Stage 4: Training (STUB)

- `[unsloth_trainer.py](finetune/infrastructure/training/unsloth_trainer.py)` -- Currently `NotImplementedError`. Implement full Unsloth + QLoRA + SFTTrainer logic.

### Stage 5: Evaluation (PARTIALLY DONE)

- `[sklearn_evaluator.py](finetune/infrastructure/evaluation/sklearn_evaluator.py)` -- implemented
- **NEW** `finetune/infrastructure/evaluation/report_generator.py` -- Generate Markdown eval report (confusion matrix, per-class F1, comparison table)

### Stage 5-6: Decide + Publish (NOT STARTED)

- **NEW** `finetune/infrastructure/registry/mlflow_registry.py` -- Log training runs, metrics, artifacts to MLflow; manage model stages (Staging/Production)
- **NEW** `finetune/infrastructure/registry/huggingface_publisher.py` -- Push merged+quantized model to HF Hub
- **NEW** `finetune/infrastructure/packaging/awq_quantizer.py` -- Merge LoRA into base model, then AutoAWQ 4-bit quantize

### Tests

- Run existing 16 unit tests after label changes
- Add tests for new components

---

## Execution Order

1. Part 1 (labels) + Part 3 (training config) + Part 4 (stage naming) -- can be done together
2. Part 2 (HLD replacement)
3. Run tests to verify no regressions
4. Part 5 Stage 4: UnslothTrainer implementation
5. Part 5 Stage 5: ReportGenerator
6. Part 5 Stage 5-6: MLflowRegistry + HuggingFacePublisher + AWQ Quantizer
7. Update main.py CLI to wire new components
8. Final test run

