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

has_product_type_artifact() {
  [ -f "$PRODUCT_DIR/00-product-type.json" ] || [ -f "$PRODUCT_DIR/00-product-type.yaml" ]
}

# Full suite signal: auto scope_mode full/refactor, or research pack present.
is_full_product_suite() {
  if [ -f "$CWD/.ship/ship-auto.local.md" ]; then
    if grep -Eq '^scope_mode:[[:space:]]*(full|refactor)[[:space:]]*$' "$CWD/.ship/ship-auto.local.md" 2>/dev/null; then
      return 0
    fi
    if grep -Eq '^scope_mode:[[:space:]]*lite[[:space:]]*$' "$CWD/.ship/ship-auto.local.md" 2>/dev/null; then
      return 1
    fi
  fi
  # Standalone / no auto state: presence of full-suite research file implies full.
  [ -s "$PRODUCT_DIR/02-research.md" ]
}

has_go_decision_artifact() {
  [ -s "$PRODUCT_DIR/00c-go-decision.md" ] || return 1
  grep -qiE '^#{1,3}[[:space:]]*(Decision|决策)' "$PRODUCT_DIR/00c-go-decision.md" || return 1
  grep -qiE '(Go|No-Go|NoGo|Nogo|Shrink|缩刀|不做|通过)' "$PRODUCT_DIR/00c-go-decision.md" || return 1
  grep -qiE '^#{1,3}[[:space:]]*(Human approval|人工批准|人批准|Approval)' "$PRODUCT_DIR/00c-go-decision.md" || return 1
}

# Optional hard human-go for design: when auto state requires it and not approved.
human_go_blocks_design() {
  # Skip if auto explicitly disabled the gate.
  if [ -f "$CWD/.ship/ship-auto.local.md" ]; then
    if grep -Eq '^require_human_go:[[:space:]]*(false|0|no|off)[[:space:]]*$' "$CWD/.ship/ship-auto.local.md" 2>/dev/null; then
      return 1
    fi
  fi
  # Env override for CI / benchmarks.
  case "${YISHUSHIP_REQUIRE_HUMAN_GO:-true}" in
    0|false|False|FALSE|no|No|NO|off|Off|OFF) return 1 ;;
  esac
  # Only enforce when an auto run is active (standalone design may still require 00c file).
  [ -f "$CWD/.ship/ship-auto.local.md" ] || return 1
  local f="$PRODUCT_DIR/00c-go-decision.md"
  [ -s "$f" ] || return 0
  if grep -qiE 'status:[[:space:]]*(approved|yes|true|已批准|通过)' "$f"; then
    return 1
  fi
  if grep -qiE '(approved_by|批准人|approved by):[[:space:]]*(user|human|我|owner)' "$f"; then
    return 1
  fi
  return 0
}

has_v2_product_handoff() {
  # Align with Engineering Gate minimum (lite-capable handoff).
  has_product_type_artifact && \
  [ -s "$PRODUCT_DIR/00b-scope-challenge.md" ] && \
  has_go_decision_artifact && \
  [ -f "$PRODUCT_DIR/01-strategy.md" ] && \
  [ -f "$PRODUCT_DIR/03-problem-solution.md" ] && \
  [ -f "$PRODUCT_DIR/08-prd.md" ] && \
  [ -f "$PRODUCT_DIR/09-tech-project-plan.md" ] && \
  [ -s "$TASK_DIR/control/matt-upstream.md" ] && \
  [ -f "$DELIVERY_DIR/design-spec.md" ] && \
  [ -f "$TASK_DIR/plan/spec.md" ] || return 1

  # Full suite must also have peer cross-review of product inputs/outputs.
  if is_full_product_suite; then
    [ -s "$TASK_DIR/control/peer-review.md" ] || return 1
  fi
  return 0
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
    block "[yishuship PM gate] /yishuship:design or /yishuship:auto needs V2 handoff: product/00, 00b-scope-challenge, 00c-go-decision (Decision + Human approval), 01, 03, 08 (Success Metrics/Assumptions/Kill Criteria), 09, control/matt-upstream.md, delivery/design-spec.md, plan/spec.md. Full suite also requires control/peer-review.md (host disposition). Old tasks can pass with pm/01-discovery.md."
    exit 0
  fi
  if human_go_blocks_design; then
    block "[yishuship PM gate] Human Go not approved. Set product/00c-go-decision.md Human approval status: approved, or run: bash scripts/auto-orchestrate.sh approve_go"
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
