"""Merge LoRA adapter into base model, then quantize with AutoAWQ."""
import logging
import os
import shutil
from typing import Optional

logger = logging.getLogger(__name__)


class AWQQuantizer:
    """Merge LoRA weights into base model, then quantize to AWQ 4-bit.

    Two-step process:
      1. merge_lora()  — base + adapter → full fp16 model
      2. quantize()    — fp16 model → AWQ 4-bit

    Requires: pip install unsloth autoawq
    """

    def __init__(self, bits: int = 4, group_size: int = 128):
        self.bits = bits
        self.group_size = group_size

    def merge_lora(
        self,
        base_model: str,
        adapter_path: str,
        output_path: str,
        max_seq_length: int = 2048,
    ) -> str:
        """Merge LoRA adapter into base model and save as fp16.

        Returns path to merged model.
        """
        from unsloth import FastLanguageModel

        logger.info(
            "Merging LoRA adapter into %s (adapter=%s)", base_model, adapter_path
        )

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=adapter_path,
            max_seq_length=max_seq_length,
            load_in_4bit=True,
        )

        merged_path = os.path.join(output_path, "merged_fp16")
        os.makedirs(merged_path, exist_ok=True)

        model.save_pretrained_merged(
            merged_path,
            tokenizer,
            save_method="merged_16bit",
        )

        logger.info("Merged model saved to %s", merged_path)
        return merged_path

    def quantize(
        self,
        model_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """Quantize a merged fp16 model to AWQ 4-bit.

        Returns path to quantized model.
        """
        try:
            from awq import AutoAWQForCausalLM
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "autoawq not installed. Run: pip install autoawq"
            ) from exc

        quant_path = output_path or f"{model_path}_awq"
        os.makedirs(quant_path, exist_ok=True)

        logger.info("Quantizing %s to AWQ %d-bit", model_path, self.bits)

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoAWQForCausalLM.from_pretrained(model_path)

        quant_config = {
            "zero_point": True,
            "q_group_size": self.group_size,
            "w_bit": self.bits,
            "version": "GEMM",
        }

        model.quantize(tokenizer, quant_config=quant_config)
        model.save_quantized(quant_path)
        tokenizer.save_pretrained(quant_path)

        logger.info("Quantized model saved to %s", quant_path)
        return quant_path

    def merge_and_quantize(
        self,
        base_model: str,
        adapter_path: str,
        output_path: str,
        max_seq_length: int = 2048,
        cleanup_merged: bool = True,
    ) -> str:
        """Full pipeline: merge LoRA → quantize AWQ → return final path.

        Args:
            cleanup_merged: Remove intermediate fp16 model to save disk.
        """
        merged_path = self.merge_lora(
            base_model, adapter_path, output_path, max_seq_length
        )

        quant_path = os.path.join(output_path, "awq_quantized")
        self.quantize(merged_path, quant_path)

        if cleanup_merged and os.path.isdir(merged_path):
            shutil.rmtree(merged_path)
            logger.info("Cleaned up intermediate merged model at %s", merged_path)

        return quant_path
