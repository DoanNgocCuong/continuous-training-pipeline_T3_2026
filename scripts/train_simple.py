"""Simple training script using transformers + peft directly."""
import os
import sys
import json
import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType

# Config
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "data/artifacts/training"
VERSION = "v1.0"
DATASET_PATH = f"data/datasets/{VERSION}"

# LoRA config
LORA_CONFIG = {
    "r": 16,
    "lora_alpha": 32,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": TaskType.CAUSAL_LM,
}

# Training config
TRAINING_CONFIG = {
    "num_epochs": 3,
    "per_device_batch_size": 4,  # Smaller for limited GPU memory
    "learning_rate": 2e-4,
    "warmup_ratio": 0.1,
    "max_seq_length": 512,
    "gradient_accumulation_steps": 4,
    "logging_steps": 10,
    "save_steps": 50,
    "save_total_limit": 2,
}


def tokenize(examples, tokenizer, max_length):
    """Tokenize text for training."""
    # examples["text"] is already formatted as ChatML
    result = tokenizer(
        examples["text"],
        truncation=True,
        max_length=max_length,
        padding="max_length",
    )
    # Labels are the same as input_ids for causal LM
    result["labels"] = result["input_ids"].copy()
    return result


def main():
    print(f"Starting training with {MODEL_NAME}")
    print(f"Dataset: {DATASET_PATH}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        padding_side="right"
    )
    tokenizer.pad_token = tokenizer.eos_token

    # Load dataset
    train_file = os.path.join(DATASET_PATH, "train_chatml.jsonl")
    val_file = os.path.join(DATASET_PATH, "val_chatml.jsonl")

    if not os.path.exists(train_file):
        print(f"Error: {train_file} not found!")
        sys.exit(1)

    data_files = {"train": train_file}
    if os.path.exists(val_file):
        data_files["val"] = val_file

    dataset = load_dataset("json", data_files=data_files)

    # Format as ChatML
    def format_chatml(example):
        """Format data as ChatML."""
        text = ""
        for msg in example["messages"]:
            role = msg["role"]
            content = msg["content"]
            text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        return {"text": text.strip()}

    if "train" in dataset:
        dataset["train"] = dataset["train"].map(
            format_chatml,
            remove_columns=dataset["train"].column_names
        )
    if "val" in dataset:
        dataset["val"] = dataset["val"].map(
            format_chatml,
            remove_columns=dataset["val"].column_names
        )

    # Tokenize
    max_len = TRAINING_CONFIG["max_seq_length"]
    if "train" in dataset:
        dataset["train"] = dataset["train"].map(
            lambda x: tokenize(x, tokenizer, max_len),
            batched=False,
            remove_columns=["text"],
        )
    if "val" in dataset:
        dataset["val"] = dataset["val"].map(
            lambda x: tokenize(x, tokenizer, max_len),
            batched=False,
            remove_columns=["text"],
        )

    print(f"Train size: {len(dataset['train'])}")
    if "val" in dataset:
        print(f"Val size: {len(dataset['val'])}")

    # Load model
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    # Apply LoRA
    print("Applying LoRA...")
    lora_config = LoraConfig(**LORA_CONFIG)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=TRAINING_CONFIG["num_epochs"],
        per_device_train_batch_size=TRAINING_CONFIG["per_device_batch_size"],
        gradient_accumulation_steps=TRAINING_CONFIG["gradient_accumulation_steps"],
        learning_rate=TRAINING_CONFIG["learning_rate"],
        warmup_steps=int(TRAINING_CONFIG["warmup_ratio"] * 100),  # Convert ratio to steps
        logging_steps=TRAINING_CONFIG["logging_steps"],
        save_steps=TRAINING_CONFIG["save_steps"],
        save_total_limit=TRAINING_CONFIG["save_total_limit"],
        fp16=True,
        dataloader_num_workers=0,  # Disable multiprocessing for simplicity
        report_to="none",
    )

    # Trainer (no data_collator - already tokenized)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset.get("val"),
    )

    # Train
    print("Starting training...")
    trainer.train()

    # Save
    adapter_path = os.path.join(OUTPUT_DIR, "lora_adapter")
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"Model saved to {adapter_path}")

    # Save metadata
    metadata = {
        "model": MODEL_NAME,
        "version": VERSION,
        "lora_config": LORA_CONFIG,
        "training_config": TRAINING_CONFIG,
        "train_size": len(dataset["train"]),
    }
    with open(os.path.join(OUTPUT_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print("Done!")


if __name__ == "__main__":
    main()
