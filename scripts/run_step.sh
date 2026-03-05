#!/bin/bash
# run_step.sh — Run a single pipeline step
# Usage: ./scripts/run_step.sh <step> [args...]
# Steps: collect, label, build, train, evaluate, decide
set -e

STEP=$1
shift

if [ -z "$STEP" ]; then
  echo "Usage: $0 <step> [args...]"
  echo "Steps: collect, label, build, train, evaluate, decide"
  exit 1
fi

echo "--- Running step: $STEP $@ ---"
python -m finetune "$STEP" "$@"
