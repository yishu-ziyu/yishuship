#!/usr/bin/env bash
set -u

# yishuship artifact integrity checker.
#
# Maintains a SHA-256 manifest of control files that agents write but
# other agents/hooks read. Product and delivery artifacts are intentionally
# excluded -- they are user-editable.
#
# Modes:
#   --check                      Verify all entries; exit 1 on mismatch
#   --check --json               Same, but output block JSON on mismatch
#   --check --task <id>          Verify only entries for one task
#   --update <file> [...]        Update manifest entries for given files
#   --init                       Scan all existing tasks and create manifest

REPO_ROOT="${SHIP_REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
MANIFEST="$REPO_ROOT/.ship/.checksums"

# ── Helpers ──────────────────────────────────────────────────

hash_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  else
    echo "ERROR: no SHA-256 tool found" >&2
    exit 1
  fi
}

manifest_write() {
  local data="$1"
  mkdir -p "$(dirname "$MANIFEST")"
  printf '%s\n' "$data" > "$MANIFEST"
}

manifest_read() {
  if [ -f "$MANIFEST" ]; then
    cat "$MANIFEST"
  else
    printf '{"version":1,"files":{}}'
  fi
}

manifest_upsert_json() {
  local json="$1" path="$2" hash="$3"
  jq --arg p "$path" --arg h "$hash" '
    .files[$p] = $h | .version = (.version // 1)
  ' <<< "$json" 2>/dev/null || printf '{"version":1,"files":{"%s":"%s"}}\n' "$path" "$hash"
}

# ── Mode: --check ────────────────────────────────────────────

do_check() {
  local manifest
  manifest=$(manifest_read)

  local task_id=""
  local json_mode=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --task) task_id="$2"; shift 2 ;;
      --json) json_mode="yes"; shift ;;
      *) shift ;;
    esac
  done

  # Resolve current task_id from state file if not provided
  if [ -z "$task_id" ] && [ -f "$REPO_ROOT/.ship/ship-auto.local.md" ]; then
    task_id=$(sed -n '/^---$/,/^---$/{/^---$/d;p;}' "$REPO_ROOT/.ship/ship-auto.local.md" \
      | grep "^task_id:" | head -1 | sed 's/^task_id: *//' | tr -d '\r' || true)
  fi

  should_check_manifest_key() {
    local key="$1"
    [ -z "$task_id" ] && return 0

    case "$key" in
      .ship/tasks/*)
        local rest task_key
        rest="${key#.ship/tasks/}"
        task_key="${rest%%/*}"
        [ "$task_key" = "$task_id" ]
        return $?
        ;;
      *)
        return 0
        ;;
    esac
  }

  local mismatches=""
  local mismatch_count=0
  local key
  while IFS= read -r key; do
    [ -z "$key" ] && continue
    should_check_manifest_key "$key" || continue

    local resolved="$key"
    if [ -n "$task_id" ]; then
      resolved="${key//\{task_id\}/$task_id}"
    fi

    local full_path="$REPO_ROOT/$resolved"
    if [ ! -f "$full_path" ]; then
      if [ -n "$json_mode" ]; then
        mismatch_count=$((mismatch_count + 1))
        # Store as newline-separated JSON array entries; join at end
        mismatches="${mismatches}{\"path\":\"$resolved\",\"reason\":\"missing\"}\n"
      else
        mismatches="${mismatches}MISSING: $resolved\n"
      fi
      continue
    fi

    local recorded current
    recorded=$(printf '%s' "$manifest" | jq -r --arg k "$key" '.files[$k] // empty' 2>/dev/null)
    current=$(hash_file "$full_path")
    if [ "$recorded" != "$current" ]; then
      if [ -n "$json_mode" ]; then
        mismatch_count=$((mismatch_count + 1))
        mismatches="${mismatches}{\"path\":\"$resolved\",\"reason\":\"tampered\",\"recorded\":\"${recorded:0:16}...\",\"actual\":\"${current:0:16}...\"}\n"
      else
        mismatches="${mismatches}TAMPERED: $resolved (recorded=${recorded:0:16}..., actual=${current:0:16}...)\n"
      fi
    fi
  done < <(printf '%s' "$manifest" | jq -r '.files | keys[]' 2>/dev/null)

  if [ -n "$mismatches" ]; then
    if [ -n "$json_mode" ]; then
      local entries
      entries=$(printf '%b' "$mismatches" | jq -s '.')
      jq -n --argjson m "$entries" --argjson n "$mismatch_count" \
        '{"decision":"block","reason":"artifact integrity check failed","mismatches":$m,"count":$n}'
    else
      printf '%b' "$mismatches"
    fi
    exit 1
  fi

  if [ -n "$json_mode" ]; then
    jq -n '{"decision":"allow","reason":"all artifacts match"}'
  fi
  exit 0
}

# ── Mode: --update ───────────────────────────────────────────

do_update() {
  [ $# -eq 0 ] && { echo "Usage: --update <file> [<file> ...]" >&2; exit 1; }

  local manifest
  manifest=$(manifest_read)

  local updated=false
  while [ $# -gt 0 ]; do
    local file="$1"; shift

    # Resolve to repo-relative path
    local rel="${file#"$REPO_ROOT"/}"

    if [ ! -f "$file" ]; then
      echo "SKIP (not found): $rel" >&2
      continue
    fi

    local hash
    hash=$(hash_file "$file")
    manifest=$(manifest_upsert_json "$manifest" "$rel" "$hash")
    updated=true
  done

  if [ "$updated" = true ]; then
    manifest_write "$manifest"
  fi
  exit 0
}

# ── Mode: --init ─────────────────────────────────────────────

do_init() {
  local manifest
  manifest=$(manifest_read)

  # Add current ship-auto.local.md if active
  if [ -f "$REPO_ROOT/.ship/ship-auto.local.md" ]; then
    local hash
    hash=$(hash_file "$REPO_ROOT/.ship/ship-auto.local.md")
    manifest=$(manifest_upsert_json "$manifest" ".ship/ship-auto.local.md" "$hash")
  fi

  # Add pm-state.yaml
  if [ -f "$REPO_ROOT/.ship/pm-state.yaml" ]; then
    local hash
    hash=$(hash_file "$REPO_ROOT/.ship/pm-state.yaml")
    manifest=$(manifest_upsert_json "$manifest" ".ship/pm-state.yaml" "$hash")
  fi

  # Scan task directories
  if [ -d "$REPO_ROOT/.ship/tasks" ]; then
    local task_dir
    for task_dir in "$REPO_ROOT/.ship/tasks"/*/; do
      [ -d "$task_dir" ] || continue
      local tid
      tid=$(basename "$task_dir")

      local rel_control="${tid}/control/run_state.yaml"
      local rel_lifecycle="${tid}/control/lifecycle-checklist.yaml"
      local rel_handoff="${tid}/handoff.md"
      local rel_requirement="${tid}/input/requirement.md"
      local rel_idea="${tid}/input/idea.md"
      local rel_spec="${tid}/plan/spec.md"

      for rel in "$rel_control" "$rel_lifecycle" "$rel_handoff" "$rel_requirement" "$rel_idea" "$rel_spec"; do
        local full="$REPO_ROOT/.ship/tasks/$rel"
        if [ -f "$full" ]; then
          local hash
          hash=$(hash_file "$full")
          manifest=$(manifest_upsert_json "$manifest" ".ship/tasks/$rel" "$hash")
        fi
      done
    done
  fi

  manifest_write "$manifest"
  local count
  count=$(printf '%s' "$manifest" | jq '.files | length' 2>/dev/null || echo "?")
  echo "Initialized manifest with $count entries."
  exit 0
}

# ── Dispatch ─────────────────────────────────────────────────

MODE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --check)       MODE="check"; shift ;;
    --update)      MODE="update"; shift ;;
    --init)        MODE="init"; shift ;;
    *)
      if [ -z "$MODE" ]; then
        echo "Usage: $0 {--check [--json] [--task <id>]|--update <file> [...]|--init}" >&2
        exit 1
      fi
      break
      ;;
  esac
done

case "$MODE" in
  check)   do_check "$@" ;;
  update)  do_update "$@" ;;
  init)    do_init ;;
  *)
    echo "Usage: $0 {--check|--update <file> [...]|--init}" >&2
    exit 1
    ;;
esac
