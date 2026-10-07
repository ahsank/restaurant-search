#!/bin/bash
# Run the Approach 6 cross-encoder benchmark on a Colab GPU VM and download the
# metrics. Scoring all 209 queries x every menu item takes about a minute on a
# T4 (vs. ~15 min on a laptop CPU).
#
# Same mechanics as run_llm_eval.sh: ships code + benchmark data with
# `colab upload`, starts the run detached, polls the log through the file API,
# downloads the results into research/results/crossencoder/, and always stops
# the VM on exit. A local model directory (e.g. a finetuned model under
# models/) is uploaded too, at the same relative path.
#
# Usage:
#   research/colab/run_crossencoder_eval.sh                                   # stock ms-marco-MiniLM-L6-v2 on a T4
#   MODEL=models/crossencoder-synthetic-plus-gapfill research/colab/run_crossencoder_eval.sh
#   MODEL=BAAI/bge-reranker-base GPU=L4 research/colab/run_crossencoder_eval.sh
#
# Env: MODEL (hub name or local dir, default cross-encoder/ms-marco-MiniLM-L6-v2),
#      GPU (T4|L4|A100|H100|G4, default T4), SESSION, POLL_SECONDS.
# Auth: Colab CLI with --auth adc (cloud sessions: COLAB_ADC_JSON, see the session-start hook).
set -euo pipefail

MODEL="${MODEL:-cross-encoder/ms-marco-MiniLM-L6-v2}"
GPU="${GPU:-T4}"
SESSION="${SESSION:-ce-eval-$$}"
POLL_SECONDS="${POLL_SECONDS:-30}"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TAG="$(basename "$MODEL")"
OUT_DIR="$ROOT/research/results/crossencoder"
REMOTE=/content/restaurant-search
REL_METRICS="research/results/crossencoder/$TAG.metrics.json"
COLAB=(colab --auth adc)

mkdir -p "$OUT_DIR"
WORK="$(mktemp -d)"
TARBALL="$WORK/restaurant-search.tgz"

cleanup() {
  echo "=== stopping session $SESSION ==="
  "${COLAB[@]}" stop -s "$SESSION" || echo "WARNING: stop failed; check 'colab sessions'"
  rm -rf "$WORK"
}

remote_py() {  # remote_py TIMEOUT CODE — run Python in the VM's kernel
  local timeout="$1"; shift
  printf '%s\n' "$1" | timeout "$((timeout + 60))" "${COLAB[@]}" exec -s "$SESSION" --timeout "$timeout"
}

echo "=== packaging code + benchmark data ==="
PATHS=(research/lib research/search data/menus data/queries)
if [ -d "$ROOT/$MODEL" ]; then
  echo "local model directory: uploading $MODEL"
  PATHS+=("$MODEL")
fi
tar -C "$ROOT" --exclude='__pycache__' --exclude='research/results' --exclude='checkpoints' \
  -czf "$TARBALL" "${PATHS[@]}"
ls -lh "$TARBALL"

echo "=== creating $GPU session $SESSION ==="
"${COLAB[@]}" new -s "$SESSION" --gpu "$GPU"
trap cleanup EXIT

# Upload in ~20 MB parts with per-part retries: one large upload (code + a ~90 MB
# model) can be dropped mid-transfer by the session's network relay.
remote_py 60 "import os; os.makedirs('/content/upload', exist_ok=True); print('upload dir ready')"
split -b 20m -d "$TARBALL" "$WORK/part-"
for part in "$WORK"/part-*; do
  for attempt in 1 2 3; do
    if timeout 300 "${COLAB[@]}" upload -s "$SESSION" "$part" "/content/upload/$(basename "$part")"; then
      break
    fi
    [ "$attempt" = 3 ] && { echo "ERROR: upload of $(basename "$part") failed"; exit 1; }
    echo "upload of $(basename "$part") failed (attempt $attempt), retrying"
  done
done
remote_py 600 "
import subprocess
r = subprocess.run('cat /content/upload/part-* > /content/restaurant-search.tgz'
                   ' && mkdir -p $REMOTE && tar -xzf /content/restaurant-search.tgz -C $REMOTE'
                   ' && pip install -q sentence-transformers 2>&1 | tail -3'
                   ' && nvidia-smi --query-gpu=name,memory.total --format=csv',
                   shell=True, capture_output=True, text=True)
print(r.stdout[-2000:], r.stderr[-2000:])
assert r.returncode == 0
"

echo "=== starting run: $MODEL ==="
LOCAL_LOG="$OUT_DIR/$TAG.log"
ARGS="--engine crossencoder --model $MODEL --save-metrics $REL_METRICS"
for attempt in 1 2 3; do
  remote_py 60 "
import os, subprocess
if os.path.exists('/content/run.log'):
    print('already started')
else:
    subprocess.Popen('cd $REMOTE && (python research/search/evaluate.py $ARGS; echo RUN_EXIT=\$?) > /content/run.log 2>&1',
                     shell=True, start_new_session=True)
    print('started')
" || true
  if timeout 90 "${COLAB[@]}" download -s "$SESSION" /content/run.log "$LOCAL_LOG" >/dev/null 2>&1; then
    break
  fi
  [ "$attempt" = 3 ] && { echo "ERROR: run did not start"; exit 1; }
  echo "launch not confirmed (attempt $attempt), retrying"
done

echo "=== polling every ${POLL_SECONDS}s ==="
while true; do
  sleep "$POLL_SECONDS"
  if ! timeout 90 "${COLAB[@]}" download -s "$SESSION" /content/run.log "$LOCAL_LOG" >/dev/null 2>&1; then
    echo "[$(date +%H:%M:%S)] poll failed, retrying"; continue
  fi
  echo "[$(date +%H:%M:%S)] $(tr '\r' '\n' < "$LOCAL_LOG" | grep -v '^\s*$' | tail -1 | cut -c1-160)"
  grep -q '^RUN_EXIT=' "$LOCAL_LOG" && break
done
grep -q '^RUN_EXIT=0$' "$LOCAL_LOG" || { echo "ERROR: run failed"; tail -40 "$LOCAL_LOG"; exit 1; }

echo "=== downloading results ==="
tr '\r' '\n' < "$LOCAL_LOG" | grep -vE 'it/s\]|^\s*$' > "$LOCAL_LOG.tmp" && mv "$LOCAL_LOG.tmp" "$LOCAL_LOG"
grep -E 'NDCG@5  |Recall@10  |MRR  ' "$LOCAL_LOG" | tail -3
"${COLAB[@]}" download -s "$SESSION" "$REMOTE/$REL_METRICS" "$ROOT/$REL_METRICS"
echo "Results in $OUT_DIR/$TAG.{metrics.json,log}"
