#!/bin/bash
# SessionStart hook for Claude Code cloud sessions: sets up the Colab CLI
# (google-colab-cli) authenticated via Application Default Credentials taken
# from the COLAB_ADC_JSON environment secret.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

ADC_PATH="$HOME/.config/gcloud/application_default_credentials.json"

# Credentials: only written when the secret is configured for this environment.
if [ -n "${COLAB_ADC_JSON:-}" ]; then
  mkdir -p "$(dirname "$ADC_PATH")"
  (umask 077 && printf '%s' "$COLAB_ADC_JSON" > "$ADC_PATH")
  chmod 600 "$ADC_PATH"
else
  echo "session-start: COLAB_ADC_JSON not set; skipping Colab credentials" >&2
fi

# google-colab-cli requires Python >= 3.12; the default python3 here is older.
export PATH="$HOME/.local/bin:$PATH"
if ! command -v colab >/dev/null 2>&1; then
  uv tool install --python 3.13 google-colab-cli
fi

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo 'export PATH="$HOME/.local/bin:$PATH"'
    [ -f "$ADC_PATH" ] && echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$ADC_PATH\""
  } >> "$CLAUDE_ENV_FILE"
fi
