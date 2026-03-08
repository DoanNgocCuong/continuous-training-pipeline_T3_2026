"""
Model Card Generator.

Generates README.md for HuggingFace model hub from eval results.
"""

import os
from typing import Optional
from datetime import datetime


class ModelCardGenerator:
    """Generate model cards for HuggingFace Hub."""

    def __init__(self, base_model: str = "Qwen/Qwen2.5-1.5B-Instruct"):
        self.base_model = base_model

    def generate(
        self,
        version: str,
        eval_result: dict,
        metrics: Optional[dict] = None,
    ) -> str:
        """Generate model card content.

        Args:
            version: Model version (e.g., v1.0)
            eval_result: Evaluation results dictionary
            metrics: Optional additional metrics

        Returns:
            Markdown content for model card
        """
        metrics = metrics or {}

        # Extract key metrics
        accuracy = eval_result.get("accuracy", 0)
        f1_macro = eval_result.get("f1_macro", 0)
        f1_per_class = eval_result.get("f1_per_class", {})

        # Build per-class F1 table
        f1_table = self._build_f1_table(f1_per_class)

        return f"""---
license: apache-2.
base_model: {self.base_model}
tags:
- emotion-classification
- pika-robot
- fine-tuned
- lora
datasets:
- pika-robot/emotion-classification
metrics:
- accuracy
- f1_macro

---

# Emotion Classifier - {version}

Fine-tuned model for emotion classification for Pika Robot.

## Model Details

- **Base Model**: {self.base_model}
- **Version**: {version}
- **Task**: Multi-class emotion classification
- **Emotions**: happy, achievement, thinking, calm, sad, worried, angry, surprised, sending_heart, sun_glassed, dizzy, sobbing, superhero
- **Fine-tuning Method**: LoRA (r=16, alpha=32)

## Evaluation Results

| Metric | Value |
|--------|-------|
| Accuracy | {accuracy:.1%} |
| F1 Macro | {f1_macro:.1%} |

### Per-Class F1 Scores

{f1_table}

## Usage

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

model_name = "pika-robot/qwen2.5-1.5b-emotion-{version}"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Predict
inputs = tokenizer("Hello!", return_tensors="pt")
outputs = model(**inputs)
predicted_class = outputs.logits.argmax(dim=-1)
```

## Training Details

- **Dataset**: Pika Robot emotion dataset
- **Training Split**: 70%
- **Validation Split**: 15%
- **Test Split**: 15%

---

*Model card generated on {datetime.now().strftime('%Y-%m-%d')}*
"""

    def _build_f1_table(self, f1_per_class: dict) -> str:
        """Build markdown table for per-class F1."""
        if not f1_per_class:
            return "No per-class metrics available."

        rows = []
        for emotion, f1 in sorted(f1_per_class.items()):
            rows.append(f"| {emotion} | {f1:.1%} |")

        return "| Emotion | F1 Score |\n|--------|----------|\n" + "\n".join(rows)

    def save(self, output_path: str, version: str, eval_result: dict,
             metrics: Optional[dict] = None) -> None:
        """Generate and save model card to file.

        Args:
            output_path: Path to save README.md
            version: Model version
            eval_result: Evaluation results
            metrics: Optional additional metrics
        """
        content = self.generate(version, eval_result, metrics)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)
