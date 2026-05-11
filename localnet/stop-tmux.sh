#!/usr/bin/env bash
set -euo pipefail

SESSION="localnet"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCALNET_DIR="$REPO_ROOT/localnet"

command -v tmux >/dev/null || { echo "tmux not found" >&2; exit 1; }
command -v docker >/dev/null || { echo "docker not found" >&2; exit 1; }

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Killing tmux session '$SESSION'..."
  tmux kill-session -t "$SESSION"
else
  echo "No tmux session '$SESSION' to kill."
fi

echo "Stopping docker compose..."
(cd "$LOCALNET_DIR" && docker compose down)
