# Technical and Project Plan

## Technical Plan

Implement a Bash sync script because the surrounding plugin infrastructure already uses shell scripts.

The script is located at `scripts/sync-local.sh`.

It reads local git state, Claude Code plugin JSON state, and symlink state.

It calls Claude Code plugin commands only in `--apply` mode.

## Architecture Decision

Use a local command instead of a background watcher.

This keeps the first version safe and inspectable.

A background watcher can be added later only after the user explicitly approves always-on automation.

## Project Plan

Completed in this task:

- Add `scripts/sync-local.sh`.
- Correct `.claude-plugin/plugin.json` repository URL.
- Correct SessionStart routing hint from `/ship:*` to `/yishuship:*`.
- Include a compact sync status in SessionStart output.
- Reinstall yishuship plugin to refresh the cache.
- Record product lifecycle artifacts for this infrastructure change.

Remaining follow-up:

- Replace remaining internal prompt wording that says `/ship:auto` where it should say `/yishuship:auto`.
- Decide whether to remove original heliohq marketplace entries.
- Decide whether to add an alias or LaunchAgent.

## Milestones

1. Immediate local refresh: done.
2. Stable manual sync command: done.
3. Startup status visibility: done.
4. Full stale wording cleanup: follow-up task.

## Risks and Mitigations

Risk: Claude Code plugin update may not copy dirty local changes into cache.

Mitigation: reinstall plugin after local metadata and hook changes.

Risk: Pulling can overwrite local work.

Mitigation: skip pull when `git status --porcelain` is not empty.

Risk: Too much SessionStart context creates noise.

Mitigation: inject only five sync lines.
