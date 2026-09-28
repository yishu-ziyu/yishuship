# The progress file and the project file

One file per idea at `<project>/.ship/ideas/<slug>.md`, and one file per
project at `<project>/.ship/PROJECT.md`. It is how the work
survives a closed session, how the scripts know where every idea stands, and
what the user reads when they come back after a week. Chat is not memory; if
it matters next time, it goes here.

The layout is in `<skill-dir>/../../docs/progress-file-template.md`: read it
before creating a file or changing its structure. It has three parts: 意图
(why and what; once the user settled it, change it only with a line in 决定),
设计 (how, per slice), 任务 (where it stands).

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
- While a question waits, `## 看得见` holds its pictures, as in the template:
  one per option (what the product looks like or does under it) and one per
  thing the question names, boxed on a real screenshot. Screenshots come from
  the running product; a mock is a small HTML file in the evidence folder built
  from real content and labeled 示意. Before asking, run
  `python3 <skill-dir>/../../scripts/ideas.py --visuals .`: every option and
  every named thing has a picture and no file is missing. Clear it with `waiting`.
- `kind: bug` marks a bug file: `## 现象` and `## 应该怎样` stand in for 为什么做
  and 用户能看到的行为; the rest is the same. Its root cause goes under `## 设计`.
- `## 设计` holds one `### <slice>` per slice: the change in two or three
  sentences a product person can follow, the rejected alternative, a diagram
  picture, and 你确认了 <date> once the user agreed.
- Link every design, slice and evidence note to the behaviors it is for, by
  number in the order they are listed: `服务：行为1、行为3` on a design or a
  slice, `证明：行为2` on an evidence note. A tick on a behavior means decided,
  never done; what proves it is the evidence that names it, and its `复查`
  line is how any later slice proves it again. Before you stop,
  run `python3 <skill-dir>/../../scripts/ideas.py --trace .` and close or report
  every gap it lists (a done slice whose behavior nothing proves, a design or
  slice that serves no behavior, a design the user has not confirmed, evidence
  with no `复查`).
- A 遗留 item that gets dealt with is ticked `- [x]` with where; one bigger
  than a note becomes its own idea or bug file.
- Record decisions with their reason. Embed before/after screenshots under
  `## 证据`; the user should not have to open a folder.
- Keep `## 问题`: what this idea does not yet know, one line each as in the
  template, the riskiest assumption first. Close one only with evidence seen
  this session and name its source (你试过 / 实测 / 你定的); a simulation or an
  inference leaves it open and says so. What proves a closed one goes under
  `## 证据` as `### <the question>`: the finding in one line, numbers, images.

## The project file

`.ship/PROJECT.md` is how anyone, a new session, another agent, the user after
a month, picks up the whole project instead of one idea.
`python3 <skill-dir>/../../scripts/ideas.py --project <root>` creates it when
missing and regenerates its lower half from the idea files: what users can do
now (every proven behavior with its `复查`), every idea, every open 遗留 item.
Never edit that half by hand. The upper half is yours, from the repo and the
running product, never from memory:

- `这是什么`: who it is for and what it does, two or three lines, naming the
  file it came from.
- `怎么搭的`: one picture of the parts and how they call each other, as text
  art in a code block (the page beside the terminal shows it as is); update
  it when a slice changes the structure.
- `界面现在长什么样`: one line per screen the user sees,
  `- <界面> · screens/<name>.png · <date>`, a screenshot of the running
  product in `.ship/screens/` (for a command-line tool, its real output saved
  as `.txt`); replace it when a slice changes that screen.

The page beside the terminal shows it under the current idea. Read it before
any idea's work. Before you stop, update the upper half where
it changed, rerun the script, and fix every problem it lists.
