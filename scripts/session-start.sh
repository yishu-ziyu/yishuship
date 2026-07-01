#!/usr/bin/env bash
# yishuship plugin - minimal SessionStart hint.
#
# Keep this hook deliberately small. It should only remind the host agent to
# consult /yishuship:use-yishuship for yishuship routing. Do not inject docs
# indexes, design pointers, memory, or production artifact content here.

set -u

# Drain stdin so hook callers can always pipe their JSON payload here.
INPUT=$(cat || true)
: "$INPUT"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SYNC_STATUS=""
if [ -f "$SCRIPT_DIR/sync-local.sh" ]; then
  SYNC_STATUS=$(bash "$SCRIPT_DIR/sync-local.sh" --check 2>/dev/null | grep -E '^(repo_head|installed_plugin|skill_links|working_tree|update_needed):' || true)
fi

PARTS="<YISHUSHIP_ROUTING>
yishuship is available in this repo. At the beginning of the session, consult /yishuship:use-yishuship when the user's request may need yishuship process.
- If the user names a specific /yishuship:* command, follow that command directly.
- If the request is unrelated to software delivery, do not use yishuship.
- Do not start /yishuship:auto unless the user explicitly asks for full end-to-end delivery.
$SYNC_STATUS
</YISHUSHIP_ROUTING>"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
  jq -n --arg context "$PARTS" '{additional_context: $context}'
else
  jq -n --arg context "$PARTS" '{
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: $context
    }
  }'
fi
