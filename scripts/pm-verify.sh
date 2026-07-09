#!/usr/bin/env bash
set -u

# yishuship PM verify — Stop hook that checks PM artifacts before
# allowing session exit during a PM workflow.
#
# Logic:
#   1. No active PM state → allow exit
#   2. Check which PM stages are complete (Prefer V2, fallback V1)
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
PRODUCT_DIR="$TASK_DIR/product"
DELIVERY_DIR="$TASK_DIR/delivery"
PLAN_DIR="$TASK_DIR/plan"

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
  # V2 phases
  product-type)
    [ ! -f "$PRODUCT_DIR/00-product-type.json" ] && [ ! -f "$PRODUCT_DIR/00-product-type.yaml" ] && MISSING="$MISSING\n- product/00-product-type.json"
    ;;
  strategy)
    [ ! -f "$PRODUCT_DIR/00-product-type.json" ] && [ ! -f "$PRODUCT_DIR/00-product-type.yaml" ] && MISSING="$MISSING\n- product/00-product-type.json"
    [ ! -f "$PRODUCT_DIR/01-strategy.md" ] && MISSING="$MISSING\n- product/01-strategy.md"
    ;;
  research)
    [ ! -f "$PRODUCT_DIR/02-research.md" ] && MISSING="$MISSING\n- product/02-research.md"
    ;;
  problem-solution)
    [ ! -f "$PRODUCT_DIR/03-problem-solution.md" ] && MISSING="$MISSING\n- product/03-problem-solution.md"
    [ ! -f "$PRODUCT_DIR/04-product-blueprint.md" ] && MISSING="$MISSING\n- product/04-product-blueprint.md"
    ;;
  product-spec)
    [ ! -f "$PRODUCT_DIR/05-model-flow-role.md" ] && MISSING="$MISSING\n- product/05-model-flow-role.md"
    [ ! -f "$PRODUCT_DIR/06-experience-spec.md" ] && MISSING="$MISSING\n- product/06-experience-spec.md"
    [ ! -f "$PRODUCT_DIR/07-data-permission-analytics.md" ] && MISSING="$MISSING\n- product/07-data-permission-analytics.md"
    [ ! -f "$PRODUCT_DIR/08-prd.md" ] && MISSING="$MISSING\n- product/08-prd.md"
    ;;
  tech-project-plan)
    [ ! -f "$PRODUCT_DIR/09-tech-project-plan.md" ] && MISSING="$MISSING\n- product/09-tech-project-plan.md"
    ;;
  handoff)
    [ ! -f "$DELIVERY_DIR/design-spec.md" ] && [ ! -f "$PLAN_DIR/spec.md" ] && MISSING="$MISSING\n- delivery/design-spec.md or plan/spec.md"
    ;;

  # Legacy phases
  discover)
    [ ! -f "$PM_DIR/01-discovery.md" ] && MISSING="$MISSING\n- pm/01-discovery.md"
    ;;
  define)
    [ ! -f "$PM_DIR/01-discovery.md" ] && MISSING="$MISSING\n- pm/01-discovery.md"
    [ ! -f "$PM_DIR/02-definition.md" ] && MISSING="$MISSING\n- pm/02-definition.md"
    ;;
  design)
    [ ! -f "$PM_DIR/02-definition.md" ] && MISSING="$MISSING\n- pm/02-definition.md"
    [ ! -f "$PM_DIR/03-design.md" ] && MISSING="$MISSING\n- pm/03-design.md"
    ;;
  validate)
    [ ! -f "$PM_DIR/03-design.md" ] && MISSING="$MISSING\n- pm/03-design.md"
    [ ! -f "$PM_DIR/04-validation.md" ] && MISSING="$MISSING\n- pm/04-validation.md"
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
