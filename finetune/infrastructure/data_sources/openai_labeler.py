"""Simple OpenAI labeling - bypass distilabel async issues."""
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from openai import OpenAI
from finetune.domain.value_objects import EmotionLabel

SYSTEM_PROMPT = """You are an emotion classifier for a children's educational robot called Pika Robot.

Given the robot's PREVIOUS response and its CURRENT response, classify the emotion
expressed in the CURRENT response into EXACTLY ONE of these 8 labels:

  happy, achievement, thinking, calm, sad, worried, angry, surprised

Rules:
- Respond with ONLY the emotion label — no explanation, no punctuation.
- If the current response expresses joy, excitement, or playfulness → happy
- If it expresses pride, encouragement, or celebration → achievement
- If it is neutral or resting → calm
- When in doubt, choose the closest match.
"""

VALID_LABELS = frozenset(e.value for e in EmotionLabel if e != EmotionLabel.UNKNOWN)


class OpenAILabeler:
    """Direct OpenAI labeling without distilabel."""

    def __init__(self, model: str = "gpt-4o-mini", batch_size: int = 50):
        self.model = model
        self.batch_size = batch_size
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def label_batch(self, samples: list[dict]) -> list[dict]:
        """Label a batch of samples using OpenAI."""
        results = []
        total_batches = (len(samples) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(samples), self.batch_size):
            batch = samples[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            print(f"Labeling batch {batch_num}/{total_batches} ({len(batch)} samples)")

            for j, sample in enumerate(batch):
                label = self._label_single(sample.get("input_text", sample.get("user_input", "")))
                sample["ai_label"] = label
                results.append(sample)
                if (j + 1) % 10 == 0:
                    print(f"  Progress: {i + j + 1}/{len(samples)}")

        return results

    def _label_single(self, text: str) -> str:
        """Label a single sample."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                max_tokens=20,
                temperature=0.0
            )
            label = response.choices[0].message.content.strip().lower()
            return self._parse_label(label)
        except Exception as e:
            print(f"Error labeling: {e}")
            return "unknown"

    def _parse_label(self, text: str) -> str:
        """Parse emotion label from LLM generation."""
        if text in VALID_LABELS:
            return text
        for label in sorted(VALID_LABELS, key=len, reverse=True):
            if label in text:
                return label
        return "unknown"


if __name__ == "__main__":
    import pandas as pd

    # Change to project root
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

    # Load samples
    df = pd.read_json("data/labeled/raw_samples.jsonl", lines=True)
    samples = df.to_dict("records")

    print(f"Loaded {len(samples)} samples")

    # Label
    labeler = OpenAILabeler()
    labeled = labeler.label_batch(samples)

    # Save
    os.makedirs("data/labeled/ai_labeled", exist_ok=True)
    with open("data/labeled/ai_labeled/labeled.jsonl", "w") as f:
        for sample in labeled:
            f.write(json.dumps(sample) + "\n")

    print(f"Labeled {len(labeled)} samples")
    print("Saved to data/labeled/ai_labeled/labeled.jsonl")
