#!/usr/bin/env bash
# Claude Code status line: keeps an existing status line, adds one yishuship line
# when the current project has an idea in progress.
#
#   settings.json → "statusLine": {"type": "command",
#     "command": "bash /path/to/yishuship/scripts/statusline.sh [existing-command ...]"}
input=$(cat)

if [ "$#" -gt 0 ]; then
  printf '%s' "$input" | "$@"
fi

dir=$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except ValueError:
    sys.exit()
print((d.get("workspace") or {}).get("current_dir") or d.get("cwd") or "")' 2>/dev/null)
[ -n "$dir" ] || exit 0

python3 "$(dirname "$0")/ideas.py" --status-line "$dir" 2>/dev/null
exit 0
