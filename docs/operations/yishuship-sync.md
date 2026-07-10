# yishuship Sync Operations

## Purpose

Keep every local agent entry point on the **same** yishuship code as the
canonical checkout. Claude Code, Codex, and agents must not drift into private
stale copies.

## Canonical source

```text
/Users/mahaoxuan/Developer/yishuship
```

(override with `YISHUSHIP_ROOT`)

One command manages all surfaces:

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --check
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --apply
```

## Surfaces (unified)

| Surface | Path | How it stays current |
|---------|------|----------------------|
| Source repo | `~/Developer/yishuship` | Git working tree (truth) |
| Claude skills | `~/.claude/skills/yishuship:*` | Symlink → source `skills/` |
| Agents / Trae / many CLIs | `~/.agents/skills/yishuship:*` | Symlink → source `skills/` |
| Claude marketplace | directory marketplace → source repo | Local path marketplace |
| Claude plugin cache | `~/.claude/plugins/cache/yishuship/yishuship/0.1.0` | `--apply` reinstall or mirror |
| Codex personal source | `~/plugins/yishuship` | **Symlink → source repo** |
| Codex plugin cache | `~/.codex/plugins/cache/personal/yishuship/0.1.0` | `--apply` reinstall or mirror |

After a successful `--apply`, skill docs and orchestrator scripts (including
`control/peer-review.md` full-suite gate) match `repo_head` on every surface.

## Quick Check

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --check
```

Healthy output should include:

```text
repo_head: <sha>
claude_plugin_peer_gate: yes
codex_personal_src: ... (symlink->repo)
codex_plugin_peer_gate: yes
claude_skill_links: 14/14
agents_skill_links: 14/14
update_needed: no
```

Optional remote comparison:

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --check-remote
```

`note: local HEAD differs from origin/main` is normal on a feature branch.
That is not a failure of local multi-agent sync.

## Safe Refresh (all agents)

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --apply
```

This will:

1. Use the **current** repo HEAD (does **not** switch branches).
2. Repair skill symlinks in both `~/.claude/skills` and `~/.agents/skills`.
3. Point `~/plugins/yishuship` at the source repo (replace stale directory copies
   with a symlink; old copy moved to `~/plugins/yishuship.bak.<timestamp>`).
4. Refresh Claude Code plugin cache (`yishuship@yishuship`).
5. Refresh Codex personal plugin cache (`yishuship@personal`).
6. If CLI reinstall is incomplete, mirror the repo tree into the cache and stamp
   `.yishuship-synced-from`.

It will not commit, push, or overwrite non-symlink skill paths.

### Optional: also fast-forward main

Only when you intentionally want the checkout on `origin/main`:

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --apply --pull-main
```

Skipped automatically if the working tree is dirty.

## After apply

Restart open Claude Code / Codex / Grok sessions so they reload skills and hooks.

## Session Rule

At the start of work that may use the Ship process, consult `/yishuship:use-yishuship`.

Do not use `/ship:use-ship` for the user's yishuship workflow unless explicitly
comparing against original Ship.
