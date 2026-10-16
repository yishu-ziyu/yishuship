# yishuship agent guide

`CLAUDE.md` is a symlink to this file. Edit this one.

## What this is

A Claude Code plugin that follows one product idea from a sentence to users
being able to use it. The user owns what users see and do; the agent owns
everything inside the box. Read the code for how: `skills/` (what the agent is
told), `hooks/register.ts` (what runs inside Claude Code; only with
`CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1`), `scripts/` (everything deterministic).

## Decisions the code does not show

- The terminal is for short lines; anything the user should look at goes on
  the page beside it. In this terminal clicks do not reach the band, and
  pictures there are too small to read.
- The user's corrections are committed as rules without their words; what
  they said stays in `.ship/live/`, out of git.
- Engineering habits (debugging, planning, review, reading) come from Waza
  (`hunt`, `think`, `check`, `read`), installed separately. Do not
  re-implement them here; refer to them only by skill name.
- No docs that explain how the code works: make the code say it. Where things
  stand is read from git, tests and the running product, not written by hand.
  Keep only what code cannot hold: the user's decisions, reasons and intent,
  short.

## Rules for changing it

- Skills hold management only. How a kind of work is done (test-first,
  design rules, release steps, app verification) goes behind an INDEX row,
  never into a skill. A row names its moment ("when ..."), not its topic.
- Give the model the target, not the path: each SKILL.md starts with an
  outcome contract; keep process to what changes behavior.
- Keep skills short: every line is loaded on each run, and v2 drowned in rules.
  A new line must earn its place by changing behavior (check with `evals/`);
  there is no fixed line count, and never compress wording just to fit one.
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
python3 -m py_compile scripts/*.py
bash -n scripts/*.sh
python3 scripts/check-index.py              # every index row still resolves
python3 scripts/ideas.py                    # overview renders
echo '{"cwd":"'"$PWD"'"}' | bash scripts/statusline.sh   # no line unless an idea is active here
HOME=$(mktemp -d) bash scripts/install.sh --no-obsidian </dev/null   # fresh-user install still works
wc -l skills/*/*.md | tail -1      # size check, not a hard limit
CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1 claude plugin validate "$PWD/.claude-plugin/plugin.json"   # hooks module loads
npx -y -p typescript@5 tsc -p .   # type-check hooks/; tsconfig.json extends the types Claude Code writes beside a plugin it loads from this folder
```

Behavior changes to the skills are measured with the eval suite before and
after the change: `python3 evals/run.py` (cases in `evals/cases/`, fixtures in
`evals/fixtures/`, reports in `evals/results/`). A change that does not raise
the score, or lowers any case, is not an improvement. Every run is isolated
from the user's own setup; see the runner's docstring. Beyond the suite, use
the skills on a real idea and read the transcript. A read-only run works well:
`claude -p --permission-mode plan "/yishuship:next"` inside a project that has
an idea in progress.

## Shipping a change to the installed plugin

Installed as a plugin, Claude Code loads a copy taken at install or update
time (`~/.claude/plugins/cache/yishuship/yishuship/<version>`), not this
checkout: edits here reach it only through a version bump and
`claude plugin update`. To run this checkout itself, name it in
`CLAUDE_CODE_PLUGIN_DIRS` (the `env` block of `~/.claude/settings.json`) and
disable `yishuship@yishuship`; the folder is then watched and reloads on save. For a release, bump `version` in both
`.claude-plugin/plugin.json` and `marketplace.json` so copies installed from
GitHub pick it up with `claude plugin update yishuship@yishuship`. The status
line script always runs from this checkout.
