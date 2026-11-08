#!/usr/bin/env bash
# Open the team monitor in its own window: a tmux split, a new macOS Terminal
# window, or (anywhere else) print the command to run in a second terminal.
# Usage: .claude/monitor/open.sh [team_monitor.py args...]   e.g. --demo
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="${CLAUDE_PROJECT_DIR:-$(cd "$DIR/../.." && pwd)}"
q() { printf '%q ' "$@"; }
CMD="python3 $(q "$DIR/team_monitor.py")--project $(q "$PROJECT")"
[ "$#" -gt 0 ] && CMD="$CMD $(q "$@")"
CMD="${CMD% }"
if [ -n "${TMUX:-}" ]; then
  tmux split-window -h -l 102 "$CMD" 2>/dev/null || tmux split-window -h "$CMD"
elif [ "$(uname)" = "Darwin" ] && command -v osascript >/dev/null; then
  osascript -e "tell application \"Terminal\" to do script \"${CMD//\"/\\\"}\"" \
            -e 'tell application "Terminal" to activate' >/dev/null
else
  echo "Run this in a second terminal (100+ columns wide):"
  echo "  $CMD"
fi
