# ADR-002: Why 3-Way Agreement for Labeling

**Status**: Accepted
**Date**: 2026-03-06

---

## Context

When labeling data with AI, how do we ensure quality and handle disagreements?

Options:
1. **Single labeler** - Just AI or just human
2. **Majority voting** - Multiple labelers, take majority
3. **3-way agreement** - AI, Human, Model all label

---

## Decision

We use **3-way agreement** between:
1. **AI labeler** (GPT-4o-mini)
2. **Human annotator**
3. **Previous model** (if available)

---

## Rationale

### 1. Quality Assurance

```
┌─────────────┬─────────────┬─────────────┬────────────────────────┐
│ AI Label    │ Human Label │ Model Label │ Decision               │
├─────────────┼─────────────┼─────────────┼────────────────────────┤
│ happy       │ happy       │ happy       │ ✅ auto_approved       │
│ happy       │ happy       │ sad         │ ✅ auto_approved_gold  │
│ happy       │ sad        │ happy       │ ✅ human_resolved      │
│ happy       │ angry      │ thinking    │ ⚠️ flagged             │
│ happy       │ -          │ -          │ ⏳ pending             │
└─────────────┴─────────────┴─────────────┴────────────────────────┘
```

### 2. Trust Hierarchy

1. **Human is gold standard** - Trust human over AI
2. **AI consensus** - If AI agrees with itself (current model), trust it
3. **Flag for review** - When all disagree

### 3. Cost Efficiency

- Only send to human when needed (not every sample)
- Reduce API costs by filtering obvious cases
- Human effort focused on hard cases

---

## Implementation

```python
class LabelAgreementService:
    """3-way agreement logic."""

    def resolve(
        self,
        ai_label: EmotionLabel,
        human_label: Optional[EmotionLabel],
        model_label: Optional[EmotionLabel],
    ) -> AgreementStatus:
        # Case 1: All agree
        if ai_label == human_label == model_label:
            return AgreementStatus.AUTO_APPROVED

        # Case 2: AI == Human (gold standard)
        if ai_label == human_label:
            return AgreementStatus.AUTO_APPROVED_GOLD

        # Case 3: AI == Model (trust model)
        if ai_label == model_label:
            return AgreementStatus.HUMAN_RESOLVED

        # Case 4: All different
        if human_label is not None:
            return AgreementStatus.FLAGGED

        # Case 5: No human label
        return AgreementStatus.PENDING
```

---

## Consequences

### Positive

- ✅ Higher label quality
- ✅ Cost-effective (fewer human labels needed)
- ✅ Clear escalation path
- ✅ Audit trail

### Negative

- ❌ More complex logic
- ❌ Need human annotators
- ❌ Need previous model for 3-way

---

## Alternatives Considered

### Option A: Single Labeler

**Pros**: Simple, cheap
**Cons**: No quality check, errors propagate

### Option B: Majority Voting

**Pros**: Robust to individual errors
**Cons**: Doesn't leverage human expertise

---

## References

- [Label Studio](https://labelstud.io/) - Open source labeling
- [Snorkel](https://snorkel.org/) - Weak supervision

---

## Related ADRs

- [ADR-001: Why DDD Structure](ADR-001-ddd-structure.md)
- [ADR-004: Why AWQ Quantization](ADR-004-awq-quantization.md)

---

*Last updated: 2026-03-08*
