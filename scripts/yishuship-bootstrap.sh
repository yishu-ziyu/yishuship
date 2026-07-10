#!/usr/bin/env bash
# yishuship Activation Layer bootstrap.
#
# Detect enablement, report structured status + human State Sense, and
# enter/resume task state.
#
# Output is machine-readable key: value lines for SessionStart injection.
# Status also emits sense_* fields (human diagnosis + causal next step).
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

# Non-empty file?
file_ok() {
  local f="$1"
  [ -f "$f" ] && [ -s "$f" ]
}

# Probe task artifacts. Sets globals: SENSE_HAVE SENSE_MISSING SENSE_STAGE
# SENSE_HAVE / SENSE_MISSING are comma-separated short labels.
probe_task_artifacts() {
  local task_id="$1"
  local td="$TASKS_DIR/$task_id"
  local have="" miss=""

  SENSE_HAVE=""
  SENSE_MISSING=""
  SENSE_STAGE="unknown"

  [ -d "$td" ] || {
    SENSE_MISSING="task_dir"
    SENSE_STAGE="none"
    return 0
  }

  # Input
  if file_ok "$td/input/idea.md" || file_ok "$td/input/requirement.md"; then
    have="${have}input,"
  else
    miss="${miss}input,"
  fi

  # PM handoff (V2): product type + PRD + delivery bridge + plan spec
  local pm_ok=0
  if file_ok "$td/product/00-product-type.json" || file_ok "$td/product/00-product-type.yaml"; then
    pm_ok=$((pm_ok + 1))
  fi
  if file_ok "$td/product/08-prd.md"; then
    pm_ok=$((pm_ok + 1))
  fi
  if file_ok "$td/delivery/design-spec.md"; then
    pm_ok=$((pm_ok + 1))
  fi
  if file_ok "$td/plan/spec.md"; then
    pm_ok=$((pm_ok + 1))
  fi
  if [ "$pm_ok" -ge 3 ]; then
    have="${have}pm_handoff,"
  else
    miss="${miss}pm_handoff,"
  fi

  # Engineering plan
  if file_ok "$td/plan/plan.md" || file_ok "$td/plan/peer-spec.md"; then
    have="${have}plan,"
  else
    miss="${miss}plan,"
  fi

  # E2E evidence
  if file_ok "$td/e2e/report.md" || dir_has_any "$td/e2e"; then
    have="${have}e2e,"
  else
    miss="${miss}e2e,"
  fi

  # QA evidence
  if dir_has_any "$td/qa"; then
    have="${have}qa,"
  else
    miss="${miss}qa,"
  fi

  # Strip trailing commas
  have="${have%,}"
  miss="${miss%,}"
  SENSE_HAVE="${have:-none}"
  SENSE_MISSING="${miss:-none}"

  # Coarse lifecycle stage from artifacts (independent of phase label)
  if [[ ",$have," == *",qa,"* ]] || [[ ",$have," == *",e2e,"* && ",$have," == *",plan,"* && ",$have," == *",pm_handoff,"* ]]; then
    if [[ ",$miss," == *",e2e,"* ]]; then
      SENSE_STAGE="built_needs_verify"
    elif [[ ",$miss," == *",qa,"* ]]; then
      SENSE_STAGE="verified_partial"
    else
      SENSE_STAGE="ready_to_ship"
    fi
  elif [[ ",$have," == *",plan,"* && ",$have," == *",pm_handoff,"* ]]; then
    SENSE_STAGE="designed"
  elif [[ ",$have," == *",pm_handoff,"* ]]; then
    SENSE_STAGE="product_defined"
  elif [[ ",$have," == *",input,"* ]]; then
    SENSE_STAGE="idea_only"
  else
    SENSE_STAGE="empty"
  fi
}

dir_has_any() {
  local d="$1"
  [ -d "$d" ] || return 1
  [ -n "$(find "$d" -maxdepth 1 -type f ! -name '.*' 2>/dev/null | head -1)" ]
}

# Map phase + missing → one skill and causal chain (effect / presentation / preview).
# Sets: NEXT_SKILL NEXT_EFFECT NEXT_PRESENT NEXT_PREVIEW WHERE_ZH MISSING_ZH
build_sense_narrative() {
  local phase="$1" next_action="$2" task_id="$3" missing="${4:-none}" stage="${5:-unknown}"
  local skill effect present preview where miss_zh

  skill="/yishuship:use-yishuship"
  effect="明确本任务该走哪条交付路径，避免直接开写"
  present="路由报告卡：Intent / Route / Reason"
  preview="先只路由、不改业务代码；你确认路线后再执行"
  where="未知"
  miss_zh="未评估"

  case "$next_action" in
    idle)
      where="本仓库未启用 yishuship，当前无交付状态机"
      miss_zh="无 .ship 启用标记、无进行中任务"
      skill="(无需 skill，或先启用 .ship/config.yaml)"
      effect="启用后，后续交付请求可被进态与闸门约束"
      present="再跑 bootstrap status，应看到 enabled: true"
      preview="可先 echo 'enabled: true' > .ship/config.yaml 再 status"
      ;;
    bypass_ok)
      where="项目显式关闭 yishuship（enabled: false）"
      miss_zh="流程约束已旁路（按配置）"
      skill="(旁路模式，除非用户要求开启)"
      effect="继续当普通助手；不会写 .ship 任务态"
      present="无 yishuship 宣告"
      preview="若要恢复，把 config enabled 改为 true"
      ;;
    route)
      where="yishuship 已启用，但还没有进行中的任务"
      miss_zh="缺 active task / run_state"
      skill="/yishuship:use-yishuship → enter"
      effect="创建任务态后，后续改动可被 phase 与产物约束"
      present="出现 task_id + [yishuship] mode=... 宣告"
      preview="可先 bootstrap enter \"一句话目标\"，不改业务代码"
      ;;
    resume)
      where="有进行中任务「${task_id}」，当前 phase=${phase}，粗阶段=${stage}"
      case "$missing" in
        none|"") miss_zh="关键产物齐全" ;;
        *) miss_zh="缺：$(echo "$missing" | tr ',' '、')" ;;
      esac

      case "$phase" in
        complete)
          skill="/yishuship:handoff 或结束任务"
          effect="任务收口：PR/交接或标记完成，避免无限开新 phase"
          present="handoff 产物或 run_state status=complete"
          preview="先展示当前 diff/PR 状态，再决定是否开 PR"
          ;;
        product-type|strategy|research|problem-solution|product-spec|tech-project-plan|intake)
          skill="/yishuship:pm-intake"
          effect="完成本 phase 的产品决策与产物，工程不会在空定义上开工"
          present="对应 product/* 与 lifecycle-checklist 更新"
          preview="本 phase 只产出文档；你可先读再批准进入下一 phase"
          ;;
        design)
          skill="/yishuship:design"
          effect="规格与切片清晰后，dev 按片推进且可独立验证"
          present="plan/plan.md + peer 对齐记录（如有）"
          preview="先给切片清单与风险，你确认范围再实现"
          ;;
        dev|implement)
          skill="/yishuship:dev"
          effect="代码按垂直切片落地，带测试缝的可运行增量"
          present="git diff + 切片验收命令通过"
          preview="先做最小一片 demo 路径，跑通再扩"
          ;;
        e2e)
          skill="/yishuship:e2e"
          effect="用户可见行为有回归网，后续改动不易静默破坏"
          present="e2e/report.md + 可重跑命令"
          preview="先固化 1 条黄金路径测试给你看红绿"
          ;;
        review)
          skill="/yishuship:review"
          effect="在扩大范围前暴露正确性/规格偏差，减少带病进入 QA/发布"
          present="按严重级别列出的 findings（Standards + Spec）"
          preview="先只扫当前 diff，不出修复 PR，你决定修哪些"
          ;;
        qa)
          skill="/yishuship:qa"
          effect="用真实运行证据证明可交付，而非口头 done"
          present="qa/ 下日志、截图或复现步骤"
          preview="先跑核心路径一遍，把失败录成证据"
          ;;
        refactor)
          skill="/yishuship:refactor"
          effect="降低后续改动成本，行为保持不变"
          present="scoped plan + 行为对照证据"
          preview="先给深模块机会列表，你选一块再动刀"
          ;;
        handoff|release)
          skill="/yishuship:handoff"
          effect="变更进入 PR/CI 闭环，可交接给其他会话或人"
          present="PR 链接或 handoff 文档 + CI 状态"
          preview="先生成 PR 描述草稿给你改，再 push"
          ;;
        *)
          # Artifact-driven fallback when phase label is unknown
          if [[ ",$missing," == *",pm_handoff,"* ]] || [ "$stage" = "idea_only" ] || [ "$stage" = "empty" ]; then
            skill="/yishuship:pm-intake"
            effect="先有产品定义与验收，再写代码"
            present="product/* + delivery/design-spec.md"
            preview="先判别产品类型与问题一页"
          elif [[ ",$missing," == *",plan,"* ]]; then
            skill="/yishuship:design"
            effect="实现有切片与顺序，避免横层大爆炸"
            present="plan/plan.md"
            preview="先出切片列表"
          elif [[ ",$missing," == *",e2e,"* ]]; then
            skill="/yishuship:e2e"
            effect="关键路径可回归"
            present="e2e/report.md"
            preview="先一条黄金路径"
          elif [[ ",$missing," == *",qa,"* ]]; then
            skill="/yishuship:qa"
            effect="运行时证据支撑发布决策"
            present="qa 证据目录"
            preview="先手跑核心路径"
          else
            skill="/yishuship:review"
            effect="发布前收敛风险"
            present="review findings"
            preview="先只读审查 diff"
          fi
          ;;
      esac
      ;;
  esac

  NEXT_SKILL="$skill"
  NEXT_EFFECT="$effect"
  NEXT_PRESENT="$present"
  NEXT_PREVIEW="$preview"
  WHERE_ZH="$where"
  MISSING_ZH="$miss_zh"
}

cmd_status() {
  local enabled active_task phase next_action reason resolved task_id
  enabled="$(detect_enabled)"
  active_task="none"
  phase="none"
  next_action="idle"
  reason="no yishuship markers"
  task_id=""

  SENSE_HAVE="none"
  SENSE_MISSING="none"
  SENSE_STAGE="none"

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
    probe_task_artifacts "$task_id"
  else
    local cfg
    cfg="$(config_enabled_value)"
    if [ "$cfg" = "false" ]; then
      enabled="false"
      next_action="bypass_ok"
      reason="config enabled: false"
      SENSE_STAGE="opt_out"
    elif [ "$enabled" = "true" ]; then
      next_action="route"
      reason="enabled, no active task - classify then enter"
      SENSE_STAGE="enabled_idle"
    else
      next_action="idle"
      reason="not enabled in this repo"
      SENSE_STAGE="disabled"
    fi
  fi

  build_sense_narrative "$phase" "$next_action" "$active_task" "$SENSE_MISSING" "$SENSE_STAGE"

  # Machine block (activation)
  emit "enabled" "$enabled"
  emit "active_task" "$active_task"
  emit "phase" "$phase"
  emit "next_action" "$next_action"
  emit "reason" "$reason"

  # State Sense block (diagnosis + causal next)
  emit "sense_stage" "$SENSE_STAGE"
  emit "sense_have" "$SENSE_HAVE"
  emit "sense_missing" "$SENSE_MISSING"
  emit "sense_where" "$WHERE_ZH"
  emit "sense_gap" "$MISSING_ZH"
  emit "sense_next" "$NEXT_SKILL"
  emit "sense_effect" "$NEXT_EFFECT"
  emit "sense_presentation" "$NEXT_PRESENT"
  emit "sense_preview" "$NEXT_PREVIEW"
  # One pasteable human block for agents (single line with | separators)
  emit "sense_report" "【现在】${WHERE_ZH} | 【缺什么】${MISSING_ZH} | 【下一步】${NEXT_SKILL} | 【做完后】${NEXT_EFFECT} | 【你怎么确认】${NEXT_PRESENT} | 【先感受】${NEXT_PREVIEW}"
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
