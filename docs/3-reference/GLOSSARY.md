# Glossary

## Domain Terminology

---

## Core Concepts

### Emotion Classification
The task of classifying text into one of 13 emotion categories for the Pika Robot's child-friendly interaction system.

### Continuous Training (CT)
A machine learning practice where models are periodically retrained on new data to maintain and improve performance over time.

### Fine-tuning
The process of adapting a pre-trained model (Qwen2.5-1.5B-Instruct) to a specific task (emotion classification) using LoRA.

---

## Pipeline Stages

### Collect
The process of loading raw data from CSV exports (typically from Datadog or other data sources).

### Label
The process of assigning emotion labels to text samples using AI (GPT-4o-mini) with 3-way agreement validation.

### Build
The process of creating train/validation/test splits from labeled data using stratified sampling.

### Train
The process of fine-tuning the base model using LoRA (Low-Rank Adaptation).

### Evaluate
The process of measuring model performance using various metrics (accuracy, F1, etc.).

### Decide
The process of determining whether to promote a model based on predefined thresholds.

---

## Emotion Labels

| Label | Description |
|-------|-------------|
| `happy` | Positive, joyful emotion |
| `achievement` | Pride from accomplishing something |
| `thinking` | Contemplative, thoughtful state |
| `calm` | Peaceful, relaxed state |
| `sad` | Negative, sorrowful emotion |
| `worried` | Anxious, concerned state |
| `angry` | Frustrated, irritated emotion |
| `surprised` | Unexpected event reaction |
| `sending_heart` | Expressing love/affection |
| `sun_glassed` | Cool, confident expression |
| `dizzy` | Confused, disoriented state |
| `sobbing` | Crying, emotional distress |
| `superhero` | Powerful, confident expression |

---

## Agreement Status

| Status | Description |
|--------|-------------|
| `auto_approved` | AI == Human == Model (perfect agreement) |
| `auto_approved_gold` | AI == Human != Model (human is gold standard) |
| `human_resolved` | AI == Model != Human (trust human judgment) |
| `flagged` | All three different (needs review) |
| `pending` | No human label available |

---

## Model Training

### LoRA (Low-Rank Adaptation)
A parameter-efficient fine-tuning technique that adds small trainable matrices to the model without modifying the original weights.

- **r (rank)**: Dimension of low-rank matrices
- **alpha**: Scaling factor
- **target_modules**: Which layers to apply LoRA (q_proj, k_proj, v_proj, o_proj)

### AWQ (Activation-aware Weight Quantization)
A quantization technique that compresses model weights to 4-bit with minimal accuracy loss.

### Base Model
The original pre-trained model used for fine-tuning: `Qwen/Qwen2.5-1.5B-Instruct`

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| `accuracy` | Percentage of correct predictions |
| `f1_macro` | F1 score averaged across classes (unweighted) |
| `f1_weighted` | F1 score weighted by class support |
| `precision` | True positives / (true positives + false positives) |
| `recall` | True positives / (true positives + false negatives) |
| `per_class_f1` | F1 score for each emotion class |

---

## Drift Detection

### Data Drift
Change in the distribution of input data (label distribution) over time.

- **KL Divergence**: Measures difference between probability distributions
- **PSI (Population Stability Index)**: Measures distribution shift

### Performance Drift
Change in model performance metrics over time.

- **Accuracy drop**: Decrease in accuracy from baseline
- **F1 regression**: Decrease in F1 score from baseline

### Concept Drift
Change in the underlying relationship between inputs and outputs.

---

## Deployment

### Canary Deployment
A deployment strategy where a new version is gradually rolled out to a small percentage of traffic before full deployment.

### Staging
MLflow model stage for models that passed evaluation but are not yet in production.

### Production
MLflow model stage for models actively serving predictions.

### Rollback
The process of reverting to a previous model version.

---

## Infrastructure

### MLflow
Open-source platform for managing the ML lifecycle, including experiment tracking and model registry.

### Langfuse
Observability platform for LLM applications, providing tracing and cost tracking.

### Argilla
Human-in-the-loop platform for data labeling and quality assurance.

### HuggingFace Hub
Platform for sharing ML models and datasets.

---

## Project Structure

### Domain Layer
Pure Python business logic with no external dependencies:
- Entities: `EmotionSample`, `TrainingRun`, `EvalResult`
- Value Objects: `EmotionLabel`, `ConfidenceScore`
- Services: `LabelAgreementService`, `PromotionDeciderService`

### Application Layer
Use cases that orchestrate domain logic and infrastructure:
- `CollectDataUseCase`
- `LabelDataUseCase`
- `BuildDatasetsUseCase`
- `RunTrainingUseCase`
- `RunEvaluationUseCase`
- `DecidePromotionUseCase`

### Infrastructure Layer
Concrete implementations of external systems:
- Data Sources: CSV loader, OpenAI labeler
- Training: TRL trainer
- Evaluation: Sklearn evaluator
- Registry: MLflow, HuggingFace

---

*Last updated: 2026-03-08*
