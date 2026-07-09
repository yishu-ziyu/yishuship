#!/usr/bin/env bash
set -u

# Ensure user-installed binaries are on PATH.
_BOOTSTRAP="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/path-bootstrap.sh"
[ -f "$_BOOTSTRAP" ] && source "$_BOOTSTRAP"

# Ship phase guardrail — PreToolUse hook that enforces artifact access
# rules per pipeline phase and PM handoff completeness.
#
# Only active when .ship/ship-auto.local.md exists (yishuship workflow running).
# Only gates subagent calls (agent_id present), not the orchestrator itself.
#
# Rules:
#   QA phase:     block Read of review.md and plan.md (independence)
#   Review phase: block Write/Edit of source code (review finds, doesn't fix)
#   QA phase:     block Write/Edit of source code (QA reports, doesn't fix)
#   All phases:   block Write/Edit of .ship/ship-auto.local.md (orchestrator owns state)
#   All phases:   block subagent Write/Edit of source files without PM handoff (Rule 5)

INPUT=$(cat)

# Fast exit: only care about file-access tools (avoids jq on 90% of calls)
case "$INPUT" in
  *'"tool_name":"Read"'*|*'"tool_name":"Write"'*|*'"tool_name":"Edit"'*|*'"tool_name": "Read"'*|*'"tool_name": "Write"'*|*'"tool_name": "Edit"'*) ;;
  *) exit 0 ;;
esac

STATE_FILE=".ship/ship-auto.local.md"

# Only active during a Ship workflow
[ -f "$STATE_FILE" ] || exit 0

# Only gate subagents, not the orchestrator
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // ""')
[ -n "$AGENT_ID" ] || exit 0

# Resolve working directory for artifact path construction
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
[ -z "$CWD" ] && exit 0

TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')

# Extract file path from tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
[ -n "$FILE_PATH" ] || exit 0

# Read current phase
PHASE=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE" \
  | grep "^phase:" | head -1 \
  | sed 's/^phase: *//' | sed 's/^"\(.*\)"$/\1/' | tr -d '\r')

[ -n "$PHASE" ] || exit 0

# Resolve task_id for PM artifact checking
TASK_ID=$(echo "$INPUT" | jq -r '.tool_input._task_id // ""')
if [ -z "$TASK_ID" ]; then
  TASK_ID=$(grep "^task_id:" "$STATE_FILE" 2>/dev/null | head -1 | sed 's/^task_id: *//' | tr -d '\r')
fi
[ -n "$TASK_ID" ] || exit 0

# Normalize file path for matching
BASENAME=$(basename "$FILE_PATH")

block() {
  local reason="$1"
  jq -n --arg reason "$reason" '{"decision":"block","reason":$reason}'
}

# ── Rule 1: QA must not read review.md or plan.md ────────────
# Only applies during qa phase itself, NOT qa_fix (which runs dev-fix
# agent that legitimately needs plan.md for context).
if [ "$PHASE" = "qa" ]; then
  if [ "$TOOL" = "Read" ]; then
    case "$BASENAME" in
      review.md)
        block "[yishuship guardrail] QA phase cannot read review.md — breaks independence"
        exit 0
        ;;
      plan.md)
        block "[yishuship guardrail] QA phase cannot read plan.md — breaks independence"
        exit 0
        ;;
    esac
  fi
fi

# ── Rule 2: Review must not write source code ────────────────
if [ "$PHASE" = "review" ]; then
  if [ "$TOOL" = "Write" ] || [ "$TOOL" = "Edit" ]; then
    # Allow writing review artifacts
    case "$FILE_PATH" in
      *.ship/tasks/*/review.md) ;;  # review's own artifact
      *.ship/*) ;;                   # other .ship metadata
      *)
        block "[yishuship guardrail] Review phase cannot modify source code — report findings only"
        exit 0
        ;;
    esac
  fi
fi

# ── Rule 3: QA must not write source code ────────────────────
if [ "$PHASE" = "qa" ]; then
  if [ "$TOOL" = "Write" ] || [ "$TOOL" = "Edit" ]; then
    case "$FILE_PATH" in
      *.ship/tasks/*/qa/*) ;;  # QA's own artifacts
      *.ship/*) ;;              # other .ship metadata
      /tmp/*) ;;                # temp files
      *)
        block "[yishuship guardrail] QA phase cannot modify source code — report findings only"
        exit 0
        ;;
    esac
  fi
fi

# ── Rule 5: Subagent writes require PM handoff artifacts ─────
# Prevents engineering phases from starting before the PM handoff is
# complete. This catches agent bypasses of pm-gate.sh: an agent can
# dispatch a subagent with Write/Edit directly (not via Agent tool),
# which skips the PreToolUse gate that pm-gate.sh occupies.
#
# Only applies when agent_id is present (subagent), not the orchestrator.
has_pm_handoff() {
  local task_dir="$1"
  [ -f "$task_dir/product/00-product-type.json" ] || [ -f "$task_dir/product/00-product-type.yaml" ] || return 1
  [ -f "$task_dir/product/01-strategy.md" ] || return 1
  [ -f "$task_dir/product/03-problem-solution.md" ] || return 1
  [ -f "$task_dir/product/08-prd.md" ] || return 1
  [ -f "$task_dir/product/09-tech-project-plan.md" ] || return 1
  [ -f "$task_dir/delivery/design-spec.md" ] || return 1
  [ -f "$task_dir/plan/spec.md" ] || return 1
}

# Only gate Write/Edit to source files (not .ship metadata)
if [ "$TOOL" = "Write" ] || [ "$TOOL" = "Edit" ]; then
  case "$FILE_PATH" in
    *.ship/*|/tmp/*) ;;  # metadata and temp files are exempt
    *)
      # Check PM handoff
      TASK_DIR="$CWD/.ship/tasks/$TASK_ID"
      if [ -d "$TASK_DIR" ] && ! has_pm_handoff "$TASK_DIR"; then
        block "[yishuship guardrail] Cannot modify source files before PM handoff is complete. Run /yishuship:pm-intake and generate product/00-product-type.json, product/01-strategy.md, product/03-problem-solution.md, product/08-prd.md, product/09-tech-project-plan.md, delivery/design-spec.md, and plan/spec.md."
        exit 0
      fi
      ;;
  esac
fi

# ── Rule 4: No subagent may write the state file ─────────────
if [ "$TOOL" = "Write" ] || [ "$TOOL" = "Edit" ]; then
  case "$FILE_PATH" in
    *ship-auto.local.md)
      block "[yishuship guardrail] Only the orchestrator may modify .ship/ship-auto.local.md"
      exit 0
      ;;
  esac
fi

# ── Rule 6: Validate artifact checksums on Write/Edit to .ship/* ─
# Any Write or Edit targeting a .ship/* path must pass SHA256 integrity
# check. This prevents silent corruption of control files during
# subagent writes (e.g., a dev agent accidentally truncating run_state.yaml).
if [ "$TOOL" = "Write" ] || [ "$TOOL" = "Edit" ]; then
  case "$FILE_PATH" in
    *.ship/*)
      GUARDRAIL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
      VALIDATE="$GUARDRAIL_DIR/validate-artifacts.sh"
      if [ -f "$VALIDATE" ]; then
        CHECK_OUTPUT=$("$VALIDATE" --check --json 2>/dev/null)
        CHECK_RC=$?
        if [ $CHECK_RC -ne 0 ]; then
          # Extract reason from block JSON if available
          CHECK_REASON=$(echo "$CHECK_OUTPUT" | jq -r '.reason // "artifact integrity mismatch"' 2>/dev/null || echo "artifact integrity mismatch")
          block "[yishuship guardrail] $CHECK_REASON — .ship artifacts have been modified outside the integrity protocol. Use update-checksums.sh to re-baseline."
          exit 0
        fi
      fi
      ;;
  esac
fi

# All checks passed
exit 0
