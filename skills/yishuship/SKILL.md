---
name: yishuship
description: "The one entry point: decides from the progress files whether to shape a new idea, record and fix a bug, ask the pending question, continue the current idea, or show every idea. Use when the user types /yishuship, with or without a sentence after it."
disable-model-invocation: true
---

# yishuship

The user types one command. You decide the step; they should never need to
remember which.

## Outcome Contract

- Outcome: the right step runs, and the first line of your reply says which
  idea you picked up and what step it is at.
- Language: every sentence you write to the user, that first line and any
  closing aside included, is in the user's language: their message's; a bare
  command carries none, so the progress file's.
- Done when: that step's own outcome is met (see the step's SKILL.md).
- Evidence: `python3 <skill-dir>/../../scripts/ideas.py --route "$PWD"`, which
  decides from disk; never from memory of earlier sessions.

## Route

Run the route script first. If it names a `current` idea, also run
`python3 <skill-dir>/../../scripts/page.py "$PWD"`: it opens the page beside
the terminal that follows the progress file (once; it says if already open).
What it prints decides every stop of this run: after `opened` or `already
open`, the user looks at the page, so pictures and the full block go into the
progress file (`../shared/asking.md`) and the terminal gets one line in the
user's language: what you need, how to reply, 看旁边的页面. After `no page`,
print the full block. Then:

A reply may also come from the page: an unticked line under `## 你的反馈`
(`../shared/asking.md`) counts as the sentence typed after the command.

1. **The user typed a sentence after the command.** Judge what it is:
   - an answer to the `waiting` question of the current idea (for example
     "1A 2B") → record the decisions in its progress file, clear `waiting`,
     and continue with `../next/SKILL.md`;
   - an answer to 满意吗: 满意 / 继续 → record it in 决定, mark that slice's
     design 你确认了, do what that line promised (its commit is approved),
     clear `waiting`, continue with
     `../next/SKILL.md`; 不行 / 重新聊 → record it, stop building, and talk it
     through: what they expected, what differs, then reshape the slice with
     them. Any other words about what they saw are feedback: apply, show again;
   - an instruction about the current idea → continue with
     `../next/SKILL.md`, applying it;
   - a new idea → `../idea/SKILL.md`;
   - a bug or an observed problem (an error, a screenshot of something wrong,
     "it used to work", an item from 遗留) → a bug file, then `../next/SKILL.md`
     on it. Write `.ship/ideas/<slug>.md` from the template with `kind: bug`:
     现象 in the user's words with their screenshot, 应该怎样, and one slice
     `第一块 修好：<现象>`. A bug inside the current idea's slice stays in that
     idea's file instead. No go / drop question: a bug is fixed unless the fix
     changes what users see in more than one reasonable way;
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
   - `start` → no idea in progress in this project: say so, read its live
     state (branch, uncommitted work, `.ship/PROJECT.md` if any, paused ideas
     here), and offer to start
     one here with `/yishuship <一句话>`. Never recommend other projects' ideas;
   - `overview` → typed outside any project: `../ideas/SKILL.md`.

When `other_active` is not empty, the first line names the idea you picked
(the most recently updated) and that the user can say "换成 <想法>" to switch.

Read the chosen step's SKILL.md in full before acting on it.
