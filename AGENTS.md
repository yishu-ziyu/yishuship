# yishuship agent guide

`CLAUDE.md` is a symlink to this file. Edit this one.

## What this is

A Claude Code plugin that follows one product idea from a sentence to users
being able to use it. The user is a product person: they own what users see
and do; the agent owns everything inside the box. The user types one command,
`/yishuship`: `skills/yishuship` reads `scripts/ideas.py --route` and hands off
to one of three steps (also invocable directly):

- `skills/idea` — shape a new idea into behaviors, a first slice, a decision.
- `skills/next` — move the current idea one verified step (slice, decision, ship).
- `skills/ideas` — list every idea across projects.

`hooks/register.ts` runs inside Claude Code (early access: only with
`CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1`): it watches every step of the agent,
writes `.ship/live/` (kept out of git), and draws what the user must do now
above the input box. It also registers three tools. `board` shows a live board above the
prompt: the behaviors the user confirmed, what the agent does now and for
which behavior, a rhythm strip of its tool calls, edits outside the planned
areas, and for an optimization task the metric as aligned step bars against the
target; a number counts as measured only when the module saw its command run
this session, and which steps to point out is the agent's call, its reason
shown. `review` serves a folder of agent-made pages through `scripts/review.py`
and opens one beside the terminal: every part gets a 「说一句」 button, and so
do words the user selects or one element they click; each comment comes back to
the agent as a prompt with what it points at, and `reply` puts the answer next
to that part. The page reloads itself, at the same place, when the agent
changes a file in its folder. The terminal is for status; anything to look at closely goes on a
page (in this terminal, clicks do not reach the band and pictures there are too
small to read). In a project without `.ship/ideas` only the board shows. `scripts/page.py` reads the same files for the page and
tells cmux (sidebar status, a flash, typing a confirmed reply). Without the
flag everything falls back to the progress file.

The user's corrections are kept per project: after every turn the hooks
module has a small model read what the user said against the agent's last
answer and suggests a rule for each correction (`.ship/记录.jsonl`, committed,
no quotes; their words stay in `.ship/live/原话.jsonl`). Rules the user
confirms on the page go to `.ship/规则.md` (this project) or
`~/.yishuship/规则.md` (every project) and into every turn's context.

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
