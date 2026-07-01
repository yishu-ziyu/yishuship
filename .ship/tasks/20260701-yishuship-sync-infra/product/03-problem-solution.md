# Problem and Solution

## Problem Summary

The user has a real yishuship repository, but Claude Code can lag behind it.

The lag can happen because plugin cache, marketplace config, skill symlinks, and session startup hints are separate surfaces.

When they disagree, the agent may say yishuship has no skill, use old `/ship:*` language, or rely on project-local commands instead of the global plugin.

## Severity and Frequency

Severity is high because yishuship is the process layer for long-running work.

If the process layer is stale, every project using it can start from the wrong route.

Frequency is moderate: it appears whenever yishuship itself changes or when Claude Code plugin installation is refreshed incompletely.

## Solution Idea

Create a small local sync command that checks the five surfaces together:

- Source checkout head.
- Remote `origin/main` head.
- Claude Code installed plugin commit.
- Namespaced `/yishuship:*` skill links.
- Stale unprefixed skill links.

The command should default to read-only checking.

With `--apply`, it can pull when the repo is clean, refresh the Claude Code plugin, and repair links.

## Evidence

`scripts/sync-local.sh --check-remote` currently reports:

```text
repo_head: 23d97bd
remote_main: 23d97bd
installed_plugin: 23d97bd
skill_links: 13/13
update_needed: no
```

It also correctly reports `working_tree: dirty` because this infrastructure change is in progress.

## Non-goals

Do not run a background daemon by default.

Do not pull over local uncommitted changes.

Do not remove the original heliohq marketplace unless the user explicitly asks, because it is a separate installed source and deletion is irreversible enough to require confirmation.

Do not turn session startup into a large document dump.
