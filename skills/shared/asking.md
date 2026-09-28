# Stopping to ask the user

The user is a product person. They decide what users see and do, which one-way
doors to walk through, and anything outward-facing or destructive. Everything
inside the box (architecture, tests, code quality) is yours; do not ask about it.

## The user looks at the page, types in the terminal

The user judges by seeing. At every stop (满意吗, a choice, a shaping
question), first write what they need to see into the progress file, best
first: the running product (screenshot or recording), else a mock on their
real content, else a diagram; words alone only when none applies. Write the
full block under `## 等你决定`, then run
`python3 <skill-dir>/../../scripts/page.py "$PWD"`. If it says the page is
open, the terminal message is one line: what you need, how to reply, and
看旁边的页面. If it says `no page`, show the full block in the terminal.

## While building: show, then ask 满意吗

Shaping a new idea is unchanged: `../idea/SKILL.md` and the layout for
choices below. Once a slice is being built, where what the user will see has
more than one reasonable answer, build the recommended one and show it; do not
ask A/B beforehand.
Stop this way at the end of a slice, and as soon as the work is harder than
planned (see `../next/SKILL.md`). The pictures: before and after under the
slice's `## 证据` note, or what it looks like now under `### 现在` in
`## 看得见` when stopped early. The block:

```
[yishuship] 给你看一下 · <slice>

现在  <what the user sees now, from the running product>

原本想  <what was agreed>              (only when stopped early)
难在哪  <what turned out harder, in product words>

满意吗？
  满意  → <what you do next: 提交这一块，接着做 <next>>
  不行  → 我停在这里，我们重新聊
```

满意 is the user's approval of the commit named in that line. Anything else
they write is feedback on what they saw: apply it, show again.

## While building, ask beforehand only for

- One-way doors: data migrations, writes to their data, storage or format choices
  that are costly to undo. Translate each into its product consequence.
- Scope: what this slice includes, what waits.
- Pushes, publishing, deleting, spending their quota or money; commits, unless
  named in the 满意 line. Approval of a plan is not approval of these.
- The ship bar, the first time a project ships (what counts as "users can use it").

Everything else: decide, say what you decided in one line, continue.

## Layout for choices

For one-way doors and shaping a new idea. The user must be able to judge in
seconds. Dense lines hide the structure, so use space and direction:

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
- Every option states its consequence in product terms and is shown: what the
  product looks like or does under it, side by side on the page (the current
  screenshot for "no change", a labeled mock on real content for the rest).
  Mark one recommendation; the user decides, you never proceed on it alone.
  Write the pictures under `## 看得见` in the progress file, exactly this shape:
  ```
  ## 看得见
  ### ① <question>
  - A ◀ 推荐 · <option> · <what the user sees> · 示意 · ../evidence/<dir>/q1-a.html
  - B · <option> · <what the user sees> · 真实截图 · ../evidence/<dir>/now.png
  ### 词
  - <named thing> · <what it is> · ../evidence/<dir>/now.png#box=x0,y0,x1,y1
  ```
  Then run `python3 <skill-dir>/../../scripts/ideas.py --visuals .` and fix
  every problem it lists. Then look: `python3 <skill-dir>/../../scripts/snap.py .`
  screenshots every picture; open each PNG. No overlapping or cut-off text,
  every box on its thing, the difference between options visible at a glance.
  Crop each picture to where the options differ: the page shows an option
  about 300 px wide, where a whole window is unreadable.
  Fix and snap again until all pass; only then show the question.
- Lines stay under about 36 Chinese characters; long lines get cut off.
- Batch every open question into one stop. End with a reply example.

## Keeping the goal in view

- Open each new version with one line: what the work is for and what is still
  unproven; do not polish looks or wording while the core is unproven. If the
  user seems lost, restate that goal and offer one next step.
- For looks or wording the user said 不行 to, show several truly different
  options at once.
- Show a proposal before asking about it: a temporary page or a literal
  example of what changes, the current way beside the proposed way.
- Anything a question names that the user can see (a panel, a mark, an area)
  gets its picture: a real screenshot with it boxed, on hover in the page.

## Words

- These instructions are in English; what you write to the user is in their
  language (see `../yishuship/SKILL.md`), including headings and short asides.
- Say what a thing does. Never invent a name for a mechanism (no "卡片",
  "账本", "闸门"); the user should not have to translate before judging.
- Each claim carries its source and conditions (实测 how / 你试过 / 你定的 /
  推断). Never invent a status, a step, or a duration.
- No engineering jargon in the question; paths and commands go after it, and
  only if they change the decision.
