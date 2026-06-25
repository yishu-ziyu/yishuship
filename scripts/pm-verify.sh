#!/usr/bin/env bash
set -u

# yishuship PM verify — Stop hook that checks PM artifacts before
# allowing session exit during a PM workflow.
#
# Logic:
#   1. No active PM state → allow exit
#   2. Check which PM stages are complete
#   3. If current stage artifacts missing → block exit with missing list
#   4. If all required stages complete → allow exit

INPUT=$(cat)

# Subagent bypass
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // ""')
[ -n "$AGENT_ID" ] && exit 0

# Check if PM workflow is active
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
[ -z "$CWD" ] && exit 0

STATE_FILE="$CWD/.ship/pm-state.yaml"
[ ! -f "$STATE_FILE" ] && exit 0

# Parse state
PM_PHASE=$(grep "^phase:" "$STATE_FILE" 2>/dev/null | head -1 | sed 's/^phase: *//' | tr -d '\r')
TASK_ID=$(grep "^task_id:" "$STATE_FILE" 2>/dev/null | head -1 | sed 's/^task_id: *//' | tr -d '\r')

[ -z "$TASK_ID" ] && exit 0

TASK_DIR="$CWD/.ship/tasks/$TASK_ID"
PM_DIR="$TASK_DIR/pm"

block_with_reason() {
  local reason="$1"
  jq -n \
    --arg reason "$reason" \
    --arg systemMessage "yishuship PM: 产出未完成，继续工作" \
    '{"decision":"block","reason":$reason,"systemMessage":$systemMessage}'
}

# ── Check required artifacts for current phase ──────
MISSING=""

case "$PM_PHASE" in
  discover)
    [ ! -f "$PM_DIR/01-discovery.md" ] && MISSING="$MISSING\n- 01-discovery.md（发现报告）"
    ;;
  define)
    [ ! -f "$PM_DIR/01-discovery.md" ] && MISSING="$MISSING\n- 01-discovery.md（发现报告）"
    [ ! -f "$PM_DIR/02-definition.md" ] && MISSING="$MISSING\n- 02-definition.md（产品定义）"
    ;;
  design)
    [ ! -f "$PM_DIR/02-definition.md" ] && MISSING="$MISSING\n- 02-definition.md（产品定义）"
    [ ! -f "$PM_DIR/03-design.md" ] && MISSING="$MISSING\n- 03-design.md（设计方案）"
    ;;
  validate)
    [ ! -f "$PM_DIR/03-design.md" ] && MISSING="$MISSING\n- 03-design.md（设计方案）"
    [ ! -f "$PM_DIR/04-validation.md" ] && MISSING="$MISSING\n- 04-validation.md（验证报告）"
    ;;
  complete)
    # All PM stages done, allow exit
    exit 0
    ;;
  *)
    exit 0
    ;;
esac

if [ -n "$MISSING" ]; then
  REASON="[yishuship PM] 当前阶段 ($PM_PHASE) 的产出物缺失：
$MISSING

请继续完成当前阶段的工作，或运行 /yishuship:pm-intake 继续。"
  block_with_reason "$REASON"
  exit 0
fi

# All checks passed
exit 0
