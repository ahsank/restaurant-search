#!/bin/bash
# Keep a Colab GPU VM running `vllm serve` so interactive Approach 7 queries
# don't reinstall vLLM or reload the model each time: `start` pays the ~5–8 min
# setup once, then each `query` takes seconds (one prompt per restaurant, sent in
# parallel; vLLM caches each menu's prefix across queries).
#
# Usage:
#   research/colab/llm_server.sh start                 # Qwen2.5-7B on an L4
#   research/colab/llm_server.sh query seafood italian
#   research/colab/llm_server.sh query --all-restaurants vegan tacos
#   research/colab/llm_server.sh sync                  # re-upload code + data after local edits
#   research/colab/llm_server.sh status
#   research/colab/llm_server.sh stop                  # release the VM (it bills while running)
#
# Env: MODEL, GPU (default L4), SESSION (default llm-server), HF_TOKEN (gated models).
# The VM keeps billing until `stop`; Colab may also reclaim it after a long idle period.
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
GPU="${GPU:-L4}"
SESSION="${SESSION:-llm-server}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE=/content/restaurant-search
PORT=8000
COLAB=(colab --auth adc)
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

remote_py() {  # remote_py TIMEOUT CODE — run Python in the VM's kernel (client capped too)
  local timeout="$1"; shift
  printf '%s\n' "$1" | timeout "$((timeout + 60))" "${COLAB[@]}" exec -s "$SESSION" --timeout "$timeout"
}

download() {  # download REMOTE LOCAL — file API, survives dropped kernel connections
  timeout 90 "${COLAB[@]}" download -s "$SESSION" "$1" "$2" >/dev/null 2>&1
}

sync_code() {
  tar -C "$ROOT" --exclude='__pycache__' --exclude='research/results' \
    -czf "$WORK/code.tgz" research/lib research/search data/menus data/queries
  "${COLAB[@]}" upload -s "$SESSION" "$WORK/code.tgz" /content/code.tgz
  remote_py 120 "
import subprocess
subprocess.run('rm -rf $REMOTE && mkdir -p $REMOTE && tar -xzf /content/code.tgz -C $REMOTE', shell=True, check=True)
print('code synced')"
}

case "${1:-}" in
start)
  "${COLAB[@]}" new -s "$SESSION" --gpu "$GPU"
  # Release the VM if setup fails; disarmed once the server is up.
  trap 'rm -rf "$WORK"; echo "setup failed, stopping $SESSION"; "${COLAB[@]}" stop -s "$SESSION" || true' EXIT
  sync_code
  # Install + serve in one detached job; a retry skips it if the log already exists.
  for attempt in 1 2 3; do
    remote_py 60 "
import os, subprocess
if os.path.exists('/content/server.log'):
    print('already started')
else:
    env = dict(os.environ, HF_TOKEN='${HF_TOKEN:-}') if '${HF_TOKEN:-}' else dict(os.environ)
    subprocess.Popen('(pip install -q vllm && vllm serve $MODEL --port $PORT --max-model-len 12288 '
                     '--enable-prefix-caching --gpu-memory-utilization 0.90; echo SERVER_EXIT=\$?) '
                     '> /content/server.log 2>&1', shell=True, env=env, start_new_session=True)
    print('started')" || true
    download /content/server.log "$WORK/server.log" && break
    [ "$attempt" = 3 ] && { echo "ERROR: server job did not start"; exit 1; }
    echo "launch not confirmed (attempt $attempt), retrying"
  done
  echo "Installing vLLM and loading $MODEL (several minutes)..."
  while true; do
    sleep 30
    download /content/server.log "$WORK/server.log" || { echo "  (poll failed, retrying)"; continue; }
    if grep -q 'Application startup complete' "$WORK/server.log"; then break; fi
    if grep -q '^SERVER_EXIT=' "$WORK/server.log"; then
      echo "ERROR: server exited during startup:"; tr '\r' '\n' < "$WORK/server.log" | tail -30; exit 1
    fi
    echo "  $(tr '\r' '\n' < "$WORK/server.log" | grep -v '^\s*$' | tail -1 | cut -c1-150)"
  done
  trap 'rm -rf "$WORK"' EXIT
  echo "Server ready: $MODEL on $GPU (session $SESSION). Query with: $0 query <words>"
  ;;

query)
  shift
  [ $# -gt 0 ] || { echo "usage: $0 query [--all-restaurants] <query words>"; exit 2; }
  ARGS_JSON="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "$@")"
  remote_py 300 "
import json, subprocess
args = json.loads('''$ARGS_JSON''')
r = subprocess.run(['python', 'research/search/llm_search.py', '--server', 'http://localhost:$PORT', *args],
                   cwd='$REMOTE', capture_output=True, text=True)
print(r.stdout if r.returncode == 0 else r.stdout + r.stderr[-3000:])"
  ;;

sync)
  sync_code
  ;;

status)
  "${COLAB[@]}" status -s "$SESSION"
  remote_py 30 "
import urllib.request
try:
    print('server:', urllib.request.urlopen('http://localhost:$PORT/v1/models', timeout=10).read().decode()[:300])
except Exception as e:
    print('server not responding:', e)"
  ;;

stop)
  "${COLAB[@]}" stop -s "$SESSION"
  ;;

*)
  sed -n '2,17p' "$0"; exit 2
  ;;
esac
