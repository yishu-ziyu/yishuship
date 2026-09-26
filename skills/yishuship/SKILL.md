---
name: yishuship
description: "The one entry point: decides from the progress files whether to shape a new idea, ask the pending question, continue the current idea, or show every idea. Use when the user types /yishuship, with or without a sentence after it."
disable-model-invocation: true
---

# yishuship

The user types one command. You decide the step; they should never need to
remember which.

## Outcome Contract

- Outcome: the right step runs, and the first line of your reply says which
  idea you picked up and what step it is at.
- Done when: that step's own outcome is met (see the step's SKILL.md).
- Evidence: `python3 <skill-dir>/../../scripts/ideas.py --route "$PWD"`, which
  decides from disk; never from memory of earlier sessions.

## Route

Run the route script first. Then:

1. **The user typed a sentence after the command.** Judge what it is:
   - an answer to the `waiting` question of the current idea (for example
     "1A 2B") → record the decisions in its progress file, clear `waiting`,
     and continue with `../next/SKILL.md`;
   - an instruction about the current idea → continue with
     `../next/SKILL.md`, applying it;
   - a new idea → `../idea/SKILL.md`;
   - asking to switch to another idea by name → make that idea current and
     continue with it.
   If it could be two of these, ask one short question instead of guessing.
2. **No sentence**, follow `step`:
   - `ask` → show the block saved under `## 等你决定` in the progress file,
     unchanged, and stop. Redraft it only if the facts behind it changed,
     and say what changed;
   - `continue` → `../next/SKILL.md` for the current idea;
   - `review` → a shipped idea is due: quote its `## 怎样算做对了`, ask
     whether that happened, and offer 继续做 / 就此打住 / 砍掉 with a
     recommendation, in the asking layout. Record the answer in 决定 and set
     `reviewed`; 继续做 reopens it with a new slice;
   - `overview` → `../ideas/SKILL.md`, then offer to start one with
     `/yishuship <一句话>`.

When `other_active` is not empty, the first line names the idea you picked
(the most recently updated) and that the user can say "换成 <想法>" to switch.

Write to the user in their language: the language of their message, or, when
they typed only the command, the language of the progress file.

Read the chosen step's SKILL.md in full before acting on it; this file only
decides which one.
