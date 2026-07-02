# yishuship Sync Operations

## Purpose

Use this when Claude Code may be behind the latest `https://github.com/yishu-ziyu/ship.git` yishuship repository.

It checks the local yishuship checkout, Claude Code plugin cache, and visible `/yishuship:*` skills together.

## Quick Check

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --check-remote
```

Healthy output should include:

```text
repo_head: <sha>
remote_main: <same sha>
installed_plugin: <same sha>
skill_links: 14/14
update_needed: no
```

## Safe Refresh

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --apply
```

This will:

1. Pull `origin/main` only if the local repo is clean.
2. Refresh the `yishuship@yishuship` Claude Code plugin.
3. Repair `/yishuship:*` skill links.
4. Remove stale unprefixed yishuship skill symlinks that point to this repo.

It will not commit, push, remove marketplaces, or overwrite non-symlink files.

## If The Repo Is Dirty

The script prints `working_tree: dirty` and skips `git pull`.

Decide manually whether to commit, stash, or keep working without pulling.

## Current Canonical Paths

| Surface | Path |
|---------|------|
| Source repo | `/Users/mahaoxuan/Developer/yishuship` |
| Remote repo | `https://github.com/yishu-ziyu/ship.git` |
| Plugin ID | `yishuship@yishuship` |
| Plugin cache | `~/.claude/plugins/cache/yishuship/yishuship/0.1.0` |
| Skill links | `~/.claude/skills/yishuship:*` |

## Session Rule

At the start of work that may use Ship process, consult `/yishuship:use-yishuship`.

Do not use `/ship:use-ship` for the user's yishuship workflow unless explicitly comparing against original Ship.
