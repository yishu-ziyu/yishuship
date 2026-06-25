#!/usr/bin/env bash
set -u

# yishuship PM gate — PreToolUse hook that enforces PM artifacts exist
# before engineering phases can begin.
#
# Rules:
#   /yishuship:design requires pm/01-discovery.md (discovery complete)
#   /yishuship:dev    requires pm/02-definition.md (definition complete)
#   /yishuship:auto   requires pm/01-discovery.md (at minimum)
#
# Only active when .ship/pm-state.yaml exists (PM workflow running).

INPUT=$(cat)

# Fast exit: only care about Agent tool calls (skill invocations)
case "$INPUT" in
  *'"tool_name":"Agent"'*|*'"tool_name": "Agent"'*) ;;
  *) exit 0 ;;
esac

# Check if PM workflow is active
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
[ -z "$CWD" ] && exit 0

STATE_FILE="$CWD/.ship/pm-state.yaml"
[ ! -f "$STATE_FILE" ] && exit 0

# Read current PM phase and task_id
PM_PHASE=$(grep "^phase:" "$STATE_FILE" 2>/dev/null | head -1 | sed 's/^phase: *//' | tr -d '\r')
TASK_ID=$(grep "^task_id:" "$STATE_FILE" 2>/dev/null | head -1 | sed 's/^task_id: *//' | tr -d '\r')

[ -z "$TASK_ID" ] && exit 0

TASK_DIR="$CWD/.ship/tasks/$TASK_ID"
PM_DIR="$TASK_DIR/pm"

# Extract the skill being invoked from the agent prompt
AGENT_PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""')

block() {
  local reason="$1"
  jq -n --arg reason "$reason" '{"decision":"block","reason":$reason}'
}

# ── Rule 1: Design requires discovery ──────────────
if echo "$AGENT_PROMPT" | grep -q "yishuship:design\|yishuship:auto"; then
  if [ ! -f "$PM_DIR/01-discovery.md" ]; then
    block "[yishuship PM gate] /yishuship:design 需要先完成发现阶段。请先运行 /yishuship:pm-intake 完成 01-discovery.md"
    exit 0
  fi
fi

# ── Rule 2: Dev requires definition ────────────────
if echo "$AGENT_PROMPT" | grep -q "yishuship:dev"; then
  if [ ! -f "$PM_DIR/02-definition.md" ]; then
    block "[yishuship PM gate] /yishuship:dev 需要先完成定义阶段。请先运行 /yishuship:pm-intake 完成 02-definition.md"
    exit 0
  fi
fi

# All checks passed
exit 0
