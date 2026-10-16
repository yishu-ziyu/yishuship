# Keeping the product beside the user

The user judges by using the product, not by reading about it. In a project
with an idea in progress, the product should already be running where they
look when they speak, and should show each change without them doing anything.

`.ship/产品.md` holds how, for this project only. The hooks module reads it:
when the user sends a message it runs `在跑吗`, and `启动` if that fails; at the
end of a turn that changed files of the product (hidden folders and build
output aside) it runs `改完刷新`. Both run in the background from the project
root and write to `.ship/live/产品.log`. Nothing runs until `你确认过` has a
date.

```
# 这个产品怎么跑在你旁边

- 启动：`<command>`
- 在跑吗：`<command, exit 0 while it runs>`
- 改完刷新：`<command>`
- 发布：<not settled yet, or the command>
- 你确认过：<date the user confirmed these; empty until then>
```

## Writing it

- Find the commands in the project first: its README, scripts, package
  manifests, and how earlier sessions ran it. Run each once yourself and see
  the product appear before writing it down.
- `启动` opens the product where the user looks: a web page in the browser
  pane beside the terminal, a Mac app's window, a browser extension in the
  browser it belongs to. Do not bring a window forward while the user is typing
  elsewhere (`docs/real-app.md`).
- `在跑吗` must be cheap and exact: a process name or a port, not a build.
- `改完刷新` must show the newest code: rebuild and reopen when nothing reloads
  by itself; a dev server that reloads on save needs only `true`. Stopping the
  product is fine here: the user confirms this line.
- Show the user the three commands in plain words (what each does, how long
  it takes) and ask once. Write the date only after they say yes.
- `发布` stays "还没定" until shipping comes up; settle it then, with the user.
