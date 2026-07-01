# Research and Current State

## Scenario Research

The user works through Claude Code sessions and expects the agent to know the current project, current progress, and next suggested step at startup.

For yishuship, the important runtime objects are local and concrete: Git repository state, Claude Code plugin installation, skill discovery, project `.ship` state, and persistent memory.

The most common failure mode is not a code bug.

It is stale context: the repository was updated, but Claude Code is still using an older plugin cache or an older skill namespace.

## Current Workflow

Current local source checkout:

- Path: `/Users/mahaoxuan/Developer/yishuship`
- Origin: `https://github.com/yishu-ziyu/ship.git`
- Branch: `main`
- Local head at inspection: `23d97bd`
- Remote `origin/main` at inspection: `23d97bd`

Current Claude Code plugin state:

- Plugin ID: `yishuship@yishuship`
- Enabled: yes
- Installed cache: `/Users/mahaoxuan/.claude/plugins/cache/yishuship/yishuship/0.1.0`
- Installed commit at inspection: `23d97bd`

Current skill exposure:

- `/yishuship:arch-design`
- `/yishuship:auto`
- `/yishuship:design`
- `/yishuship:dev`
- `/yishuship:e2e`
- `/yishuship:handoff`
- `/yishuship:pm-intake`
- `/yishuship:qa`
- `/yishuship:refactor`
- `/yishuship:review`
- `/yishuship:use-yishuship`
- `/yishuship:visual-design`
- `/yishuship:write-docs`

## Existing Alternatives

Manual commands already work:

```bash
git -C /Users/mahaoxuan/Developer/yishuship pull origin main
claude plugin marketplace update yishuship
claude plugin update --scope user yishuship@yishuship
```

They are too easy to forget and do not verify skill links.

## Evidence

The user reported that yishuship skills were not visible.

Inspection found an empty legacy `~/.claude/skills/use-yishuship` directory and stale `heliohq/ship` references in cache/config, while the real updated repository already contained `skills/use-yishuship/SKILL.md`.

A subagent refreshed plugin installation and created 13 namespaced symlinks.

A direct check confirmed those 13 links and the enabled plugin.
