#!/bin/bash
# Run the Approach 7 LLM-reader benchmark (research/search/llm_search.py) on a
# Colab GPU VM and download the results.
#
# Ships the code and benchmark data with `colab upload` (no git clone, so no
# GitHub token needed), installs vLLM, starts the run detached on the VM so a
# dropped connection doesn't kill it, polls the log, downloads the rankings,
# metrics and log into research/results/llm/, and always stops the VM on exit.
#
# Usage:
#   research/colab/run_llm_eval.sh                                # Qwen2.5-7B on an L4
#   MODEL=microsoft/Phi-3.5-mini-instruct research/colab/run_llm_eval.sh
#   LIMIT=5 research/colab/run_llm_eval.sh                        # smoke test
#   GPU=A100 MODEL=Qwen/Qwen2.5-14B-Instruct research/colab/run_llm_eval.sh
#
# Env: MODEL, GPU (T4|L4|A100|H100|G4, default L4), LIMIT, SESSION,
#      EXTRA_ARGS (passed to llm_search.py), HF_TOKEN (only for gated models).
# Auth: Colab CLI with --auth adc (cloud sessions: see .claude/hooks/session-start.sh).
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
GPU="${GPU:-L4}"
SESSION="${SESSION:-llm-eval-$$}"
LIMIT="${LIMIT:-}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
POLL_SECONDS="${POLL_SECONDS:-60}"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TAG="$(basename "$MODEL" | tr '[:upper:]' '[:lower:]')${LIMIT:+-limit$LIMIT}"
OUT_DIR="$ROOT/research/results/llm"
REMOTE=/content/restaurant-search
REMOTE_OUT="$REMOTE/research/results/llm/$TAG.jsonl"
COLAB=(colab --auth adc)

mkdir -p "$OUT_DIR"
TARBALL="$(mktemp -d)/restaurant-search.tgz"

cleanup() {
  echo "=== stopping session $SESSION ==="
  "${COLAB[@]}" stop -s "$SESSION" || echo "WARNING: stop failed; check 'colab sessions'"
}

remote_py() {  # remote_py TIMEOUT CODE — run Python in the VM's kernel
  # `exec --timeout` bounds the code, not a stuck connection, so also cap the client.
  local timeout="$1"; shift
  printf '%s\n' "$1" | timeout "$((timeout + 60))" "${COLAB[@]}" exec -s "$SESSION" --timeout "$timeout"
}

echo "=== packaging code + benchmark data ==="
tar -C "$ROOT" --exclude='__pycache__' --exclude='research/results' \
  -czf "$TARBALL" research/lib research/search data/menus data/queries
ls -lh "$TARBALL"

echo "=== creating $GPU session $SESSION ==="
"${COLAB[@]}" new -s "$SESSION" --gpu "$GPU"
trap cleanup EXIT

"${COLAB[@]}" upload -s "$SESSION" "$TARBALL" /content/restaurant-search.tgz
remote_py 120 "
import subprocess
subprocess.run('mkdir -p $REMOTE && tar -xzf /content/restaurant-search.tgz -C $REMOTE && nvidia-smi --query-gpu=name,memory.total --format=csv', shell=True, check=True)
"

echo "=== installing vLLM (several minutes) ==="
remote_py 1800 "
import subprocess
r = subprocess.run('pip install -q vllm 2>&1 | tail -5; python -c \"import vllm; print(\'vllm\', vllm.__version__)\"', shell=True, capture_output=True, text=True)
print(r.stdout[-3000:], r.stderr[-3000:])
assert r.returncode == 0
"

echo "=== starting run: $MODEL ==="
ARGS="--model $MODEL --out $REMOTE_OUT ${LIMIT:+--limit $LIMIT} $EXTRA_ARGS"
remote_py 60 "
import os, subprocess
env = dict(os.environ, HF_TOKEN='${HF_TOKEN:-}') if '${HF_TOKEN:-}' else dict(os.environ)
log = open('/content/run.log', 'w')
p = subprocess.Popen('cd $REMOTE && exec python research/search/llm_search.py $ARGS', shell=True,
                     stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
open('/content/run.pid', 'w').write(str(p.pid))
print('started pid', p.pid)
"

echo "=== polling every ${POLL_SECONDS}s ==="
while true; do
  sleep "$POLL_SECONDS"
  STATUS="$(remote_py 60 "
import os
pid = int(open('/content/run.pid').read())
try:
    os.kill(pid, 0); alive = os.waitpid(pid, os.WNOHANG) == (0, 0)
except (ProcessLookupError, ChildProcessError):
    alive = False
lines = open('/content/run.log', errors='replace').read().replace(chr(13), chr(10)).splitlines()
print(chr(10).join(l[-200:] for l in lines[-3:]))
print('RUNNING' if alive else 'FINISHED')
" 2>&1 || echo "POLL_FAILED")"
  echo "[$(date +%H:%M:%S)] $(echo "$STATUS" | tail -4 | tr '\n' ' ')"
  case "$STATUS" in *FINISHED*) break ;; esac
done

echo "=== downloading results ==="
"${COLAB[@]}" download -s "$SESSION" /content/run.log "$OUT_DIR/$TAG.log"
tail -40 "$OUT_DIR/$TAG.log"
"${COLAB[@]}" download -s "$SESSION" "$REMOTE_OUT" "$OUT_DIR/$TAG.jsonl"
"${COLAB[@]}" download -s "$SESSION" "${REMOTE_OUT%.jsonl}.metrics.json" "$OUT_DIR/$TAG.metrics.json"
echo "Results in $OUT_DIR/$TAG.{jsonl,metrics.json,log}"
