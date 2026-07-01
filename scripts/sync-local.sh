#!/usr/bin/env bash
# Keep the local yishuship repository and Claude Code plugin exposure in sync.
#
# Default mode is check-only. Use --apply to pull the latest main branch when the
# repo is clean, refresh the Claude Code plugin, and repair /yishuship:* skill
# links.

set -u

MODE="check"
CHECK_REMOTE="0"
ROOT="${YISHUSHIP_ROOT:-/Users/mahaoxuan/Developer/yishuship}"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
PLUGIN_ID="yishuship@yishuship"
MARKETPLACE="yishuship"
INSTALL_JSON="$HOME/.claude/plugins/installed_plugins.json"

usage() {
  cat <<'EOF'
Usage: scripts/sync-local.sh [--check] [--check-remote] [--apply]

Modes:
  --check          Inspect local repo, plugin cache, and skill links. Default.
  --check-remote   Also compare local HEAD with origin/main.
  --apply          Pull origin/main when safe, update the plugin, and repair links.

Environment:
  YISHUSHIP_ROOT      Local yishuship checkout. Default: /Users/mahaoxuan/Developer/yishuship
  CLAUDE_SKILLS_DIR   Claude skills directory. Default: ~/.claude/skills
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

skill_total=0
skill_ok=0
skill_missing=""
for skill_file in "$ROOT"/skills/*/SKILL.md; do
  [ -f "$skill_file" ] || continue
  skill_dir=$(dirname "$skill_file")
  skill_name=$(basename "$skill_dir")
  case "$skill_name" in
    .shared)
      continue
      ;;
  esac
  skill_total=$((skill_total + 1))
  link_path="$SKILLS_DIR/yishuship:$skill_name"
  if [ -L "$link_path" ] && [ "$(readlink "$link_path")" = "$skill_dir" ]; then
    skill_ok=$((skill_ok + 1))
  else
    skill_missing="$skill_missing yishuship:$skill_name"
  fi
done

stale_unprefixed=""
for skill_file in "$ROOT"/skills/*/SKILL.md; do
  [ -f "$skill_file" ] || continue
  skill_dir=$(dirname "$skill_file")
  skill_name=$(basename "$skill_dir")
  case "$skill_name" in
    .shared)
      continue
      ;;
  esac
  legacy_path="$SKILLS_DIR/$skill_name"
  if [ -L "$legacy_path" ] && [ "$(readlink "$legacy_path")" = "$skill_dir" ]; then
    stale_unprefixed="$stale_unprefixed $skill_name"
  fi
done

print_status() {
  echo "yishuship sync status"
  echo "repo: $ROOT"
  echo "origin: $origin_url"
  echo "branch: $repo_branch"
  echo "repo_head: $(short_sha "$repo_head")"
  echo "remote_main: $(short_sha "$remote_head")"
  echo "installed_plugin: $(short_sha "$installed_sha")"
  echo "installed_path: $installed_path"
  echo "manifest_repository: $manifest_repo"
  echo "skill_links: $skill_ok/$skill_total"
  if [ -n "$skill_missing" ]; then
    echo "missing_or_wrong_links:$skill_missing"
  fi
  if [ -n "$stale_unprefixed" ]; then
    echo "stale_unprefixed_links:$stale_unprefixed"
  fi
  if [ -n "$repo_status" ]; then
    echo "working_tree: dirty"
  else
    echo "working_tree: clean"
  fi

  if [ "$CHECK_REMOTE" = "1" ] && [ "$remote_head" != "unknown" ] && [ "$repo_head" != "$remote_head" ]; then
    echo "update_needed: repo differs from origin/main"
  elif [ "$installed_sha" != "missing" ] && [ "$installed_sha" != "$repo_head" ]; then
    echo "update_needed: installed plugin differs from local repo"
  elif [ "$skill_ok" -ne "$skill_total" ]; then
    echo "update_needed: skill links need repair"
  else
    echo "update_needed: no"
  fi
}

if [ "$MODE" = "check" ]; then
  print_status
  exit 0
fi

if [ -n "$repo_status" ]; then
  echo "Local yishuship repo has uncommitted changes. Skipping git pull to avoid overwriting local work."
else
  echo "Fetching and fast-forwarding origin/main..."
  git -C "$ROOT" fetch origin main
  git -C "$ROOT" pull --ff-only origin main
fi

if command -v claude >/dev/null 2>&1; then
  echo "Refreshing Claude Code marketplace and plugin..."
  claude plugin marketplace update "$MARKETPLACE" >/dev/null 2>&1 || true
  claude plugin uninstall "$PLUGIN_ID" >/dev/null 2>&1 || true
  claude plugin install --scope user "$PLUGIN_ID" >/dev/null
  if ! claude plugin list --json | jq -e --arg id "$PLUGIN_ID" '.[] | select(.id == $id and .enabled == true)' >/dev/null 2>&1; then
    claude plugin enable "$PLUGIN_ID" >/dev/null 2>&1 || true
  fi
else
  echo "WARN claude command not found; skipping plugin refresh" >&2
fi

mkdir -p "$SKILLS_DIR"
for skill_file in "$ROOT"/skills/*/SKILL.md; do
  [ -f "$skill_file" ] || continue
  skill_dir=$(dirname "$skill_file")
  skill_name=$(basename "$skill_dir")
  case "$skill_name" in
    .shared)
      continue
      ;;
  esac
  link_path="$SKILLS_DIR/yishuship:$skill_name"
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
  legacy_path="$SKILLS_DIR/$skill_name"
  if [ -L "$legacy_path" ] && [ "$(readlink "$legacy_path")" = "$skill_dir" ]; then
    rm "$legacy_path"
  fi
done

repo_head=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo "unknown")
repo_status=$(git -C "$ROOT" status --porcelain 2>/dev/null || true)
if [ -f "$INSTALL_JSON" ]; then
  installed_sha=$(jq -r --arg id "$PLUGIN_ID" '.plugins[$id][0].gitCommitSha // "missing"' "$INSTALL_JSON" 2>/dev/null || echo "missing")
  installed_path=$(jq -r --arg id "$PLUGIN_ID" '.plugins[$id][0].installPath // "missing"' "$INSTALL_JSON" 2>/dev/null || echo "missing")
fi

print_status
