# Contributing Guide

How to contribute to the Emotion CT Pipeline project.

---

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Welcome newcomers and help them learn
- Focus on what is best for the project

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- GitHub account
- Development environment setup (see [Local Development](../1-tutorials/local-development.md))

### Quick Start

```bash
# 1. Fork the repository
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/emotion-ct-pipeline.git

# 3. Create a feature branch
git checkout -b feature/your-feature

# 4. Make changes and commit
git commit -m "feat: Add new feature"

# 5. Push and create PR
git push origin feature/your-feature
```

---

## Development Workflow

### 1. Pick an Issue

- Check [Issues](https://github.com/pika-robot/emotion-ct-pipeline/issues)
- Look for `good first issue` labels
- Ask questions if anything is unclear

### 2. Create a Branch

```bash
git checkout -b type/description
```

Types:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Adding tests

### 3. Make Changes

#### Code Style

We use:
- **Black** for formatting
- **Ruff** for linting
- **Type hints** for all functions

```python
# Good
def calculate_accuracy(predictions: list[str], labels: list[str]) -> float:
    """Calculate accuracy score.

    Args:
        predictions: Model predictions
        labels: Ground truth labels

    Returns:
        Accuracy score between 0 and 1
    """
    correct = sum(p == l for p, l in zip(predictions, labels))
    return correct / len(labels) if labels else 0.0
```

#### File Organization

```
finetune/
├── domain/           # Pure business logic
│   ├── entities/    # Data classes
│   ├── value_objects/ # Immutable values
│   └── services/    # Domain services
├── application/      # Use cases
│   └── usecases/   # Orchestration
└── infrastructure/  # External integrations
    ├── data_sources/
    ├── training/
    ├── evaluation/
    └── registry/
```

### 4. Write Tests

```python
# tests/unit/test_your_feature.py
import pytest
from finetune.domain.services.your_service import YourService

class TestYourService:
    def test_basic_functionality(self):
        service = YourService()
        result = service.do_something("input")
        assert result == expected_output
```

### 5. Commit

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "type(scope): description

- Detail 1
- Detail 2

Closes #123"
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance

### 6. Push and PR

```bash
git push origin feature/your-feature
```

Then create a Pull Request on GitHub.

---

## Testing Requirements

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific file
python -m pytest tests/unit/test_label_agreement.py -v

# With coverage
python -m pytest tests/ --cov=finetune --cov-report=html
```

### Coverage Requirements

- New code: 80% minimum
- Domain logic: 90% minimum
- Bug fixes: Test required

---

## Pull Request Process

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] PR description complete

### PR Description Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Test Plan
- [ ] Unit tests added/updated
- [ ] Manual testing done

## Checklist
- [ ] Code is type-annotated
- [ ] No lint errors
- [ ] Tests pass
```

### Review Process

1. **Automated checks** run (lint, test, coverage)
2. **Code review** by maintainer(s)
3. **Address feedback** if any
4. **Merge** when approved

---

## Common Contribution Types

### Adding a New Emotion

1. Update `configs/emotions.yml`
2. Add to `EmotionLabel` enum in `finetune/domain/value_objects.py`
3. Add test case in `tests/unit/test_value_objects.py`
4. Update docs (GLOSSARY.md)

### Adding a New Metric

1. Add calculation in `SklearnEvaluator`
2. Add field to `EvalResult` entity
3. Update promotion rules in `configs/evaluation/promotion_rules.yml`
4. Add test

### Adding a CLI Command

1. Add command in `finetune/main.py`
2. Create use case if needed
3. Add tests
4. Update API.md documentation

---

## Questions?

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions
- **Slack**: For real-time discussion

---

## Recognition

Contributors will be recognized in:
- CHANGELOG.md
- GitHub contributors page

---

*Last updated: 2026-03-08*
