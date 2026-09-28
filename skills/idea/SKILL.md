---
name: idea
description: "Turns a new product idea, or a wish to make an existing product better, into behaviors users will see, a first slice, and a go / shrink / drop decision for the user. Use when the user wants to build, add, or improve something, including vague wishes such as 'X 用起来不太好，想改改'. Not for errors or crashes, a small edit the user has fully specified, or ideas already in progress (use next)."
when_to_use: "我有个想法, 想做个, 新功能, 新产品, 能不能做一个, 想改改, 不太好用, 体验不好, 想优化, 想让它更好, idea, new feature, I want to build, make it better, improve"
---

# yishuship: idea

Turn a raw idea into something the user can decide on and cannot lose.

## Outcome Contract

- Outcome: the user knows who this is for, what problem it solves, what users
  will be able to do, the smallest first slice that proves it, what it will
  not do, and how much they are willing to spend on it; then decides
  go / shrink / drop.
- Done when: `.ship/ideas/<slug>.md` and `.ship/PROJECT.md` exist in the
  project (see `../shared/progress-file.md`), the project is registered, and the user has
  been asked for the decision in the layout of `../shared/asking.md` (read it
  before writing the question).
- Evidence: the user's own words, the project's current state (read the repo,
  its AGENTS.md / CLAUDE.md / CONTEXT.md), and, when the problem is not new,
  how two or three existing products or tools already solve it. Look them up;
  do not describe them from memory.
- Output: the decision question. No code, no scaffolding.

## Shaping

1. **Place it**: find its project (or a new one) yourself; ask only if two fit.
   Read its `.ship/PROJECT.md`; if there is none, create it now
   (`../shared/progress-file.md`): the new idea is judged against what the
   product already does and owes.
2. **Understand before proposing.** Ask at most three questions per round,
   each with your recommended answer. Anything the repo, the product, or a
   public source can answer, answer yourself. Stop asking once the behaviors
   can be written down. A round of questions is a stop like any other: write
   the progress file first (`status: shaping`, the questions in `waiting`,
   only the sections you already know), so nothing lives only in the chat,
   then open the page beside the terminal (`../shared/asking.md`).
   Show what you understood: one or two mocks built on the user's real
   product or content, what users would see, listed under `## 看得见` as
   `### 你是说这样吗` (`- <what it shows> · ../evidence/<dir>/<file>`).
   When the real material is not in the project (their name, texts, images,
   data), ask for it or for the path to take it from; placeholder content
   only when the user says an example is enough, and label it 示例.
   How to question them may come from a matched index row (a grilling
   method, say); when to stop and what the page shows stays with this file.
   Set the appetite, how much this is worth (a slice, a few days, a few
   weeks), before the solution: it shapes the solution, not the other way
   round. Ask when it is not obvious; for a small idea, propose
   one slice as the limit. Record it in `appetite` as a limit, not an estimate.
3. **Write behaviors in product words**: `用户<做什么> → 看到<什么>`. Each one
   must be checkable in the running product. Mark which are settled and which
   still have a choice for the user. Behaviors that cross screens or branch:
   draw them, per the index row for showing structure.
4. **Challenge it once.** Name the minimal version in one line. If an existing
   feature, tool, or something the user already has covers most of it, say so
   plainly; recommending not to build is a valid outcome. Name the one
   assumption most likely to sink the idea (usually: will they use it)
   and the cheapest way to check it; if the check costs less than the first
   slice, make the check the first slice.
5. **Cut the first slice**: the thinnest end-to-end behavior a user could try.
   It must stand on its own if nothing after it ships. List later slices in one
   line each; do not plan them. Write what this idea will not do, so later
   slices cannot widen it silently.
6. **Say how you will know it worked**: what the user will observe after
   shipping, and `从哪看出来`, the real place it will show: their own use at a
   named moment, a named person to ask, a log line or count the product keeps.
   With few users, asking is enough; something the product has to record is
   built and checked before shipping, not after.
7. **Name the one-way doors** in product terms (data that has to move, formats
   that are costly to change, money or quota spent).
8. **Write the progress file** with `status: waiting`, register the project
   (`python3 <skill-dir>/../../scripts/ideas.py --register <root>`), rerun
   `ideas.py --project <root>`, and ask.

## Hard Rules

- Technical design only as deep as it changes a user decision; the rest belongs
  to `/yishuship:next`, or to the index row for choosing approaches.
- No placeholders ("待定", "later", "选定后填写") anywhere in the progress
  file. Where a choice is still open, write it for the recommended option and
  mark it as pending; what cannot be settled is a question for the user.
- One idea per progress file. A second idea surfacing in the conversation gets
  its own file or goes to 遗留, never folded in silently.

## Output

One stop the user can judge without remembering anything said before. From
top to bottom, in their language, the way that fits this idea:

- what they asked for, in their words, and what they answered so far;
- what the first slice will look like (a picture) and what users will be
  able to do with it;
- what it leaves out, and what it costs (time, money, anything only they
  can do);
- one full-sentence question, such as 照上面这个样子，先把这一块做出来，可以吗？,
  with the smaller version and not building at all offered in sentences
  too, your recommendation marked.

Then any one-way doors in the asking layout, and the path of the progress file.
It goes under `## 等你决定` for the page; the terminal prints it only when
`page.py` says `no page`, else one line (`../shared/asking.md`).
