---
name: idea
description: "Turns a new product idea into behaviors users will see, a first slice, and a go / shrink / drop decision for the user. Use when the user brings a new idea or feature to build. Not for bugs or ideas already in progress (use next)."
when_to_use: "我有个想法, 想做个, 新功能, 新产品, 能不能做一个, idea, new feature, I want to build"
---

# yishuship: idea

Turn a raw idea into something the user can decide on, and make it impossible
to lose.

## Outcome Contract

- Outcome: the user knows who this is for, what problem it solves, what users
  will be able to do, the smallest first slice that proves it, and what it
  costs; then decides go / shrink / drop.
- Done when: `.ship/ideas/<slug>.md` exists in the project (see
  `../shared/progress-file.md`), the project is registered, and the user has
  been asked for the decision in the layout of `../shared/asking.md`.
- Evidence: the user's own words, the project's current state (read the repo,
  its AGENTS.md / CLAUDE.md / CONTEXT.md), and, when the problem is not new,
  how two or three existing products or tools already solve it. Look them up;
  do not describe them from memory.
- Output: the decision question. No code, no scaffolding.

## Shaping

1. **Place it.** Which project does it belong to, or is it a new one? Find the
   repo yourself; ask only if two places are equally plausible.
2. **Understand before proposing.** Ask at most three questions per round,
   each with your recommended answer. Anything the repo, the product, or a
   public source can answer, answer yourself. Stop asking once the behaviors
   can be written down.
3. **Write behaviors in product words**: `用户<做什么> → 看到<什么>`. Each one
   must be checkable in the running product. Mark which are settled and which
   still have a choice for the user.
4. **Challenge it once.** Name the minimal version in one line. If an existing
   feature, tool, or something the user already has covers most of it, say so
   plainly; recommending not to build is a valid outcome.
5. **Cut the first slice**: the thinnest end-to-end behavior a user could try.
   It must stand on its own if nothing after it ships. List later slices in one
   line each; do not plan them.
6. **Name the one-way doors** in product terms (data that has to move, formats
   that are costly to change, money or quota spent).
7. **Write the progress file** with `status: waiting`, register the project
   (`python3 <skill-dir>/../../scripts/ideas.py --register <root>`), and ask.

## Hard Rules

- Technical design only as deep as it changes a user decision; the rest
  belongs to `/yishuship:next` or Waza `/think` when a slice needs a plan.
- No placeholders ("待定", "later") in the behaviors or the first slice. If
  something cannot be settled, it is a question for the user.
- One idea per progress file. A second idea surfacing in the conversation gets
  its own file or goes to 遗留, never folded in silently.

## Output

The asking layout, with at minimum:

```
①  做不做
   ├─ A  做，先做第一刀：<slice>      ◀ 推荐
   ├─ B  缩小：<smaller version>
   └─ C  不做：<reason>
```

plus any behavior choices and one-way doors, then the path of the progress file.
