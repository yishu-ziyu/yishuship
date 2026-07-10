#!/usr/bin/env bash
# yishuship Activation Layer bootstrap.
#
# Detect enablement, report structured status, and enter/resume task state.
# Output is machine-readable key: value lines for SessionStart injection.
#
# Usage:
#   bash scripts/yishuship-bootstrap.sh status
#   bash scripts/yishuship-bootstrap.sh enter [reason]
#
# See: docs/decisions/DEC-0005-activation-contract.md

set -u

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

# Anchor at git root when available so .ship/ is never forked under a subdir.
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT" || exit 1

SHIP_DIR=".ship"
CONFIG_FILE="$SHIP_DIR/config.yaml"
ENABLED_MARKER="$SHIP_DIR/enabled"
AUTO_STATE="$SHIP_DIR/ship-auto.local.md"
PM_STATE="$SHIP_DIR/pm-state.yaml"
TASKS_DIR="$SHIP_DIR/tasks"

emit() {
  local key="$1" value="$2"
  printf '%s: %s\n' "$key" "$value"
}

yaml_get() {
  # Read a simple top-level key: value from a yaml-ish file.
  local file="$1" key="$2"
  [ -f "$file" ] || return 0
  # Prefer unquoted value; strip surrounding quotes and CR.
  grep -E "^${key}:" "$file" 2>/dev/null \
    | head -1 \
    | sed "s/^${key}:[[:space:]]*//" \
    | sed 's/^["'\'']//;s/["'\'']$//' \
    | tr -d '\r' || true
}

frontmatter_get() {
  local file="$1" key="$2"
  [ -f "$file" ] || return 0
  sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$file" 2>/dev/null \
    | grep -E "^${key}:" \
    | head -1 \
    | sed "s/^${key}:[[:space:]]*//" \
    | sed 's/^["'\'']//;s/["'\'']$//' \
    | tr -d '\r' || true
}

is_active_run_state() {
  local file="$1"
  [ -f "$file" ] || return 1
  local active status
  active="$(yaml_get "$file" "active")"
  status="$(yaml_get "$file" "status")"
  if [ "$active" = "true" ]; then
    return 0
  fi
  case "$status" in
    running|in_progress|blocked) return 0 ;;
  esac
  return 1
}

# Return the newest active run_state path, or empty.
find_active_run_state() {
  local best="" best_mtime=0 mtime f
  [ -d "$TASKS_DIR" ] || return 0
  # Portable mtime: prefer stat -f (macOS), fall back to stat -c (GNU).
  for f in "$TASKS_DIR"/*/control/run_state.yaml; do
    [ -f "$f" ] || continue
    is_active_run_state "$f" || continue
    mtime=0
    if mtime=$(stat -f %m "$f" 2>/dev/null); then
      :
    elif mtime=$(stat -c %Y "$f" 2>/dev/null); then
      :
    else
      mtime=0
    fi
    if [ -z "$best" ] || [ "$mtime" -ge "$best_mtime" ]; then
      best="$f"
      best_mtime="$mtime"
    fi
  done
  printf '%s' "$best"
}

config_enabled_value() {
  # Prints true | false | unset
  if [ ! -f "$CONFIG_FILE" ]; then
    printf 'unset'
    return 0
  fi
  local v
  v="$(yaml_get "$CONFIG_FILE" "enabled")"
  case "$v" in
    true|True|TRUE|yes|Yes|1) printf 'true' ;;
    false|False|FALSE|no|No|0) printf 'false' ;;
    *)
      # File exists without explicit false → treat as enabled.
      printf 'true'
      ;;
  esac
}

detect_enabled() {
  # Echo true|false. Explicit config false wins over soft markers
  # unless an active task is already on disk (resume still required).
  local cfg
  cfg="$(config_enabled_value)"
  if [ "$cfg" = "false" ]; then
    printf 'false'
    return 0
  fi
  if [ "$cfg" = "true" ]; then
    printf 'true'
    return 0
  fi
  if [ -f "$ENABLED_MARKER" ]; then
    printf 'true'
    return 0
  fi
  if [ -f "$AUTO_STATE" ]; then
    printf 'true'
    return 0
  fi
  if [ -f "$PM_STATE" ]; then
    printf 'true'
    return 0
  fi
  local rs
  rs="$(find_active_run_state)"
  if [ -n "$rs" ]; then
    printf 'true'
    return 0
  fi
  # Any historical task run_state also counts as project having used yishuship.
  if [ -d "$TASKS_DIR" ]; then
    for f in "$TASKS_DIR"/*/control/run_state.yaml; do
      if [ -f "$f" ]; then
        printf 'true'
        return 0
      fi
    done
  fi
  printf 'false'
}

resolve_active_task() {
  # Prints: task_id|phase|source  or empty if none.
  local task_id phase source rs

  # 1) ship-auto.local.md wins when it points at a real task.
  if [ -f "$AUTO_STATE" ]; then
    task_id="$(frontmatter_get "$AUTO_STATE" "task_id")"
    phase="$(frontmatter_get "$AUTO_STATE" "phase")"
    local auto_active
    auto_active="$(frontmatter_get "$AUTO_STATE" "active")"
    if [ -n "$task_id" ] && [ -d "$TASKS_DIR/$task_id" ]; then
      if [ "$auto_active" != "false" ]; then
        [ -n "$phase" ] || phase="$(yaml_get "$TASKS_DIR/$task_id/control/run_state.yaml" "current_phase")"
        [ -n "$phase" ] || phase="unknown"
        printf '%s|%s|ship-auto' "$task_id" "$phase"
        return 0
      fi
    fi
  fi

  # 2) Newest active run_state.yaml
  rs="$(find_active_run_state)"
  if [ -n "$rs" ]; then
    task_id="$(yaml_get "$rs" "task_id")"
    phase="$(yaml_get "$rs" "current_phase")"
    if [ -z "$task_id" ]; then
      # Infer from path: .ship/tasks/<id>/control/run_state.yaml
      task_id="$(printf '%s' "$rs" | sed -n 's|.*/tasks/\([^/]*\)/control/run_state.yaml|\1|p')"
    fi
    [ -n "$phase" ] || phase="unknown"
    if [ -n "$task_id" ]; then
      printf '%s|%s|run_state' "$task_id" "$phase"
      return 0
    fi
  fi

  # 3) pm-state.yaml if task dir still present and not complete-without-run_state
  if [ -f "$PM_STATE" ]; then
    task_id="$(yaml_get "$PM_STATE" "task_id")"
    phase="$(yaml_get "$PM_STATE" "phase")"
    if [ -n "$task_id" ] && [ -d "$TASKS_DIR/$task_id" ]; then
      if [ -f "$TASKS_DIR/$task_id/control/run_state.yaml" ]; then
        if is_active_run_state "$TASKS_DIR/$task_id/control/run_state.yaml"; then
          phase="$(yaml_get "$TASKS_DIR/$task_id/control/run_state.yaml" "current_phase")"
          [ -n "$phase" ] || phase="unknown"
          printf '%s|%s|pm-state' "$task_id" "$phase"
          return 0
        fi
      elif [ -n "$phase" ] && [ "$phase" != "complete" ]; then
        [ -n "$phase" ] || phase="unknown"
        printf '%s|%s|pm-state' "$task_id" "$phase"
        return 0
      fi
    fi
  fi

  return 0
}

cmd_status() {
  local enabled active_task phase next_action reason resolved task_id
  enabled="$(detect_enabled)"
  active_task="none"
  phase="none"
  next_action="idle"
  reason="no yishuship markers"

  resolved="$(resolve_active_task || true)"
  if [ -n "${resolved:-}" ]; then
    task_id="${resolved%%|*}"
    local rest phase_src
    rest="${resolved#*|}"
    phase="${rest%%|*}"
    phase_src="${rest#*|}"
    active_task="$task_id"
    enabled="true"
    next_action="resume"
    reason="active task via ${phase_src}"
  else
    local cfg
    cfg="$(config_enabled_value)"
    if [ "$cfg" = "false" ]; then
      enabled="false"
      next_action="bypass_ok"
      reason="config enabled: false"
    elif [ "$enabled" = "true" ]; then
      next_action="route"
      reason="enabled, no active task - classify then enter"
    else
      next_action="idle"
      reason="not enabled in this repo"
    fi
  fi

  emit "enabled" "$enabled"
  emit "active_task" "$active_task"
  emit "phase" "$phase"
  emit "next_action" "$next_action"
  emit "reason" "$reason"
}

slugify() {
  local raw="$1"
  printf '%s' "$raw" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]/-/g' \
    | sed 's/--*/-/g' \
    | sed 's/^-//;s/-$//' \
    | cut -c1-60
}

ensure_task_dirs() {
  local task_dir="$1"
  mkdir -p \
    "$task_dir/input/attachments" \
    "$task_dir/product" \
    "$task_dir/delivery" \
    "$task_dir/growth" \
    "$task_dir/control" \
    "$task_dir/plan" \
    "$task_dir/e2e" \
    "$task_dir/qa"
}

write_run_state_if_missing() {
  local task_id="$1" phase="${2:-intake}" status="${3:-running}"
  local task_dir="$TASKS_DIR/$task_id"
  local rs="$task_dir/control/run_state.yaml"
  ensure_task_dirs "$task_dir"
  if [ -f "$rs" ]; then
    return 0
  fi
  {
    printf 'task_id: %s\n' "$task_id"
    printf 'active: true\n'
    printf 'current_phase: %s\n' "$phase"
    printf 'status: %s\n' "$status"
    printf 'updated_at: "%s"\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  } > "$rs"
}

cmd_enter() {
  local reason="${1:-session-enter}"
  local resolved task_id phase

  resolved="$(resolve_active_task || true)"
  if [ -n "${resolved:-}" ]; then
    task_id="${resolved%%|*}"
    local rest
    rest="${resolved#*|}"
    phase="${rest%%|*}"
    write_run_state_if_missing "$task_id" "${phase:-intake}" "running"
    emit "action" "reuse"
    emit "task_id" "$task_id"
    emit "phase" "$(yaml_get "$TASKS_DIR/$task_id/control/run_state.yaml" "current_phase")"
    emit "task_dir" "$TASKS_DIR/$task_id"
    return 0
  fi

  task_id="$(slugify "$reason")"
  if [ -z "$task_id" ]; then
    task_id="$(date +%Y%m%d-%H%M%S)"
  fi
  # Avoid clobbering a completed historical task with the same slug.
  if [ -d "$TASKS_DIR/$task_id" ] && [ -f "$TASKS_DIR/$task_id/control/run_state.yaml" ]; then
    if ! is_active_run_state "$TASKS_DIR/$task_id/control/run_state.yaml"; then
      task_id="${task_id}-$(date +%Y%m%d-%H%M%S)"
    fi
  fi

  ensure_task_dirs "$TASKS_DIR/$task_id"

  if [ ! -f "$TASKS_DIR/$task_id/input/idea.md" ]; then
    {
      printf '# Idea\n\n'
      printf '%s\n' "$reason"
    } > "$TASKS_DIR/$task_id/input/idea.md"
  fi
  if [ ! -f "$TASKS_DIR/$task_id/input/requirement.md" ]; then
    {
      printf '# Requirement\n\n'
      printf '## Original Input\n\n'
      printf '%s\n' "$reason"
    } > "$TASKS_DIR/$task_id/input/requirement.md"
  fi

  write_run_state_if_missing "$task_id" "intake" "running"

  # Soft enablement marker so subsequent status sees the project as enabled
  # even if config.yaml was never created.
  if [ ! -f "$CONFIG_FILE" ] && [ ! -f "$ENABLED_MARKER" ]; then
    mkdir -p "$SHIP_DIR"
    printf 'enabled: true\n' > "$CONFIG_FILE"
  fi

  emit "action" "create"
  emit "task_id" "$task_id"
  emit "phase" "intake"
  emit "task_dir" "$TASKS_DIR/$task_id"
}

usage() {
  cat <<'EOF'
Usage:
  yishuship-bootstrap.sh status
  yishuship-bootstrap.sh enter [reason]
EOF
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    status)
      cmd_status
      ;;
    enter)
      shift
      cmd_enter "${*:-session-enter}"
      ;;
    -h|--help|help|"")
      usage
      exit 1
      ;;
    *)
      emit "error" "unknown command: $cmd"
      usage
      exit 1
      ;;
  esac
}

main "$@"
