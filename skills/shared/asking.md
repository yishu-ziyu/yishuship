# Stopping to ask the user

The user is a product person. They decide what users see and do, which one-way
doors to walk through, and anything outward-facing or destructive. Everything
inside the box (architecture, tests, code quality) is yours; do not ask about it.

## Stop and ask only for

- Behavior the user will see that has more than one reasonable answer.
- One-way doors: data migrations, writes to their data, storage or format choices
  that are costly to undo. Translate each into its product consequence.
- Scope: what this slice includes, what waits.
- Commits, pushes, publishing, deleting, spending their quota or money. Approval
  of a plan is not approval of these.
- The ship bar, the first time a project ships (what counts as "users can use it").

Everything else: decide, say what you decided in one line, continue.

## Layout

The user must be able to judge in seconds. Dense lines hide the structure, so
use space and direction:

```
[yishuship] 需要你决定


①  <the question, one line>
   │
   ├─ A  <option>                       ◀ 推荐
   │     <what the user will see / what it costs>
   │
   └─ B  <option>
         <what the user will see / what it costs>


回复示例：1A 2A
```

- A settled path is drawn vertically with `│` and `▼`; open questions branch
  with `├─` / `└─`. One question per block, blank lines between blocks.
- Every option states its consequence in product terms. Mark one recommendation.
- Lines stay under about 36 Chinese characters; long lines get cut off.
- Batch every open question into one stop. End with a reply example.

## Words

- Say what a thing does. Never invent a name for a mechanism (no "卡片",
  "账本", "闸门"); the user should not have to translate before judging.
- No engineering jargon in the question; paths and commands go after it, and
  only if they change the decision.
