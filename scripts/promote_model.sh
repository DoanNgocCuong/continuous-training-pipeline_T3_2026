#!/bin/bash
# promote_model.sh — Manually promote a candidate model to HuggingFace Hub
set -e

RUN_ID=${1:-"latest"}
HF_REPO=${2:-""}

if [ -z "$HF_REPO" ]; then
  echo "Usage: $0 <run_id> <hf_repo>"
  echo "Example: $0 latest my-org/pika-emotion-v1"
  exit 1
fi

echo "--- Promoting model run=$RUN_ID to $HF_REPO ---"
python -m finetune publish --run-id "$RUN_ID" --repo "$HF_REPO"
