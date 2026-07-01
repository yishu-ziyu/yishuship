# PRD

## Product Requirements

1. Provide a local sync script at `scripts/sync-local.sh`.
2. The script must support `--check`, `--check-remote`, and `--apply`.
3. The script must compare local repo head, optional remote head, installed plugin commit, and `/yishuship:*` skill links.
4. The script must repair namespaced skill links during `--apply`.
5. The script must skip `git pull` when the repo is dirty.
6. SessionStart must point to `/yishuship:use-yishuship`, not `/ship:use-ship`.
7. Plugin metadata must point to `https://github.com/yishu-ziyu/ship`.
8. The installed plugin cache must be refreshed after metadata or hook changes.
9. The workflow must be documented in `docs/operations/yishuship-sync.md`.

## Acceptance Criteria

- `scripts/sync-local.sh --check-remote` exits 0 and prints `skill_links: 13/13`.
- The same command prints `repo_head`, `remote_main`, and `installed_plugin` as matching short SHAs when the local repo is current.
- Running the SessionStart script emits `/yishuship:use-yishuship` and not `/ship:use-ship` in the routing hint.
- `~/.claude/plugins/cache/yishuship/yishuship/0.1.0/.claude-plugin/plugin.json` contains `https://github.com/yishu-ziyu/ship` after reinstall.
- Claude Code plugin list shows `yishuship@yishuship` enabled.

## Edge Cases

If the local repo is dirty, sync status may still report `update_needed: no`, but `working_tree: dirty` must be visible.

If a remote update exists while the repo is dirty, the script must not pull.

If Claude Code CLI is unavailable, the script should still report status and repair symlinks when possible.

## Out of Scope

Do not create a LaunchAgent in this task.

Do not remove heliohq marketplace entries in this task.

Do not commit or push unless the user asks.
