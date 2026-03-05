"""Fine-tune Qwen2.5 using Unsloth + QLoRA + SFTTrainer."""
import json
import logging
import os
import time
from pathlib import Path

from finetune.application.repositories.trainer_repository import ITrainerRepository
from finetune.domain.entities import TrainingRun
from finetune.domain.exceptions import TrainingFailedError

logger = logging.getLogger(__name__)


class UnslothTrainer(ITrainerRepository):
    """Fine-tune using Unsloth QLoRA + HuggingFace SFTTrainer.

    Requires: pip install unsloth trl datasets
    Requires: NVIDIA GPU with CUDA
    """

    def train(self, dataset_path: str, config: dict) -> TrainingRun:
        run = TrainingRun(
            base_model=config.get("base_model", "Qwen/Qwen2.5-1.5B-Instruct"),
            dataset_version=os.path.basename(dataset_path),
            config_path=config.get("_source", ""),
            status="running",
        )
        logger.info("Starting training run %s", run.run_id)
        start = time.time()

        try:
            self._execute_training(dataset_path, config, run)
        except Exception as exc:
            run.status = "failed"
            run.training_time_seconds = time.time() - start
            logger.error("Training failed: %s", exc)
            raise TrainingFailedError(str(exc)) from exc

        run.training_time_seconds = time.time() - start
        run.status = "completed"
        logger.info(
            "Training complete in %.1fs. Adapter at %s",
            run.training_time_seconds, run.adapter_path,
        )
        return run

    def _execute_training(self, dataset_path: str, config: dict, run: TrainingRun) -> None:
        from unsloth import FastLanguageModel

        lora_cfg = config.get("lora", {})
        train_cfg = config.get("training", {})
        data_cfg = config.get("data", {})
        output_dir = config.get("output_dir", "data/artifacts")
        run_output = os.path.join(output_dir, run.run_id)
        os.makedirs(run_output, exist_ok=True)

        # 1. Load base model with Unsloth (4-bit if configured)
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=config["base_model"],
            max_seq_length=train_cfg.get("max_seq_length", 2048),
            load_in_4bit=config.get("load_in_4bit", True),
            dtype=None,
        )

        # 2. Apply LoRA adapters
        model = FastLanguageModel.get_peft_model(
            model,
            r=lora_cfg.get("r", 16),
            lora_alpha=lora_cfg.get("alpha", 32),
            lora_dropout=lora_cfg.get("dropout", 0.05),
            target_modules=lora_cfg.get("target_modules", [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "up_proj", "down_proj", "gate_proj",
            ]),
            bias="none",
            use_gradient_checkpointing="unsloth",
        )

        # 3. Load dataset
        dataset = self._load_dataset(dataset_path, data_cfg, tokenizer)

        # 4. Configure SFTTrainer
        from trl import SFTTrainer
        from transformers import TrainingArguments

        training_args = TrainingArguments(
            output_dir=run_output,
            num_train_epochs=train_cfg.get("num_epochs", 3),
            per_device_train_batch_size=train_cfg.get("per_device_batch_size", 8),
            gradient_accumulation_steps=train_cfg.get("gradient_accumulation_steps", 4),
            learning_rate=train_cfg.get("learning_rate", 2e-4),
            warmup_ratio=train_cfg.get("warmup_ratio", 0.1),
            lr_scheduler_type=train_cfg.get("lr_scheduler", "cosine"),
            weight_decay=train_cfg.get("weight_decay", 0.01),
            fp16=train_cfg.get("fp16", True),
            logging_steps=train_cfg.get("logging_steps", 10),
            eval_strategy=train_cfg.get("eval_strategy", "no"),
            eval_steps=train_cfg.get("eval_steps", 50),
            save_strategy=train_cfg.get("save_strategy", "steps"),
            save_steps=train_cfg.get("save_steps", 100),
            save_total_limit=2,
            report_to="none",
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=dataset["train"],
            eval_dataset=dataset.get("val"),
            args=training_args,
            max_seq_length=train_cfg.get("max_seq_length", 2048),
            dataset_text_field="text",
        )

        # 5. Train
        train_result = trainer.train()
        run.training_loss = train_result.training_loss

        # 6. Save LoRA adapter
        adapter_path = os.path.join(run_output, "lora_adapter")
        model.save_pretrained(adapter_path)
        tokenizer.save_pretrained(adapter_path)
        run.adapter_path = adapter_path

        # 7. Save run metadata
        self._save_metadata(run, run_output)

    def _load_dataset(self, dataset_path: str, data_cfg: dict, tokenizer) -> dict:
        from datasets import load_dataset

        data_files = {}
        dataset_format = (data_cfg.get("format") or "chatml").lower()

        # Prefer ChatML exports when available (messages[]), otherwise fall back to internal JSONL.
        if dataset_format == "chatml":
            train_file = os.path.join(dataset_path, "train_chatml.jsonl")
            val_file = os.path.join(dataset_path, "val_chatml.jsonl")
        else:
            train_file = os.path.join(dataset_path, "train.jsonl")
            val_file = os.path.join(dataset_path, "val.jsonl")

        if os.path.exists(train_file):
            data_files["train"] = train_file
        else:
            raise FileNotFoundError(f"Training file not found: {train_file}")

        if os.path.exists(val_file):
            data_files["val"] = val_file

        dataset = load_dataset("json", data_files=data_files)

        # Map ChatML {"messages": [...]} to a single "text" field for SFTTrainer.
        if dataset_format == "chatml":
            def _to_text(row: dict) -> dict:
                messages = row.get("messages")
                if not messages:
                    raise ValueError("ChatML row missing 'messages'")
                return {
                    "text": tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=False,
                    )
                }

            dataset = dataset.map(_to_text, remove_columns=dataset["train"].column_names)

        return dataset

    @staticmethod
    def _save_metadata(run: TrainingRun, output_dir: str) -> None:
        meta = {
            "run_id": run.run_id,
            "base_model": run.base_model,
            "dataset_version": run.dataset_version,
            "adapter_path": run.adapter_path,
            "training_loss": run.training_loss,
            "training_time_seconds": run.training_time_seconds,
            "status": run.status,
        }
        meta_path = os.path.join(output_dir, "run_metadata.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
