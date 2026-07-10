#!/usr/bin/env bash
# Unified local exposure for yishuship across Claude Code, Codex, and agents.
#
# Canonical source of truth:
#   YISHUSHIP_ROOT (default: /Users/mahaoxuan/Developer/yishuship)
#
# Surfaces kept in lockstep by --apply:
#   1. Skill symlinks: ~/.claude/skills/yishuship:* and ~/.agents/skills/yishuship:*
#   2. Codex personal marketplace source: ~/plugins/yishuship -> YISHUSHIP_ROOT
#   3. Claude Code plugin cache (reinstall yishuship@yishuship from local marketplace)
#   4. Codex personal plugin cache (reinstall yishuship@personal)
#
# Default mode is check-only. Never force-pulls main onto a feature branch unless
# you pass --pull-main.

set -u

MODE="check"
CHECK_REMOTE="0"
PULL_MAIN="0"
ROOT="${YISHUSHIP_ROOT:-/Users/mahaoxuan/Developer/yishuship}"
PLUGIN_ID="yishuship@yishuship"
MARKETPLACE="yishuship"
INSTALL_JSON="$HOME/.claude/plugins/installed_plugins.json"
CODEX_PLUGIN_ID="yishuship@personal"
CODEX_PERSONAL_SRC="${YISHUSHIP_CODEX_SRC:-$HOME/plugins/yishuship}"
CODEX_CACHE_DIR="${YISHUSHIP_CODEX_CACHE:-$HOME/.codex/plugins/cache/personal/yishuship/0.1.0}"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
AGENTS_SKILLS_DIR="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"

# Ordered skill link directories (unified entry points for skill discovery).
SKILL_DIRS=("$CLAUDE_SKILLS_DIR" "$AGENTS_SKILLS_DIR")

usage() {
  cat <<'EOF'
Usage: scripts/sync-local.sh [--check] [--check-remote] [--apply] [--pull-main]

Modes:
  --check          Inspect all local exposure surfaces. Default.
  --check-remote   Also compare local HEAD with origin/main.
  --apply          Refresh skill links, Codex personal source link, Claude + Codex
                   plugin caches from the local repo HEAD (no branch switch).
  --pull-main      With --apply: also fetch/ff-only origin/main when working tree
                   is clean (optional; default is never change git branch).

Environment:
  YISHUSHIP_ROOT         Local yishuship checkout.
  CLAUDE_SKILLS_DIR      Default: ~/.claude/skills
  AGENTS_SKILLS_DIR      Default: ~/.agents/skills
  YISHUSHIP_CODEX_SRC    Codex personal marketplace path (default: ~/plugins/yishuship)
  YISHUSHIP_CODEX_CACHE  Codex installed cache path
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check)
      MODE="check"
      ;;
    --check-remote)
      CHECK_REMOTE="1"
      ;;
    --apply)
      MODE="apply"
      CHECK_REMOTE="1"
      ;;
    --pull-main)
      PULL_MAIN="1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ ! -d "$ROOT/.git" ]; then
  echo "FAIL yishuship repo not found at $ROOT" >&2
  exit 1
fi

if [ ! -d "$ROOT/skills" ]; then
  echo "FAIL yishuship skills directory not found at $ROOT/skills" >&2
  exit 1
fi

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "FAIL missing required command: $1" >&2
    exit 1
  fi
}

need_command git
need_command jq

short_sha() {
  local value="$1"
  if [ "$value" = "missing" ] || [ "$value" = "unknown" ] || [ -z "$value" ]; then
    printf '%s' "$value"
  else
    printf '%s' "$value" | cut -c 1-7
  fi
}

resolve_path() {
  # Resolve symlinks when possible; fall back to the given path.
  local p="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath "$p" 2>/dev/null || printf '%s' "$p"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$p" 2>/dev/null || printf '%s' "$p"
  else
    printf '%s' "$p"
  fi
}

repo_head=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo "unknown")
repo_branch=$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
repo_status=$(git -C "$ROOT" status --porcelain 2>/dev/null || true)
origin_url=$(git -C "$ROOT" config --get remote.origin.url 2>/dev/null || echo "missing")
remote_head="unknown"

if [ "$CHECK_REMOTE" = "1" ]; then
  remote_head=$(git -C "$ROOT" ls-remote origin refs/heads/main 2>/dev/null | awk '{print $1}')
  [ -z "$remote_head" ] && remote_head="unknown"
fi

installed_sha="missing"
installed_path="missing"
if [ -f "$INSTALL_JSON" ]; then
  installed_sha=$(jq -r --arg id "$PLUGIN_ID" '.plugins[$id][0].gitCommitSha // "missing"' "$INSTALL_JSON" 2>/dev/null || echo "missing")
  installed_path=$(jq -r --arg id "$PLUGIN_ID" '.plugins[$id][0].installPath // "missing"' "$INSTALL_JSON" 2>/dev/null || echo "missing")
fi

manifest_repo=$(jq -r '.repository // "missing"' "$ROOT/.claude-plugin/plugin.json" 2>/dev/null || echo "missing")

# Peer-review gate is a canary for "cache matches current repo discipline".
has_peer_gate() {
  local script="$1"
  [ -f "$script" ] && grep -q "require_peer_review_log\|control/peer-review.md" "$script" 2>/dev/null
}

claude_cache_peer="missing"
if [ "$installed_path" != "missing" ] && [ -f "$installed_path/scripts/auto-orchestrate.sh" ]; then
  if has_peer_gate "$installed_path/scripts/auto-orchestrate.sh"; then
    claude_cache_peer="yes"
  else
    claude_cache_peer="no"
  fi
fi

codex_cache_peer="missing"
if [ -f "$CODEX_CACHE_DIR/scripts/auto-orchestrate.sh" ]; then
  if has_peer_gate "$CODEX_CACHE_DIR/scripts/auto-orchestrate.sh"; then
    codex_cache_peer="yes"
  else
    codex_cache_peer="no"
  fi
fi

codex_src_state="missing"
if [ -L "$CODEX_PERSONAL_SRC" ]; then
  target=$(readlink "$CODEX_PERSONAL_SRC")
  resolved=$(resolve_path "$CODEX_PERSONAL_SRC")
  root_resolved=$(resolve_path "$ROOT")
  if [ "$resolved" = "$root_resolved" ] || [ "$target" = "$ROOT" ]; then
    codex_src_state="symlink->repo"
  else
    codex_src_state="symlink->other:$target"
  fi
elif [ -d "$CODEX_PERSONAL_SRC" ]; then
  codex_src_state="directory-copy"
elif [ -e "$CODEX_PERSONAL_SRC" ]; then
  codex_src_state="other"
fi

count_skill_links() {
  local skills_dir="$1"
  local skill_total=0
  local skill_ok=0
  local skill_missing=""
  local skill_file skill_dir skill_name link_path

  for skill_file in "$ROOT"/skills/*/SKILL.md; do
    [ -f "$skill_file" ] || continue
    skill_dir=$(dirname "$skill_file")
    skill_name=$(basename "$skill_dir")
    case "$skill_name" in
      .shared) continue ;;
    esac
    skill_total=$((skill_total + 1))
    link_path="$skills_dir/yishuship:$skill_name"
    if [ -L "$link_path" ] && [ "$(readlink "$link_path")" = "$skill_dir" ]; then
      skill_ok=$((skill_ok + 1))
    else
      skill_missing="$skill_missing yishuship:$skill_name"
    fi
  done

  printf '%s\t%s\t%s' "$skill_ok" "$skill_total" "$skill_missing"
}

stale_unprefixed_in() {
  local skills_dir="$1"
  local skill_file skill_dir skill_name legacy_path
  local stale=""
  for skill_file in "$ROOT"/skills/*/SKILL.md; do
    [ -f "$skill_file" ] || continue
    skill_dir=$(dirname "$skill_file")
    skill_name=$(basename "$skill_dir")
    case "$skill_name" in
      .shared) continue ;;
    esac
    legacy_path="$skills_dir/$skill_name"
    if [ -L "$legacy_path" ] && [ "$(readlink "$legacy_path")" = "$skill_dir" ]; then
      stale="$stale $skill_name"
    fi
  done
  printf '%s' "$stale"
}

claude_links=$(count_skill_links "$CLAUDE_SKILLS_DIR")
agents_links=$(count_skill_links "$AGENTS_SKILLS_DIR")
claude_ok=${claude_links%%$'\t'*}
claude_rest=${claude_links#*$'\t'}
claude_total=${claude_rest%%$'\t'*}
claude_missing=${claude_rest#*$'\t'}
agents_ok=${agents_links%%$'\t'*}
agents_rest=${agents_links#*$'\t'}
agents_total=${agents_rest%%$'\t'*}
agents_missing=${agents_rest#*$'\t'}

claude_stale=$(stale_unprefixed_in "$CLAUDE_SKILLS_DIR")
agents_stale=$(stale_unprefixed_in "$AGENTS_SKILLS_DIR")

print_status() {
  echo "yishuship sync status"
  echo "canonical_repo: $ROOT"
  echo "origin: $origin_url"
  echo "branch: $repo_branch"
  echo "repo_head: $(short_sha "$repo_head")"
  echo "remote_main: $(short_sha "$remote_head")"
  echo "claude_plugin_sha: $(short_sha "$installed_sha")"
  echo "claude_plugin_path: $installed_path"
  echo "claude_plugin_peer_gate: $claude_cache_peer"
  echo "codex_personal_src: $CODEX_PERSONAL_SRC ($codex_src_state)"
  echo "codex_plugin_cache: $CODEX_CACHE_DIR"
  echo "codex_plugin_peer_gate: $codex_cache_peer"
  echo "manifest_repository: $manifest_repo"
  echo "claude_skill_links: $claude_ok/$claude_total ($CLAUDE_SKILLS_DIR)"
  echo "agents_skill_links: $agents_ok/$agents_total ($AGENTS_SKILLS_DIR)"
  if [ -n "$claude_missing" ]; then
    echo "claude_missing_or_wrong_links:$claude_missing"
  fi
  if [ -n "$agents_missing" ]; then
    echo "agents_missing_or_wrong_links:$agents_missing"
  fi
  if [ -n "$claude_stale" ]; then
    echo "claude_stale_unprefixed_links:$claude_stale"
  fi
  if [ -n "$agents_stale" ]; then
    echo "agents_stale_unprefixed_links:$agents_stale"
  fi
  if [ -n "$repo_status" ]; then
    echo "working_tree: dirty"
  else
    echo "working_tree: clean"
  fi

  local problems=0
  if [ "$CHECK_REMOTE" = "1" ] && [ "$remote_head" != "unknown" ] && [ "$repo_head" != "$remote_head" ]; then
    echo "note: local HEAD differs from origin/main (ok if on a feature branch)"
  fi
  if [ "$installed_sha" != "missing" ] && [ "$installed_sha" != "$repo_head" ]; then
    problems=1
  fi
  if [ "$claude_cache_peer" = "no" ] || [ "$codex_cache_peer" = "no" ]; then
    problems=1
  fi
  if [ "$codex_src_state" != "symlink->repo" ]; then
    problems=1
  fi
  if [ "$claude_ok" -ne "$claude_total" ] || [ "$agents_ok" -ne "$agents_total" ]; then
    problems=1
  fi
  if [ "$problems" -eq 0 ]; then
    echo "update_needed: no"
  else
    echo "update_needed: yes (run: scripts/sync-local.sh --apply)"
  fi
}

repair_skill_links() {
  local skills_dir="$1"
  local skill_file skill_dir skill_name link_path legacy_path

  mkdir -p "$skills_dir"
  for skill_file in "$ROOT"/skills/*/SKILL.md; do
    [ -f "$skill_file" ] || continue
    skill_dir=$(dirname "$skill_file")
    skill_name=$(basename "$skill_dir")
    case "$skill_name" in
      .shared) continue ;;
    esac
    link_path="$skills_dir/yishuship:$skill_name"
    if [ -e "$link_path" ] && [ ! -L "$link_path" ]; then
      echo "WARN not replacing non-symlink path: $link_path" >&2
      continue
    fi
    ln -sfn "$skill_dir" "$link_path"
  done

  for skill_file in "$ROOT"/skills/*/SKILL.md; do
    [ -f "$skill_file" ] || continue
    skill_dir=$(dirname "$skill_file")
    skill_name=$(basename "$skill_dir")
    case "$skill_name" in
      .shared) continue ;;
    esac
    legacy_path="$skills_dir/$skill_name"
    if [ -L "$legacy_path" ] && [ "$(readlink "$legacy_path")" = "$skill_dir" ]; then
      rm "$legacy_path"
    fi
  done
}

unify_codex_personal_source() {
  # Prefer a single symlink: ~/plugins/yishuship -> canonical repo.
  mkdir -p "$(dirname "$CODEX_PERSONAL_SRC")"
  if [ -L "$CODEX_PERSONAL_SRC" ]; then
    ln -sfn "$ROOT" "$CODEX_PERSONAL_SRC"
    echo "Codex personal source: symlink refreshed -> $ROOT"
    return 0
  fi
  if [ -d "$CODEX_PERSONAL_SRC" ]; then
    backup="${CODEX_PERSONAL_SRC}.bak.$(date +%Y%m%d-%H%M%S)"
    echo "Codex personal source is a directory copy; moving aside to $backup"
    mv "$CODEX_PERSONAL_SRC" "$backup"
  elif [ -e "$CODEX_PERSONAL_SRC" ]; then
    echo "FAIL unexpected non-directory at $CODEX_PERSONAL_SRC" >&2
    return 1
  fi
  ln -sfn "$ROOT" "$CODEX_PERSONAL_SRC"
  echo "Codex personal source: created symlink $CODEX_PERSONAL_SRC -> $ROOT"
}

mirror_tree_to_cache() {
  # Fallback mirror when CLI reinstall is unavailable.
  local dest="$1"
  mkdir -p "$dest"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude '.git/' \
      --exclude '.DS_Store' \
      --exclude 'node_modules/' \
      --exclude '__pycache__/' \
      --exclude '.ship/' \
      --exclude '*.pyc' \
      "$ROOT"/ "$dest"/
  else
    # Portable fallback: wipe dest contents then copy.
    find "$dest" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    # shellcheck disable=SC2086
    tar -C "$ROOT" \
      --exclude '.git' \
      --exclude '.DS_Store' \
      --exclude 'node_modules' \
      --exclude '__pycache__' \
      --exclude '.ship' \
      -cf - . | tar -C "$dest" -xf -
  fi
  # Stamp the cache with the repo HEAD for humans and future checks.
  printf '%s\n' "$repo_head" >"$dest/.yishuship-synced-from"
  echo "Mirrored repo into cache: $dest"
}

refresh_claude_plugin() {
  if command -v claude >/dev/null 2>&1; then
    echo "Refreshing Claude Code marketplace and plugin..."
    claude plugin marketplace update "$MARKETPLACE" >/dev/null 2>&1 || true
    claude plugin uninstall "$PLUGIN_ID" >/dev/null 2>&1 || true
    if ! claude plugin install --scope user "$PLUGIN_ID" >/dev/null 2>&1; then
      echo "WARN claude plugin install failed; mirroring into known cache path" >&2
      if [ "$installed_path" != "missing" ] && [ -d "$(dirname "$installed_path")" ]; then
        mirror_tree_to_cache "$installed_path"
      else
        mirror_tree_to_cache "$HOME/.claude/plugins/cache/yishuship/yishuship/0.1.0"
      fi
    fi
    claude plugin enable "$PLUGIN_ID" >/dev/null 2>&1 || true
  else
    echo "WARN claude command not found; mirroring Claude plugin cache" >&2
    mirror_tree_to_cache "$HOME/.claude/plugins/cache/yishuship/yishuship/0.1.0"
  fi

  # After reinstall, if peer gate still missing, force mirror (CLI may have used stale snapshot).
  local path="$HOME/.claude/plugins/cache/yishuship/yishuship/0.1.0"
  if [ -f "$INSTALL_JSON" ]; then
    path=$(jq -r --arg id "$PLUGIN_ID" '.plugins[$id][0].installPath // empty' "$INSTALL_JSON" 2>/dev/null || true)
    [ -z "$path" ] && path="$HOME/.claude/plugins/cache/yishuship/yishuship/0.1.0"
  fi
  if ! has_peer_gate "$path/scripts/auto-orchestrate.sh"; then
    echo "Claude plugin cache still missing peer gate; forcing mirror from repo"
    mirror_tree_to_cache "$path"
    # Best-effort: stamp installed_plugins.json sha to current HEAD so check stays honest.
    if [ -f "$INSTALL_JSON" ] && command -v python3 >/dev/null 2>&1; then
      python3 - "$INSTALL_JSON" "$PLUGIN_ID" "$repo_head" "$path" <<'PY'
import json, sys, pathlib
path, plugin_id, sha, install = sys.argv[1:5]
data = json.loads(pathlib.Path(path).read_text())
entries = data.get("plugins", {}).get(plugin_id, [])
if entries:
    entries[0]["gitCommitSha"] = sha
    entries[0]["installPath"] = install
    entries[0]["lastUpdated"] = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    pathlib.Path(path).write_text(json.dumps(data, indent=2) + "\n")
PY
    fi
  fi
}

refresh_codex_plugin() {
  if command -v codex >/dev/null 2>&1; then
    echo "Refreshing Codex personal plugin ($CODEX_PLUGIN_ID)..."
    codex plugin remove "$CODEX_PLUGIN_ID" >/dev/null 2>&1 || true
    if ! codex plugin add "$CODEX_PLUGIN_ID" >/dev/null 2>&1; then
      echo "WARN codex plugin add failed; mirroring into cache" >&2
      mirror_tree_to_cache "$CODEX_CACHE_DIR"
    fi
  else
    echo "WARN codex command not found; mirroring Codex plugin cache" >&2
    mirror_tree_to_cache "$CODEX_CACHE_DIR"
  fi

  if ! has_peer_gate "$CODEX_CACHE_DIR/scripts/auto-orchestrate.sh"; then
    echo "Codex plugin cache still missing peer gate; forcing mirror from repo"
    mirror_tree_to_cache "$CODEX_CACHE_DIR"
  fi
}

if [ "$MODE" = "check" ]; then
  print_status
  exit 0
fi

# ── apply ──────────────────────────────────────────────────────────────

if [ "$PULL_MAIN" = "1" ]; then
  if [ -n "$repo_status" ]; then
    echo "Local yishuship repo has uncommitted changes. Skipping git pull."
  else
    echo "Fetching and fast-forwarding origin/main..."
    git -C "$ROOT" fetch origin main
    git -C "$ROOT" pull --ff-only origin main
    repo_head=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo "unknown")
    repo_branch=$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  fi
else
  echo "Skipping git pull (pass --pull-main to ff origin/main). Using current HEAD $(short_sha "$repo_head") on $repo_branch."
fi

echo "Repairing skill links (Claude + agents)..."
for d in "${SKILL_DIRS[@]}"; do
  repair_skill_links "$d"
  echo "  linked: $d"
done

echo "Unifying Codex personal marketplace source..."
unify_codex_personal_source

refresh_claude_plugin
refresh_codex_plugin

# Recompute status fields after apply.
repo_head=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo "unknown")
repo_status=$(git -C "$ROOT" status --porcelain 2>/dev/null || true)
if [ -f "$INSTALL_JSON" ]; then
  installed_sha=$(jq -r --arg id "$PLUGIN_ID" '.plugins[$id][0].gitCommitSha // "missing"' "$INSTALL_JSON" 2>/dev/null || echo "missing")
  installed_path=$(jq -r --arg id "$PLUGIN_ID" '.plugins[$id][0].installPath // "missing"' "$INSTALL_JSON" 2>/dev/null || echo "missing")
fi

claude_cache_peer="missing"
if [ "$installed_path" != "missing" ] && [ -f "$installed_path/scripts/auto-orchestrate.sh" ]; then
  if has_peer_gate "$installed_path/scripts/auto-orchestrate.sh"; then
    claude_cache_peer="yes"
  else
    claude_cache_peer="no"
  fi
elif [ -f "$HOME/.claude/plugins/cache/yishuship/yishuship/0.1.0/scripts/auto-orchestrate.sh" ]; then
  if has_peer_gate "$HOME/.claude/plugins/cache/yishuship/yishuship/0.1.0/scripts/auto-orchestrate.sh"; then
    claude_cache_peer="yes"
    installed_path="$HOME/.claude/plugins/cache/yishuship/yishuship/0.1.0"
  else
    claude_cache_peer="no"
  fi
fi

codex_cache_peer="missing"
if [ -f "$CODEX_CACHE_DIR/scripts/auto-orchestrate.sh" ]; then
  if has_peer_gate "$CODEX_CACHE_DIR/scripts/auto-orchestrate.sh"; then
    codex_cache_peer="yes"
  else
    codex_cache_peer="no"
  fi
fi

if [ -L "$CODEX_PERSONAL_SRC" ]; then
  resolved=$(resolve_path "$CODEX_PERSONAL_SRC")
  root_resolved=$(resolve_path "$ROOT")
  if [ "$resolved" = "$root_resolved" ]; then
    codex_src_state="symlink->repo"
  else
    codex_src_state="symlink->other:$(readlink "$CODEX_PERSONAL_SRC")"
  fi
elif [ -d "$CODEX_PERSONAL_SRC" ]; then
  codex_src_state="directory-copy"
else
  codex_src_state="missing"
fi

claude_links=$(count_skill_links "$CLAUDE_SKILLS_DIR")
agents_links=$(count_skill_links "$AGENTS_SKILLS_DIR")
claude_ok=${claude_links%%$'\t'*}
claude_rest=${claude_links#*$'\t'}
claude_total=${claude_rest%%$'\t'*}
claude_missing=${claude_rest#*$'\t'}
agents_ok=${agents_links%%$'\t'*}
agents_rest=${agents_links#*$'\t'}
agents_total=${agents_rest%%$'\t'*}
agents_missing=${agents_rest#*$'\t'}
claude_stale=$(stale_unprefixed_in "$CLAUDE_SKILLS_DIR")
agents_stale=$(stale_unprefixed_in "$AGENTS_SKILLS_DIR")

print_status
