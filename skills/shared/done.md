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
  and that evidence note in the progress file says `证明：行为N`.
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

The user cannot see files you only name. Put screenshots in front of them:

```
bash <skill-dir>/../../scripts/show-evidence.sh "<title>" \
  "<before.png>|改之前 · <what is wrong>" \
  "<after.png>|改之后 · <what changed>"
```

It opens a temporary page beside the terminal; once the user has looked, close
it with the command it prints. Keep the images in `.ship/evidence/<date>-<slug>/`.

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


没验证到的
  <item> · <why>

参考了：<index entries used, or 无>
索引缺了：<gap and its level, or 无>
```

Then the next decision, if any, in the asking layout.
