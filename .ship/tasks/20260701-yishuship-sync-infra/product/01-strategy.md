# Strategy

## BRD: Why This Is Worth Doing

The current yishuship workflow can drift in three places: the GitHub repository, the local plugin cache, and the skill links exposed to Claude Code.

When those three drift, the user sees stale commands, missing skills, or old `/ship:*` wording even after the repo was updated.

This work is worth doing because yishuship is intended to be the shared operating process between the user and AI agents.

If the process layer is stale, every downstream project inherits confusion.

## MRD: Market, User, Competition

The primary user is the repository owner using Claude Code across multiple projects and sessions.

The competing alternatives are manual plugin reinstall, original `heliohq/ship`, and per-project ad hoc `.claude/commands` files.

Manual reinstall is fragile because it depends on memory.

Original Ship is useful but does not reflect the user's PM lifecycle additions.

Per-project commands are useful locally but do not create a stable global yishuship entry point.

## Switching Reason

The user should switch to this local sync infrastructure because it gives one small source of truth check before a session relies on yishuship.

The key command is `scripts/sync-local.sh --check-remote` for inspection and `scripts/sync-local.sh --apply` for safe refresh.

## Decision

- Do: Add a local sync script, correct plugin metadata, expose `/yishuship:*` skills, and document the operating contract.
- Do not do: Build a background daemon, auto-delete files, or silently overwrite dirty local work.
- Evidence: Local inspection showed `yishuship@yishuship` enabled at commit `23d97bd`, 13 `/yishuship:*` links present, but stale `/ship:*` startup text and a wrong repository URL in plugin metadata.
