# Local Development Setup

A step-by-step tutorial for setting up the Emotion CT Pipeline development environment from scratch.

**Prerequisites**: Python 3.11+, Git, GPU (optional for training)

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/pika-robot/emotion-ct-pipeline.git
cd emotion-ct-pipeline
```

---

## Step 2: Create Virtual Environment

```bash
# Create venv
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

---

## Step 3: Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install ML/AI dependencies
pip install torch transformers trl

# Install optional dependencies (for full pipeline)
pip install huggingface_hub mlflow langfuse argilla
```

---

## Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Optional (for publishing)
HF_TOKEN=hf-your-huggingface-token

# Optional (for MLflow)
MLFLOW_TRACKING_URI=http://localhost:5000

# Optional (for Langfuse)
LANGFUSE_PUBLIC_KEY=pk-your-langfuse-public
LANGFUSE_SECRET_KEY=sk-your-langfuse-secret

# Optional (for notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

> **Security Note**: Never commit `.env` to version control!

---

## Step 5: Verify Installation

```bash
# Check Python version
python --version  # Should be 3.11+

# Check CLI is working
python -m finetune.main --help

# Check PyTorch and CUDA
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

Expected output:
```
Usage: python -m finetune.main [OPTIONS] COMMAND [ARGS]...
Try 'python -m finetune.main --help' for more information.
```

---

## Step 6: Run a Quick Test

```bash
# Run unit tests
python -m pytest tests/unit/ -v
```

Expected: All 16 tests pass ✅

---

## Step 7: Run the Pipeline (Optional)

If you have:
- Raw CSV data in `data/raw/`
- OpenAI API key

```bash
# Activate environment
source .venv/bin/activate

# Set API key
export OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d= -f2-)

# Run full pipeline
python -m finetune.main pipeline --version v1.0
```

---

## Troubleshooting

### CUDA/GPU Issues

```bash
# Check GPU visibility
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

If GPU not available, training will be slow on CPU.

### Import Errors

```bash
# Reinstall dependencies
pip install -e .

# Or reinstall specific package
pip install transformers --upgrade
```

### API Key Errors

```bash
# Verify key is set
echo $OPENAI_API_KEY

# Test OpenAI connection
python -c "import openai; openai.api_key = '$OPENAI_API_KEY'; print(openai.Model.list())"
```

---

## Next Steps

- [First Contribution Guide](first-contribution.md) - Make your first PR
- [API Reference](../3-reference/API.md) - Explore CLI commands
- [SDD](../3-reference/SDD.md) - Understand system architecture

---

*Last updated: 2026-03-08*
