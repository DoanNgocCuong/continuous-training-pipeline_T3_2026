# First Contribution Guide

A guide for making your first contribution to the Emotion CT Pipeline.

**Prerequisites**: Git, GitHub account, local development setup

---

## Overview

This guide walks through:
1. Creating a feature branch
2. Making code changes
3. Running tests
4. Creating a Pull Request

---

## Step 1: Sync Your Fork

```bash
# If you forked the repo
git remote add upstream https://github.com/pika-robot/emotion-ct-pipeline.git

# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main
```

---

## Step 2: Create a Feature Branch

```bash
# Create and switch to new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring

---

## Step 3: Make Your Changes

### Code Style

Follow these conventions:

```python
# Use type hints
def train_model(dataset_path: str, config: dict) -> TrainingRun:
    """Train a model on the given dataset.

    Args:
        dataset_path: Path to training data
        config: Training configuration

    Returns:
        TrainingRun object with results
    """
    pass

# Use logging
import logging
logger = logging.getLogger(__name__)

# Handle errors with custom exceptions
from finetune.domain.exceptions import ModelPublishError
raise ModelPublishError(f"Failed to publish: {error}")
```

### File Organization

```
finetune/
├── domain/           # Pure business logic (no external deps)
│   ├── entities/
│   ├── value_objects/
│   └── services/
├── application/      # Use cases
│   └── usecases/
└── infrastructure/  # External implementations
    ├── data_sources/
    ├── training/
    └── evaluation/
```

---

## Step 4: Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/unit/test_label_agreement.py -v

# Run with coverage
python -m pytest tests/ --cov=finetune --cov-report=html
```

### Writing Tests

Follow the test structure:

```python
# tests/unit/test_your_feature.py
import pytest
from finetune.domain.services.your_service import YourService

class TestYourService:
    """Tests for YourService."""

    def test_should_do_something(self):
        """Test description."""
        service = YourService()
        result = service.do_something()
        assert result == expected

    def test_should_raise_error_on_invalid_input(self):
        """Test error handling."""
        with pytest.raises(YourException):
            service.do_something(invalid_input)
```

---

## Step 5: Commit Your Changes

```bash
# Check what changed
git status
git diff

# Stage changes
git add path/to/changed/file.py

# Commit with conventional message
git commit -m "feat: Add new feature for emotion detection

- Added new service for X
- Updated tests
- Updated documentation

Closes #123"
```

### Commit Message Convention

```
<type>: <short description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

---

## Step 6: Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then in GitHub:
1. Go to your fork
2. Click "Compare & pull request"
3. Fill in PR template
4. Submit PR

### PR Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Test Plan
How did you test your changes?

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes
```

---

## Common Contribution Types

### Adding a New Emotion

1. Update `configs/emotions.yml`
2. Add to `EmotionLabel` enum in `finetune/domain/value_objects.py`
3. Add tests
4. Update documentation

### Adding a New Metric

1. Add metric calculation in `SklearnEvaluator`
2. Add to `EvalResult` entity
3. Update promotion rules if needed
4. Add tests

### Adding a New CLI Command

1. Add command in `finetune/main.py`
2. Create use case if needed
3. Add tests
4. Update API reference docs

---

## Getting Help

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Slack**: Join the team Slack channel

---

## Code Review Tips

### For Reviewers
- Be constructive and specific
- Suggest improvements, don't just criticize
- Approve if changes are correct, not perfect

### For Authors
- Respond to all comments
- Don't take feedback personally
- Ask for clarification if needed

---

*Last updated: 2026-03-08*
