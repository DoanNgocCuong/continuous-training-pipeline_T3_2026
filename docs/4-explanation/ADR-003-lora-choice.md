# ADR-003: Why LoRA for Fine-tuning

**Status**: Accepted
**Date**: 2026-03-06

---

## Context

We need to choose a fine-tuning method for Qwen2.5-1.5B.

Options:
1. **Full fine-tuning** - Update all parameters
2. **LoRA** - Low-Rank Adaptation
3. **QLoRA** - Quantized LoRA

---

## Decision

We use **LoRA** with the option to upgrade to **QLoRA** for larger models.

---

## Rationale

### 1. Memory Efficiency

| Method | GPU Memory | Trainable Params |
|--------|------------|-------------------|
| Full | ~30GB | 1.5B (100%) |
| LoRA | ~8GB | 2.8M (0.2%) |
| QLoRA | ~4GB | 2.8M (0.2%) |

### 2. Training Speed

- LoRA is **2-5x faster** than full fine-tuning
- Can train on consumer GPUs (RTX 3090)

### 3. Quality

- LoRA achieves **95%+** of full fine-tuning quality
- Works well for instruction tuning

### 4. Simplicity

- Easy to implement with TRL/Unsloth
- No special hardware needed

---

## Implementation

```yaml
# configs/training/qwen2.5_1.5b_lora.yml
lora:
  r: 16                    # Rank
  lora_alpha: 32           # Scaling factor
  target_modules:          # Which layers to adapt
    - q_proj              # Query
    - k_proj              # Key
    - v_proj              # Value
    - o_proj              # Output

  dropout: 0.05
  bias: none
```

---

## Consequences

### Positive

- ✅ Train on consumer GPU (RTX 3090)
- ✅ Fast training (3-5 minutes)
- ✅ Good quality
- ✅ Easy to implement

### Negative

- ❌ Slightly lower quality than full fine-tuning
- ❌ May need hyperparameter tuning
- ❌ Need to merge for inference

---

## Alternatives Considered

### Option A: Full Fine-tuning

**Pros**: Best quality
**Cons**: Requires A100/H100, expensive

### Option B: QLoRA

**Pros**: Even less memory
**Cons**: Slower inference, more complex

---

## References

- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [TRL Library](https://huggingface.co/docs/trl)
- [Unsloth](https://unsloth.ai/)

---

## Related ADRs

- [ADR-001: Why DDD Structure](ADR-001-ddd-structure.md)
- [ADR-004: Why AWQ Quantization](ADR-004-awq-quantization.md)

---

*Last updated: 2026-03-08*
