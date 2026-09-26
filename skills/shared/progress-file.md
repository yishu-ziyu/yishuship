# The progress file

One file per idea at `<project>/.ship/ideas/<slug>.md`. It is how the work
survives a closed session, and how `/yishuship:ideas` and the status line know
where every idea stands. Chat is not memory; if it matters next time, it goes
here.

## Rules

- Read it before doing anything; update it before you stop.
- Reconcile it with reality on every read: git log, tags, tests, the running
  product. If the file and reality disagree, reality wins; fix the file and say
  what you corrected.
- Front matter is machine-read by the scripts. Keep the keys exactly as below.
- `waiting` is non-empty only while the user owes a decision; write the
  question in one short line, and keep the full question block exactly as
  shown to the user under `## 等你决定`. Clear both once answered.
- Record decisions with their reason, not just the choice.

## Template

```markdown
---
idea: <one line, the user's words>
project: <project name>
status: shaping | building | waiting | shipping | shipped | paused | dropped
waiting: <the open question for the user, or empty>
slice: <current slice in one line, or empty>
ship_bar: <what "users can use it" means here, or empty until asked>
updated: <YYYY-MM-DD>
---

## 为什么做
<who, what problem, why now; two or three lines>

## 用户能看到的行为
- [x] <decided behavior, in product words>
- [ ] <undecided behavior> → <the open choice>

## 决定
- <date> <decision> · 理由：<why>

## 切片
1. [done] <slice> · 证据：<path or commit>
2. [now] <slice>
3. [next] <slice>

## 等你决定
<the question block exactly as last shown to the user, or empty>

## 下一步
<exactly one next action, and what it needs from the user if anything>

## 遗留
- <finding outside scope, with where it was seen>
```

Register the project once so `/yishuship:ideas` can find it:

```
python3 <skill-dir>/../../scripts/ideas.py --register <project-root>
```
