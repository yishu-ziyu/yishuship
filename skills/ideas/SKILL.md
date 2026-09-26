---
name: ideas
description: "Lists every idea in progress across the user's projects: where each stands, which ones wait on the user, which went quiet. Use when the user runs /yishuship:ideas. Not for starting or continuing an idea."
disable-model-invocation: true
---

# yishuship: ideas

Show the user every idea still alive, so nothing is forgotten and the next
choice is obvious.

## Outcome Contract

- Outcome: the user sees, at a glance, each idea's project, step, and whether
  it waits on them, and gets one recommendation for what to continue.
- Done when: the list comes from the progress files on disk, not from memory.
- Output: the list, then one line: which idea to continue and why.

## Steps

1. Run `python3 <skill-dir>/../../scripts/ideas.py`. It reads every registered
   project's `.ship/ideas/*.md`.
2. Present it as the script prints it: waiting on the user first, then in
   progress, then quiet for over 7 days, then shipped in the last 30 days.
   Dropped and older shipped ideas stay hidden unless asked.
3. Recommend one idea to continue: the one blocked on the user if any, else the
   one closest to its ship bar. Tell the user to `cd` there and run
   `/yishuship:next`.

Read only. Do not edit progress files here; if one looks wrong, say so and let
`/yishuship:next` reconcile it in that project.
