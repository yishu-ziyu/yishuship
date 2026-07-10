#!/usr/bin/env bash
# yishuship plugin - SessionStart hint + structured activation status.
#
# Keep this hook deliberately small. It should only:
#   1. Inject structured YISHUSHIP_STATUS from bootstrap (disk facts).
#   2. Remind the host agent to consult /yishuship:use-yishuship for routing.
# Do not inject docs indexes, design pointers, memory, or production artifact
# content here.

set -u

# Drain stdin so hook callers can always pipe their JSON payload here.
INPUT=$(cat || true)
: "$INPUT"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

SYNC_STATUS=""
if [ -f "$SCRIPT_DIR/sync-local.sh" ]; then
  SYNC_STATUS=$(bash "$SCRIPT_DIR/sync-local.sh" --check 2>/dev/null | grep -E '^(repo_head|installed_plugin|skill_links|working_tree|update_needed):' || true)
fi

# Structured activation status (key: value). Prefer repo-local bootstrap.
BOOTSTRAP_STATUS=""
if [ -f "$SCRIPT_DIR/yishuship-bootstrap.sh" ]; then
  BOOTSTRAP_STATUS=$(bash "$SCRIPT_DIR/yishuship-bootstrap.sh" status 2>/dev/null || true)
fi

NEXT_ACTION=""
ACTIVE_TASK=""
SENSE_REPORT=""
if [ -n "$BOOTSTRAP_STATUS" ]; then
  NEXT_ACTION=$(printf '%s\n' "$BOOTSTRAP_STATUS" | grep -E '^next_action:' | head -1 | sed 's/^next_action:[[:space:]]*//' || true)
  ACTIVE_TASK=$(printf '%s\n' "$BOOTSTRAP_STATUS" | grep -E '^active_task:' | head -1 | sed 's/^active_task:[[:space:]]*//' || true)
  SENSE_REPORT=$(printf '%s\n' "$BOOTSTRAP_STATUS" | grep -E '^sense_report:' | head -1 | sed 's/^sense_report:[[:space:]]*//' || true)
fi

RESUME_LINE=""
case "$NEXT_ACTION" in
  resume)
    RESUME_LINE="- Active task detected (${ACTIVE_TASK:-unknown}). After enter/resume, show State Sense (sense_report) to the user before executing."
    ;;
  route)
    RESUME_LINE="- yishuship is enabled with no active task. Classify via /yishuship:use-yishuship, then enter state before business source edits."
    ;;
  bypass_ok)
    RESUME_LINE="- Project opts out of yishuship (enabled: false). Bypass is OK unless user asks for yishuship."
    ;;
  idle)
    RESUME_LINE="- No yishuship markers in this repo. Enter state only for delivery intents."
    ;;
  *)
    RESUME_LINE="- If the request is delivery-shaped, run bootstrap status/enter before business source edits."
    ;;
esac

PARTS="<YISHUSHIP_STATUS>
${BOOTSTRAP_STATUS:-enabled: unknown
active_task: none
phase: none
next_action: idle
reason: bootstrap unavailable}
</YISHUSHIP_STATUS>
<YISHUSHIP_STATE_SENSE>
${SENSE_REPORT:-unavailable}
After enter/resume, present this diagnosis to the user (where / gap / next / effect / how to verify / preview) before coding.
Do not give a naked next step without effect + presentation + preview.
</YISHUSHIP_STATE_SENSE>
<YISHUSHIP_ROUTING>
yishuship is available. At session start, read YISHUSHIP_STATUS (disk facts) and YISHUSHIP_STATE_SENSE.
- Consult /yishuship:use-yishuship when the request may need yishuship process.
- Delivery intents: enter state (bootstrap enter or equivalent) before business source edits; announce [yishuship] mode=... phase=... task=...
- L0 only for tiny fixes / pure Q&A, or explicit bypass; announce mode=L0_bypass.
- If the user names a specific /yishuship:* command, follow that command directly.
- Do not start /yishuship:auto unless the user explicitly asks for full end-to-end delivery.
${RESUME_LINE}
${SYNC_STATUS}
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
