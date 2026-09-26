# Saying something is done

"Done" is a claim the user will act on. It needs evidence the user can see.

## Required

- **Before and after** for anything a user can see: a screenshot, recording, or
  real output from the running product, taken this session. Compiling, tests
  passing, or reading the code is not evidence of a visible change.
- **Each decided behavior gets its own line** with the evidence that proves it.
- **What was not verified**, stated plainly with the reason, in its own block.
  A missing layer is a gap, not an implied pass.
- **Commands actually run** this session back every "passes" claim. If evidence
  is reused from earlier, say where it came from.
- **Findings outside the slice** are listed, not fixed.
- **Which index entries this slice used**, one line (`参考了：…` or `参考了：无`),
  so the user can see whether the right guidance was opened.

## Showing images

The user cannot see files you only name. Put screenshots in front of them:

```
bash <skill-dir>/../../scripts/show-evidence.sh "<title>" \
  "<before.png>|改之前 · <what is wrong>" \
  "<after.png>|改之后 · <what changed>"
```

It writes a temporary page and opens it beside the terminal (cmux split, or the
default browser). Once the user has looked, close it with the command the script
prints. Keep a copy of the images under `.ship/evidence/<date>-<slug>/`.

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
```

Then the next decision, if any, in the asking layout.
