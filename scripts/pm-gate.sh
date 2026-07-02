#!/usr/bin/env bash
set -u

# yishuship PM gate — PreToolUse hook that enforces PM artifacts exist
# before engineering phases can begin.
#
# Rules (V2 preference with V1 fallback):
#   /yishuship:design requires V2 product handoff OR legacy pm/01-discovery.md
#   /yishuship:dev    requires V2 product handoff OR legacy pm/02-definition.md
#   /yishuship:auto   requires V2 product handoff OR legacy pm/01-discovery.md
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
PRODUCT_DIR="$TASK_DIR/product"
DELIVERY_DIR="$TASK_DIR/delivery"

has_v2_product_handoff() {
  [ -f "$PRODUCT_DIR/00-product-type.yaml" ] && \
  [ -f "$PRODUCT_DIR/01-strategy.md" ] && \
  [ -f "$PRODUCT_DIR/03-problem-solution.md" ] && \
  [ -f "$PRODUCT_DIR/08-prd.md" ] && \
  [ -f "$PRODUCT_DIR/09-tech-project-plan.md" ] && \
  [ -f "$DELIVERY_DIR/design-spec.md" ] && \
  [ -f "$TASK_DIR/plan/spec.md" ]
}

has_legacy_discovery() {
  [ -f "$PM_DIR/01-discovery.md" ]
}

has_legacy_definition() {
  [ -f "$PM_DIR/02-definition.md" ]
}

# Extract the skill being invoked from the agent prompt
AGENT_PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""')

block() {
  local reason="$1"
  jq -n --arg reason "$reason" '{"decision":"block","reason":$reason}'
}

# ── Rule 1: Design requires product type (V2) or discovery (V1) ──────────────
if echo "$AGENT_PROMPT" | grep -q "yishuship:design\|yishuship:auto"; then
  if ! has_v2_product_handoff && ! has_legacy_discovery; then
    block "[yishuship PM gate] /yishuship:design or /yishuship:auto requires a complete V2 product handoff. Please run /yishuship:pm-intake and generate at least product/00-product-type.yaml, product/01-strategy.md, product/03-problem-solution.md, product/08-prd.md, product/09-tech-project-plan.md, delivery/design-spec.md, and plan/spec.md. Old tasks can pass with pm/01-discovery.md."
    exit 0
  fi
fi

# ── Rule 2: Dev requires design-spec (V2) or definition (V1) ────────────────
if echo "$AGENT_PROMPT" | grep -q "yishuship:dev"; then
  if ! has_v2_product_handoff && ! has_legacy_definition; then
    block "[yishuship PM gate] /yishuship:dev needs executable product handoff, PRD and technical project plan. Old tasks can pass with pm/02-definition.md."
    exit 0
  fi
fi

# All checks passed
exit 0
