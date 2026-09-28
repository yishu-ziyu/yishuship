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
  2. the work got harder than planned: the user shown the product as it is
     now and asked 满意吗, or asked a one-way-door decision;
  3. the idea meets its ship bar and users can use it.
- Done when: the progress file and the project file reflect reality, and the
  progress file names exactly one next step.
- Evidence: `../shared/done.md`; the running product proves it, tests support.
- Output: what the product looks like now, and 满意吗.

## Every run

1. **Find the idea.** Read `.ship/PROJECT.md` (create it if missing, per
   `../shared/progress-file.md`), then `.ship/ideas/*.md`. Several
   active: take the most recently updated that is not paused, and name it. None:
   say so and suggest `/yishuship:idea`.
2. **Reconcile** with git log, tags and the working tree. Where the file and
   reality disagree, reality wins: fix the file and say what changed.
3. **Waiting on the user?** First read `## 你的反馈`: the page writes the
   user's answer and the spots they pointed at there (`../shared/asking.md`);
   an unticked line is their reply, as if typed. If `waiting` is still set and
   not answered in this conversation, ask that one question again and stop.

## A slice

4. **Build first, then show.** Where a behavior of this slice still has a
   choice, build the recommended option in its smallest version; the user
   judges it on the running product, not as an A/B question beforehand. Ask
   before building only for one-way doors (see `../shared/asking.md`). For a
   bug, find the root cause first (index row for errors). Write the slice's
   design under `## 设计` as in the template: what changes and why, the
   alternative you rejected, and pictures the user can judge: how it is put
   together (an architecture diagram, index row for showing structure) and,
   when users will see something new, how it looks. Never show file names or
   line ranges. Material the product needs and the project lacks (texts,
   images, data): ask the user for it or for a path; placeholders only if
   they say an example is enough. No git yet: create the repository yourself.
   Everything inside the box is yours.
   Keep the slice small enough that the user sees something new often; a
   slice that grows gets cut, and the part that works is shown.
5. **Read the project's own rules first** (AGENTS.md, CLAUDE.md, CONTEXT.md,
   ADRs) and follow them. New domain terms go into CONTEXT.md if it exists.
6. **Build it the way this slice calls for.** Match the slice against the
   index rows at three levels: `<skill-dir>/../../INDEX.md` (general),
   `~/.yishuship/INDEX.md` (the user's, cross-project), and
   `<project>/.ship/INDEX.md` (this project only). Before building, tell the
   user which methods you are using and what each gives, by name, so they
   can look them up later, then show the shape of the change (index row for
   showing structure). The first time a kind of work comes up that no row
   covers, ask whether to connect a mature open method for it (for example
   Matt Pocock's skills: prototype for looks, tdd, diagnosing-bugs,
   code-review, wizard for steps only the user can do); on yes, install it
   and add the row to `~/.yishuship/INDEX.md`. The method decides how a step
   is done; when to stop and what to show stays with yishuship.
   The matched entries decide the method, including whether test-first is
   worth it; a small, obvious change does not earn a whole method.
7. **First green is not done.** Run it on real data, not only your fixtures;
   where possible check with something independent of the implementation.
8. **Verify in the running product**, before and after, using the index entry
   for that kind of product, then run the independent check in
   `../shared/done.md`. Embed the images in `## 证据`; the page shows them.
   Then rerun the `复查` of every behavior an earlier slice proved
   (`ideas.py --trace .` lists them). One that no longer holds blocks done,
   unless a decided behavior of this slice changed it on purpose: say so and
   update that check.
9. **Report** per `../shared/done.md`, ending with 满意吗 in the show layout of
   `../shared/asking.md`. If `page.py` said the page is open, the report goes
   into the slice's `## 证据` note and the terminal gets one line in the
   user's language (`第一块做完了，看旁边的页面。满意回「满意」，不行回「不行」。`);
   only after `no page` is the report printed. Then update the progress file: slice
   done with evidence, next slice, `waiting`, `updated`; then the project
   file: structure picture and screenshots where this slice changed them, and
   `ideas.py --project .` until it lists no problem.

## Shipping

Shipped means: someone who is not the user gets it from where they would
normally get such a thing, opens it, and can use it. When the slices cover
the idea's behaviors, set `status: shipping`. How to get there depends on
this product and its people; judge it here, do not assume a kind of product.

1. **Agree on the bar.** If `ship_bar` is empty, ask what it means here,
   in the stop layout: the realistic levels for this product, cheapest
   first, each with what the user gets and what it costs (money, accounts,
   steps only they can do), and who it is for (where they are: a site may
   not open for them without a proxy, say). Recommend the cheapest level a
   real person can use.
2. **Prepare, not yet public.** Build what the bar requires, with the
   matching method (index), and whatever `从哪看出来` needs the product to
   record. Put it in a real environment that is not announced yet. Steps
   only the user can do (accounts, payment, signing, a fresh machine
   account): guide them one at a time and wait.
3. **Real-world acceptance.** A user isolated from the build, knowing only
   the idea's behaviors, gets the product through its real entry in that
   environment and does those things; record it (screenshots or a
   recording) into the evidence, and check each claim against it. Use
   whatever tools reach the real entry; if none does, say so plainly and ask
   the user to do that part, never substitute the source or a mock. Show
   it and ask 满意吗.
4. **Ship.** Make it public as agreed, check it opens from the outside, then
   `status: shipped`, with `shipped` today and `review_on` a week later
   unless the user wants another day: that is when `/yishuship` asks whether
   it worked.

## Hard Rules

- One slice per run unless the user says to keep going.
- When the work reaches the idea's `appetite`, stop and ask whether it is
  still worth more; never extend it silently.
- List the slice's things (its behaviors, in words) as checkboxes indented
  under it in 进度. While you work, `now` says `<step> · <that thing, copied>`,
  step one of 定行为 在写 在验证 独立检查 汇报 验收 上线; `next` says when and why you
  will next need the user. Rewrite both at every change; empty `now` before you stop.
- Never widen scope silently. Anything found outside the slice goes to 遗留 or
  becomes its own idea.
- Never touch, stash, or move the user's uncommitted work.
- Stop at the end of a slice, at a one-way door, or as soon as it is harder
  than planned: the planned approach fails and must change, what users will
  see is going to differ from what was agreed, or about half the appetite is
  spent without the slice done. Each of these stops shows the product as it is
  now and asks 满意吗 (`../shared/asking.md`); say which stop it is.
