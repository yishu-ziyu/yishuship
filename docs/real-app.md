# Verifying in the running product

Visible behavior is verified by running the product and looking at it. This is
the user's real machine, often in use while you work.

## Before and after builds

- Build the "before" from the last commit in a separate worktree
  (`git worktree add --detach /tmp/<name>-base HEAD`, own derived-data path),
  so the user's checkout is never switched or stashed. Remove it afterwards.
- Take the "after" from the current build, same data, same steps.

## Driving a macOS app

- Launch your own instance in the background (`open -g -n -a <App.app> <file>`)
  and record its pid. Only ever stop pids you started and recorded.
- Act through `cua-driver call <tool> '<json>'` scoped to that pid and window.
  Prefer element tokens from `get_window_state`; use pixel clicks only on a
  window that is on screen.
- Never send keystrokes to "whatever is frontmost" (osascript `keystroke`,
  global key events without a pid). With Stage Manager the front app can
  change under you and input lands somewhere unknown.
- Before any step that brings a window forward, check the user is not using
  the machine: `bash <yishuship>/scripts/user-idle.sh` prints idle
  seconds; below 20, do not take the foreground. If the frontmost app changes
  mid-run, stop at once, say so, and hand the check to the user.
- After foreground work, give the user's app back the foreground.
- If the app has several windows, keyboard ops are refused; close the extra
  windows or use element actions.
- SwiftUI text fields ignore an accessibility `set_value` until they have real
  focus: set the value, pixel-click the field, then one `hotkey` keystroke
  (space, delete) so the binding updates.
- Screenshot one window: `screencapture -x -o -l <window_id> <file>`.
  Enlarge the window first (`set_window_frame`) so text is readable.

## When a tool blocks you

- `xcodebuild test` failing with "Failed to prevent system sleep" means the
  machine refuses power assertions (even `caffeinate` fails). Run pure-logic
  tests through a throwaway Swift package that symlinks the same source and
  test files; report the full suite as not run.
- Any tool failure: find out why before switching tools, and say which layer
  was verified and which was not.

## Services you start

Record every server or helper you start (pid, port). Stop them when the
verification is over, unless the user wants to try the product; then say what
is still running and how to stop it.
