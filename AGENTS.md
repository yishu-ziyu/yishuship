# yishuship agent guide

`CLAUDE.md` is a symlink to this file. Edit this one.

## What this is

A Claude Code plugin that follows one product idea from a sentence to users
being able to use it. The user is a product person: they own what users see
and do; the agent owns everything inside the box. Three user-invoked skills:

- `skills/idea` — shape a new idea into behaviors, a first slice, a decision.
- `skills/next` — move the current idea one verified step (slice, decision, ship).
- `skills/ideas` — list every idea across projects.

`skills/shared/*.md` hold the management rules all three follow: when and how
to stop and ask, what "done" must show, the progress file. `INDEX.md` maps each
moment of the work (writing code, designing, a bug, a release, verifying a
running app) to where the method lives; `~/.yishuship/INDEX.md` holds the same
kind of rows for paths on the user's machine. `docs/` holds yishuship's own
method notes that the index points at. `scripts/` hold everything
deterministic.

Engineering habits (debugging, planning, review, reading) come from Waza
(`hunt`, `think`, `check`, `read`) installed separately; do not re-implement
them here, and refer to them only by skill name.

## Rules for changing it

- Skills hold management only. How a kind of work is done (test-first,
  design rules, release steps, app verification) goes behind an INDEX row,
  never into a skill. A row names its moment ("when ..."), not its topic.
- Give the model the target, not the path: each SKILL.md starts with an
  outcome contract; keep process to what changes behavior.
- Budget: all `skills/**/*.md` together stay under 400 lines. Adding a line
  means finding one to remove. Check with `wc -l skills/*/*.md | tail -1`.
- Deterministic work (listing, parsing, status, page generation, idle checks)
  goes in `scripts/`, stdlib only, no new dependencies.
- No hooks that block the user or the agent. Information may be shown; nothing
  may refuse.
- No invented names for mechanisms in anything the user reads. Say what it does.
- A lesson earns a line only if it came from a real run and prevents a repeat;
  write the rule, drop the story.
- Commit messages: `<type>: <description>`; no AI co-author lines.

## Checking a change

```bash
python3 -m py_compile scripts/ideas.py scripts/check-index.py
bash -n scripts/*.sh
python3 scripts/check-index.py              # every index row still resolves
python3 scripts/ideas.py                    # overview renders
echo '{"cwd":"'"$PWD"'"}' | bash scripts/statusline.sh   # no line unless an idea is active here
wc -l skills/*/*.md | tail -1      # under 400
```

Behavior changes to the skills are verified by using them on a real idea and
reading the transcript, not by keyword checks. A read-only run works well:
`claude -p --permission-mode plan "/yishuship:next"` inside a project that has
an idea in progress.

## Shipping a change to the installed plugin

Claude Code installs a copy under `~/.claude/plugins/cache/yishuship/`, so edits
here do nothing until the plugin is updated: bump `version` in both
`.claude-plugin/plugin.json` and `marketplace.json`, then
`claude plugin update yishuship@yishuship` and start a new session. The status
line script runs from this checkout directly and needs no update.
