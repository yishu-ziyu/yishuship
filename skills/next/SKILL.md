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
- Done when: the progress file and the project file reflect reality, and the
  progress file names exactly one next step.
- Evidence: `../shared/done.md`; the running product proves it, tests support.
- Output: the done report and/or the decision question.

## Every run

1. **Find the idea.** Read `.ship/PROJECT.md` (create it if missing, per
   `../shared/progress-file.md`), then `.ship/ideas/*.md`. Several
   active: take the most recently updated that is not paused, and name it. None:
   say so and suggest `/yishuship:idea`.
2. **Reconcile** with git log, tags and the working tree. Where the file and
   reality disagree, reality wins: fix the file and say what changed.
3. **Waiting on the user?** If `waiting` is set and not answered in this
   conversation, ask that one question again and stop.

## A slice

4. **Settle the behaviors and the design.** Any behavior of this slice that
   still has a choice goes to the user, batched. Read `../shared/asking.md`
   before writing any question and use its layout exactly; a plain numbered
   list is not it. For a bug, find the root cause first (index row for errors).
   Write the slice's design under `## 设计` as in the template: what changes and
   why, the alternative you rejected, and a diagram rendered as a picture (index
   row for showing structure). Unless the change is one obvious edit, the design
   goes to the user in the same stop as the behaviors, as a question whose
   picture is that diagram (an HTML picture under `## 看得见`, not text art).
   Everything else inside the box is yours.
5. **Read the project's own rules first** (AGENTS.md, CLAUDE.md, CONTEXT.md,
   ADRs) and follow them. New domain terms go into CONTEXT.md if it exists.
6. **Build it the way this slice calls for.** Match the slice against the
   index rows at three levels: `<skill-dir>/../../INDEX.md` (general),
   `~/.yishuship/INDEX.md` (the user's, cross-project), and
   `<project>/.ship/INDEX.md` (this project only). Before building, tell the
   user in one line which rows matched and what each gave, or that none did,
   then show the shape of the change (index row for showing structure).
   The matched entries decide the method, including whether test-first is
   worth it; a small, obvious change does not earn a whole method.
7. **First green is not done.** Run it on real data, not only your fixtures;
   where possible check with something independent of the implementation.
8. **Verify in the running product**, before and after, using the index entry
   for that kind of product, then run the independent check in
   `../shared/done.md`. Show images with the evidence script.
   Then rerun the `复查` of every behavior an earlier slice proved
   (`ideas.py --trace .` lists them). One that no longer holds blocks done,
   unless a decided behavior of this slice changed it on purpose: say so and
   update that check.
9. **Report** per `../shared/done.md`, then update the progress file: slice
   done with evidence, next slice, `waiting`, `updated`; then the project
   file: structure picture and screenshots where this slice changed them, and
   `ideas.py --project .` until it lists no problem.

## Shipping

When the slices cover the idea's behaviors, set `status: shipping`.
If `ship_bar` is empty, ask what "users can use it" means for this project
(installable build, public URL, store listing, a friend using it). Do what the
bar requires, with the index entry for releases, and whatever `从哪看出来`
needs the product to record (check it records), then verify from a new user's
side: install the built artifact or open the public URL fresh. Only then
`status: shipped`, with `shipped` today and `review_on` a week later unless
the user wants another day: that is when `/yishuship` asks whether it worked.

## Hard Rules

- One slice per run unless the user says to keep going.
- When the work reaches the idea's `appetite`, stop and ask whether it is
  still worth more; never extend it silently.
- List the slice's things (its behaviors, in words) as checkboxes indented
  under it in 进度. While you work, `now` says `<step> · <that thing, copied>`,
  step one of 定行为 在写 在验证 独立检查 汇报; `next` says when and why you
  will next need the user. Rewrite both at every change; empty `now` before you stop.
- Never widen scope silently. Anything found outside the slice goes to 遗留 or
  becomes its own idea.
- Never touch, stash, or move the user's uncommitted work.
- Stop only at a real decision, a real blocker, or the end of a slice; say which.
