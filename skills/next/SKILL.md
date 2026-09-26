---
name: next
description: "Moves the current idea one verified step toward users being able to use it: next slice, next decision, or shipping. Use when the user runs /yishuship:next in a project with an idea in progress. Not for new ideas (use idea)."
disable-model-invocation: true
---

# yishuship: next

The user owns what users see; you own everything inside the box. Each run moves
one idea one step and leaves the progress file true.

## Outcome Contract

- Outcome: one of three, whichever comes first:
  1. a slice's behaviors verified in the running product, with before and
     after evidence shown to the user;
  2. the user asked for a decision only they can make;
  3. the idea meets its ship bar and users can use it.
- Done when: the progress file reflects reality and names exactly one next step.
- Evidence: see `../shared/done.md`. Tests and builds support the claim; the
  running product proves it.
- Output: the done report and/or the decision question.

## Every run

1. **Find the idea.** Read `.ship/ideas/*.md` in the current project. Several
   active: take the most recently updated that is not paused, and name it. None:
   say so and suggest `/yishuship:idea`.
2. **Reconcile.** Check git log, tags, the working tree, and whatever the file
   claims shipped. Where the file and reality disagree, reality wins; fix the
   file and tell the user what changed.
3. **Waiting on the user?** If `waiting` is set and not answered in this
   conversation, ask that one question again and stop.

## A slice

4. **Settle the behaviors.** Any behavior of this slice that still has a choice
   goes to the user, batched, in the layout of `../shared/asking.md`. Decide
   everything inside the box yourself.
5. **Read the project's own rules first** (AGENTS.md, CLAUDE.md, CONTEXT.md,
   ADRs) and follow them. New domain terms go into CONTEXT.md if it exists.
6. **Build it the way this slice calls for.** Open the entries of
   `<skill-dir>/../../INDEX.md` and `~/.yishuship/INDEX.md` whose moment has
   come (writing code, designing a screen, a bug, an AI capability) and follow
   them. Those decide the method, including whether this slice is worth
   test-first; do not import a whole method for a small, obvious change.
7. **First green is not done.** Run it on real data, not only your fixtures;
   where possible check with something independent of the implementation.
8. **Verify in the running product**, before and after, using the index entry
   for that kind of product. Show images with the evidence script.
9. **Report** per `../shared/done.md`, then update the progress file: slice
   done with evidence, next slice, `waiting`, `updated`.

Commits and pushes happen only after the user says so for this slice; ask
together with the next decision. Commit messages: `<type>: <description>`,
no AI co-author lines.

## Shipping

When the slices cover the idea's behaviors, set `status: shipping`.
If `ship_bar` is empty, ask what "users can use it" means for this project
(installable build, public URL, store listing, a friend using it). Do what the
bar requires, with the index entry for releases, then verify from a new user's
side: install the built artifact or open the public URL fresh. Only then
`status: shipped`.

## Hard Rules

- One slice per run unless the user says to keep going.
- Never widen scope silently. Anything found outside the slice goes to 遗留 or
  becomes its own idea.
- Never touch, stash, or move the user's uncommitted work.
- Stop only at a real decision, a real blocker, or the end of the slice; say
  which.
