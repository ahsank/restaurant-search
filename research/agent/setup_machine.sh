#!/usr/bin/env bash
# Machine setup for agent experiments, run by research/colab/agent_campaign.ipynb at the start of
# every session (after its own pip installs) and safe to run by hand: `bash research/agent/setup_machine.sh`.
#
# Agents append the packages and downloads their experiments need here instead of committing large
# artifacts. Keep every step idempotent (skip what is already installed/downloaded), and document what
# each download is for in research/agent/README.md. Downloads go outside the repo or under models/.
set -euo pipefail
cd "$(dirname "$0")/../.."
SCRATCH_DIR="${SCRATCH_DIR:-/content/scratch}"
mkdir -p "$SCRATCH_DIR"

# --- packages ------------------------------------------------------------------------
# e.g. pip install -q rank-bm25
pip install -q accelerate
# Mismatched torchaudio/torchvision breaks transformers imports on PyTorch with CUDA 13.0
pip uninstall -y torchaudio torchvision >/dev/null 2>&1 || true

# --- models / data -------------------------------------------------------------------
# Hugging Face models normally need no step here: they download on first use into the HF cache.
# Add explicit downloads only for files that aren't fetched automatically, e.g.:
[ -f "$SCRATCH_DIR/numberbatch-en-19.08.txt.gz" ] || wget -q -O "$SCRATCH_DIR/numberbatch-en-19.08.txt.gz" https://conceptnet.s3.amazonaws.com/downloads/2019/numberbatch/numberbatch-en-19.08.txt.gz
