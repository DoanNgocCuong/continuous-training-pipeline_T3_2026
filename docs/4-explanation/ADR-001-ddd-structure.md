# ADR-001: Why Clean Architecture with DDD

**Status**: Accepted
**Date**: 2026-03-06

---

## Context

We need to decide on the architectural approach for the Emotion CT Pipeline.

Options considered:
1. **Monolithic script** - All in one file
2. **Layered architecture** - UI/Business/Data
3. **Clean Architecture with DDD** - Domain/Application/Infrastructure

---

## Decision

We will use **Clean Architecture with Domain-Driven Design (DDD)**.

---

## Rationale

### 1. Separation of Concerns

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  (Use Cases: Collect, Label, Train, Evaluate...)      │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                    Domain Layer                         │
│  (Entities, Services: Agreement, Promotion, Drift)    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                Infrastructure Layer                     │
│  (CSV, OpenAI, TRL, Sklearn, MLflow, HuggingFace)   │
└─────────────────────────────────────────────────────────┘
```

### 2. Testability

- Domain layer has **zero external dependencies**
- Easy to unit test domain logic
- Can mock infrastructure for testing

```python
# Easy to test - no external deps
from finetune.domain.services.label_agreement import LabelAgreementService

def test_auto_approve():
    service = LabelAgreementService()
    result = service.resolve("happy", "happy", "happy")
    assert result == AgreementStatus.AUTO_APPROVED
```

### 3. Flexibility

- Can swap out infrastructure without changing domain logic
- Example: Replace TRL with Unsloth without touching domain

### 4. Maintainability

- Clear boundaries between layers
- Self-documenting structure
- Easier to onboard new developers

---

## Consequences

### Positive

- ✅ Easier to test domain logic
- ✅ Clear dependency direction
- ✅ Flexible infrastructure choices
- ✅ Scalable codebase

### Negative

- ❌ More boilerplate code
- ❌ Learning curve for DDD concepts
- ❌ May be overkill for small projects

---

## Implementation

### Directory Structure

```
finetune/
├── domain/                    # Pure Python, 0 deps
│   ├── entities/             # EmotionSample, TrainingRun
│   ├── value_objects/        # EmotionLabel, ConfidenceScore
│   ├── exceptions/           # Custom exceptions
│   └── services/             # LabelAgreement, PromotionDecider
│
├── application/              # Use cases
│   ├── repositories/         # ABCs (interfaces)
│   └── usecases/            # Orchestration
│
└── infrastructure/           # Concrete implementations
    ├── data_sources/        # CSV, OpenAI, Argilla
    ├── training/            # TRL, Unsloth
    ├── evaluation/          # Sklearn
    ├── registry/            # MLflow, HuggingFace
    └── observability/       # Langfuse, notifications
```

### Dependency Rule

> Inner layers know nothing about outer layers.

- Domain ← Application ← Infrastructure
- Domain is the core, everything depends on it

---

## Alternatives Considered

### Option A: Monolithic Script

**Pros**: Quick to start, simple
**Cons**: Hard to test, maintain, scale

### Option B: Layered Architecture

**Pros**: Familiar pattern
**Cons**: Unclear boundaries, hidden dependencies

---

## References

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) by Robert C. Martin
- [Domain-Driven Design](https://domainlanguage.com/ddd/) by Eric Evans

---

## Related ADRs

- [ADR-002: Why 3-Way Agreement for Labeling](ADR-002-3-way-agreement.md)
- [ADR-003: Why LoRA for Fine-tuning](ADR-003-lora-choice.md)

---

*Last updated: 2026-03-08*
