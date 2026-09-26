# The progress file

One file per idea at `<project>/.ship/ideas/<slug>.md`. It is how the work
survives a closed session, how the scripts know where every idea stands, and
what the user reads when they come back after a week. Chat is not memory; if
it matters next time, it goes here.

The layout is in `<skill-dir>/../../docs/progress-file-template.md`: read it
before creating a file or changing its structure.

## Rules

- Read it before doing anything; update it before you stop.
- Reconcile it with reality on every read: git log, tags, tests, the running
  product. If the file and reality disagree, reality wins; fix the file and say
  what you corrected.
- Front matter is machine-read by the scripts. Keep the keys exactly as in the
  template. `short` is what the status line shows: at most 8 characters, and
  recognizable on its own. After changing it, regenerate the summary at the top with
  `python3 <skill-dir>/../../scripts/ideas.py --refresh <file>`; never write
  that summary by hand.
- `waiting` is non-empty only while the user owes a decision: the questions in
  one short line in front matter, and the full question block exactly as
  shown to the user under `## 等你决定`. Clear both once answered.
- Record decisions with their reason. Embed before/after screenshots under
  `## 证据`; the user should not have to open a folder.
- Register a new project once:
  `python3 <skill-dir>/../../scripts/ideas.py --register <project-root>`.
  If `~/.yishuship/config` sets `obsidian_dir`, it also links the project's
  ideas and evidence there.
