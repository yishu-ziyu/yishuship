# Product Blueprint

## Product Solution

The solution is a lightweight yishuship sync layer, not a new product surface.

It provides one check command and one apply command:

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --check-remote
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --apply
```

The check command is safe to run at the beginning of sessions or before using yishuship for important work.

The apply command is safe by default because it skips `git pull` if the local repository is dirty.

## Positioning

This is the local seatbelt for yishuship.

It does not replace Claude Code plugin install commands.

It wraps the necessary checks so the user and agents do not rely on memory.

## Core Flow

1. Agent starts a session or the user asks to use yishuship.
2. Agent runs or reads the sync status.
3. If the repo, plugin, and skill links match, proceed with `/yishuship:use-yishuship`.
4. If remote is ahead and the tree is clean, run `--apply`.
5. If remote is ahead and the tree is dirty, report that manual commit/stash decision is needed.

## Evolution Blueprint

Immediate version:

- Sync check script.
- Correct repository metadata.
- Operating document.
- Memory update.

Later version if needed:

- Shell alias such as `yishuship-sync`.
- SessionStart hook showing a one-line yishuship version.
- Optional scheduled reminder using Claude Code loop or an external LaunchAgent, only with explicit approval.

## Scope Boundary

The script only manages yishuship itself.

Per-project `.ship` tasks remain project-owned.

The script does not create commits or push changes.
