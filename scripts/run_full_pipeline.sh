#!/bin/bash
# run_full_pipeline.sh — Run all pipeline steps end-to-end
set -e

SOURCE=${1:-"data/raw/extract.csv"}
CONFIG=${2:-"qwen2.5_1.5b_lora"}
VERSION=${3:-"v1.0"}

echo "=== Emotion CT Pipeline ==="
echo "Source: $SOURCE"
echo "Config: $CONFIG"
echo "Version: $VERSION"
echo ""

echo "--- Step 1: Collect data ---"
python -m finetune collect --source "$SOURCE"

echo "--- Step 2: Label data ---"
python -m finetune label

echo "--- Step 2.5: Build datasets ---"
python -m finetune build --version "$VERSION"

echo "--- Step 3: Train ---"
python -m finetune train --config "$CONFIG"

echo "--- Step 4: Evaluate ---"
python -m finetune evaluate

echo "--- Step 5: Decide ---"
python -m finetune decide

echo "=== Pipeline complete ==="
