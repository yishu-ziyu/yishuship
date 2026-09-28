# Saying something is done

"Done" is a claim the user will act on. It needs evidence the user can see.

## Required

- **Before and after** for anything a user can see: a screenshot, recording, or
  real output from the running product, taken this session. Compiling, tests
  passing, or reading the code is not evidence of a visible change. Capture
  "before" by running the product before the first edit and quote it as it
  was; never describe it afterwards from memory or from the code.
- **An independent check** before the word "done": hand a fresh subagent only
  the decided behaviors with their examples, how to run the product, and your
  before/after claims. It runs the product itself and reports only mismatches
  that break a behavior or a claim, not style. Fix, check again, and say in
  the report what it found. If no subagent can run, say the check was yours.
- **Each decided behavior gets its own line** with the evidence that proves it,
  and that evidence note in the progress file says `证明：行为N`. The line says
  what the user sees, with the real example (`上传后只剩顶部「开始精读」是亮蓝`),
  never how you measured it: color values, selectors, file:line and logs go in
  a `细节：` line under it, which the page folds away.
- **Earlier behaviors still hold**: each earlier slice's `复查` was run again
  after this change, with its result. Each new evidence note ends with
  `复查：<one command, or a few steps on the running product>` that proves its
  behaviors again, so the next slice can run it.
- **What was not verified**, stated plainly with the reason, in its own block.
  A missing layer is a gap, not an implied pass.
- **Commands actually run** this session back every "passes" claim. If evidence
  is reused from earlier, say where it came from.
- **Findings outside the slice** are listed, not fixed.
- **Which index entries this slice used** (`参考了：…`) and **what the index
  lacked** (`索引缺了：…`), naming the level a new row belongs to: a kind of
  work goes in `~/.yishuship/INDEX.md`, a fact about this project only in
  `<project>/.ship/INDEX.md`. Add a row only when the user says so.

## Showing images

The user cannot see files you only name. Embed the before and after in the
slice's `## 证据` note (`![改之前 · …](…)`); the page beside the terminal shows
them (`asking.md`). Keep the images in `.ship/evidence/<date>-<slug>/`. Only
when `page.py` says `no page`, open them with
`bash <skill-dir>/../../scripts/show-evidence.sh "<title>" "<before.png>|改之前 · …" "<after.png>|改之后 · …"`.

## Where it goes

When `page.py` says the page is open, write the report below into the slice's
`## 证据` note (the page shows its pictures, behaviors and what was not
verified) and the terminal gets one line: `<slice> 做完了，看旁边的页面。满意回
「满意」，不行回「不行」。` Only when it says `no page`, print the report.

## Layout

```
[yishuship] 完成 · <project>
<slice in one line>


改之前  <what the user saw>
          │
          ▼
改之后  <what the user sees now>


行为 1 ✓ <behavior>
        <evidence>

行为 2 ✓ ...


之前的行为
  行为 N ✓ 还在 · <复查 run, its result>


没验证到的
  <item> · <why>

参考了：<index entries used, or 无>
索引缺了：<gap and its level, or 无>


满意吗？
  满意  → 提交这一块，接着做 <next slice>
  不行  → 我停在这里，我们重新聊
```

End there: one question, no separate commit question. A one-way door the next
slice needs goes in the choices layout of `asking.md` instead.
