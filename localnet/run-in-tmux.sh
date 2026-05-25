#!/usr/bin/env bash
set -euo pipefail

SESSION="localnet"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCALNET_DIR="$REPO_ROOT/localnet"

command -v tmux >/dev/null || { echo "tmux not found" >&2; exit 1; }
command -v docker >/dev/null || { echo "docker not found" >&2; exit 1; }
command -v uv >/dev/null || { echo "uv not found" >&2; exit 1; }

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session '$SESSION' already exists. Run: tmux kill-session -t $SESSION" >&2
  exit 1
fi

if [ ! -f "$LOCALNET_DIR/.env" ]; then
  cp "$LOCALNET_DIR/.env.example" "$LOCALNET_DIR/.env"
  echo "Created localnet/.env from .env.example"
fi

echo "Starting docker compose..."
(cd "$LOCALNET_DIR" && docker compose up -d --wait)

echo "Syncing validator deps..."
(cd "$REPO_ROOT/validator" && uv sync)
echo "Syncing miner deps..."
(cd "$REPO_ROOT/miner" && uv sync)

echo "Running bootstrap..."
uv run "$LOCALNET_DIR/bootstrap.py"

tmux new-session -d -s "$SESSION" -n main \
  -c "$REPO_ROOT/validator" \
  "uv run validator --env-file ../localnet/.env"

tmux split-window -h -t "$SESSION:main" \
  -c "$REPO_ROOT/miner" \
  "uv run miner -n 1"

tmux select-pane -t "$SESSION:main.0"

if [ -t 1 ]; then
  tmux attach -t "$SESSION"
else
  echo "Session '$SESSION' started. Attach with: tmux attach -t $SESSION"
fi
