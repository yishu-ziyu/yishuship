# Model, Flow, and Roles

## Business Data Model

| Object | Meaning | Source of truth |
|--------|---------|-----------------|
| `source_repo` | Local checkout of the user's yishuship project | `/Users/mahaoxuan/Developer/yishuship` |
| `remote_head` | Latest known `origin/main` commit | `git ls-remote origin refs/heads/main` |
| `local_head` | Current local checkout commit | `git rev-parse HEAD` |
| `plugin_install` | Claude Code installed plugin record | `~/.claude/plugins/installed_plugins.json` |
| `plugin_cache` | Files Claude Code loads for the installed plugin | `~/.claude/plugins/cache/yishuship/yishuship/<version>` |
| `skill_link` | Namespaced skill entry visible to Claude Code | `~/.claude/skills/yishuship:<skill>` |
| `project_state` | Per-project yishuship work state | `<project>/.ship/` |
| `durable_memory` | Cross-session user and project facts | `~/.claude/projects/-/memory/` |

## Object Relationships

`source_repo` produces plugin metadata and skill files.

Claude Code copies `source_repo` into `plugin_cache` during plugin install or update.

`skill_link` points directly to `source_repo/skills/<skill>` for immediate namespaced discovery.

`project_state` is separate and should not be overwritten by plugin sync.

`durable_memory` records only non-obvious long-term facts, not every task file.

## Workflow

1. Check `source_repo`, `remote_head`, `plugin_install`, and `skill_link` together.
2. If all match, use `/yishuship:use-yishuship`.
3. If `remote_head` differs and the repo is clean, apply sync.
4. If the repo is dirty, stop before pulling and ask whether to commit, stash, or skip.
5. After a meaningful infrastructure correction, update durable memory.

## Roles and Handoffs

The user owns the product process and decides whether to automate more aggressively.

Claude Code runs checks, explains drift, and applies safe local refreshes.

Subagents may inspect or verify, but should not delete or overwrite user files without explicit approval.
