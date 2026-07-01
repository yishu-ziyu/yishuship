# Engineering Spec

## Goal

Keep local Claude Code yishuship usage synchronized with `https://github.com/yishu-ziyu/ship.git` and expose reliable `/yishuship:*` skills.

## Acceptance Criteria

- `scripts/sync-local.sh --check-remote` reports repo, remote, plugin, and skill-link status.
- `scripts/sync-local.sh --apply` skips `git pull` when the repo is dirty.
- SessionStart output mentions `/yishuship:use-yishuship` and does not mention `/ship:use-ship`.
- Plugin metadata repository is `https://github.com/yishu-ziyu/ship`.
- Installed plugin cache is refreshed after metadata changes.
- `docs/operations/yishuship-sync.md` explains check and apply usage.
