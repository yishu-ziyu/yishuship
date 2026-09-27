#!/usr/bin/env python3
"""A page beside the terminal: does the user need to act, what the agent is doing and for what, what comes next.

  page.py DIR           open the page for the project containing DIR; reuses the
                        one already open, reopens it if the user closed it
  page.py --html DIR    print the page once (for checking)
  page.py --serve ROOT  run the local server (started by the first form)

YISHUSHIP_NO_PAGE=1 turns opening off (the eval runner sets it).

The server renders from the progress file on every request, so the page follows
whatever the agent writes. The page asks again every 2 seconds; once nobody has
asked for IDLE_EXIT seconds the server exits on its own.
"""
from __future__ import annotations

import hashlib
import html
import http.server
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ideas import current, doing, project_root, quiet_for, slice_things  # noqa: E402

POLL_MS = 2000
IDLE_EXIT = 600      # seconds without a request before the server stops
CLOSED_AFTER = 8     # seconds without a request before the page counts as closed


# ---------- reading the progress file ----------

def waiting_block(idea: dict) -> str:
    """The question saved under ## 等你决定, when the user owes a decision."""
    if not idea.get("waiting"):
        return ""
    text = Path(idea["file"]).read_text(encoding="utf-8")
    section = re.search(r"^## 等你决定\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    fence = re.search(r"```[^\n]*\n(.*?)```", section.group(1) if section else "", flags=re.S)
    block = fence.group(1).rstrip() if fence else idea["waiting"]
    return re.sub(r"\A\[yishuship\] *需要你决定\s*\n", "", block).strip("\n")  # the page already says it


# ---------- drawing it ----------
# Three questions, most urgent first: do I need to do anything; what is it doing
# and for what; what happens next. Normal is quiet; only exceptions stand out.

def esc(text: str) -> str:
    return html.escape(text or "")


def body(idea: dict | None) -> str:
    if idea is None:
        return '<p class="state">这个项目现在没有进行中的想法</p>'
    top = f'<p class="which">{esc(idea.get("idea"))} · {esc(idea.get("project"))}</p>'
    slice_name = idea.get("slice", "")
    question = waiting_block(idea)
    if question:
        where = f'<p class="quiet">停在：{esc(slice_name)}</p>' if slice_name else ""
        return (f'{top}<p class="state alert">需要你决定</p>{where}<pre>{esc(question)}</pre>'
                '<p class="quiet">在终端里回复</p>')
    step, thing, place, _ = doing(idea)
    working, age = bool(idea.get("now")), quiet_for(idea) if idea.get("now") else ""
    if age:
        head = (f'<p class="state alert">⚠ {esc(age.removesuffix("前"))}没有动静</p>'
                '<p class="quiet">可能卡住了，或者会话已经关了。在终端里打 /yishuship 看看</p>')
    elif working:
        head = f'<p class="state">不用管它<span class="quiet"> · {esc(minutes_ago(idea))}更新</span></p>'
    else:
        head = ('<p class="state">现在没有 Agent 在做</p>'
                '<p class="quiet">要它接着做，在终端里打 /yishuship</p>')
    now = ""
    if working:
        what = f"{esc(step)}：{esc(thing)}" if thing else esc(step)
        if age:  # it may have stopped: say where it was, not that it is still going
            what = "上次" + ("" if step.startswith("在") else "在") + what
        now = f'<p class="now">{what}</p>'
    things = slice_things(idea)
    rows = "".join(
        f'<li class="{"done" if done else ("here" if n == place else "")}">'
        f'<span class="mark">{"✓" if done else ("◐" if n == place else "○")}</span>{esc(text)}</li>'
        for n, (done, text) in enumerate(things, 1))
    listing = (f'<p class="label list">{esc(slice_name)} · {len(things)} 件事</p><ul>{rows}</ul>' if things else "")
    after = ("" if age or not idea.get("next")
             else f'<p class="next"><span class="label">接下来</span>{esc(idea.get("next"))}</p>')
    return f"{top}{head}{now}{listing}{after}"


def minutes_ago(idea: dict) -> str:
    minutes = int((time.time() - Path(idea["file"]).stat().st_mtime) // 60)
    return "刚刚" if minutes < 1 else f"{minutes} 分钟前"


def page(root: Path) -> str:
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>走到哪了</title><style>
body{{margin:0;background:#111;color:#ccc;font:15px/1.6 -apple-system,"PingFang SC",sans-serif}}
main{{max-width:560px;margin:0 auto;padding:24px 28px 40px}} p{{margin:0}}
.which{{color:#666;font-size:12px;margin-bottom:18px}}
.state{{color:#eee;font-size:16px;font-weight:600}} .state .quiet{{font-weight:400}}
.alert{{color:#e5c07b}} .quiet{{color:#777;font-size:13px}} .state+.quiet{{margin-top:2px}}
.now{{font-size:22px;line-height:1.4;color:#fff;margin:32px 0 36px}}
.label{{color:#777;font-size:13px;margin-right:12px}} .quiet+.list,.state+.list{{margin-top:32px}}
ul{{list-style:none;margin:10px 0 32px;padding:0}} li{{margin:6px 0;color:#777}}
li.here{{color:#fff}} .mark{{display:inline-block;width:1.6em}} li.done .mark{{color:#6a9}}
.next{{color:#bbb}} pre{{font:14px/1.5 Menlo,monospace;white-space:pre;overflow-x:auto;margin:24px 0 16px;color:#eee}}
</style></head><body><main id="m">{body(current(str(root)))}</main><script>
setInterval(async()=>{{try{{const r=await fetch('/body');const t=await r.text();
const m=document.getElementById('m');if(m.innerHTML!==t)m.innerHTML=t}}catch(e){{}}}},{POLL_MS});
</script></body></html>"""


# ---------- serving and opening ----------

def state_file(root: Path) -> Path:
    key = hashlib.sha1(str(root).encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"yishuship-page-{key}.json"


def serve(root: Path) -> None:
    last = [time.time()]   # any request; keeps the server alive
    polled = [0.0]         # the last time an open page asked for an update

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            last[0] = time.time()
            if self.path == "/body":
                polled[0] = time.time()
            if self.path == "/ping":
                out = json.dumps({"root": str(root), "page_idle": time.time() - polled[0]}).encode()
            else:
                out = (body(current(str(root))) if self.path == "/body" else page(root)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *_):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state = state_file(root)
    state.write_text(json.dumps({"port": server.server_address[1], "pid": os.getpid()}))

    def watch():
        while time.time() - last[0] < IDLE_EXIT:
            time.sleep(5)
        server.shutdown()
    threading.Thread(target=watch, daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # so the finally below still runs
    try:
        server.serve_forever()
    finally:
        state.unlink(missing_ok=True)


def running(root: Path) -> tuple[int, float] | None:
    """Port of a live server for ROOT and seconds since a page last asked it, if any."""
    try:
        port = json.loads(state_file(root).read_text())["port"]
        reply = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/ping", timeout=1).read())
        return port, reply["page_idle"]
    except (OSError, ValueError, KeyError):
        return None


def open_page(directory: str) -> int:
    root = project_root(directory)
    if root is None or current(str(root)) is None or os.environ.get("YISHUSHIP_NO_PAGE"):
        return 0
    live = running(root)
    if live is None:
        subprocess.Popen([sys.executable, __file__, "--serve", str(root)], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            time.sleep(0.1)
            if (live := running(root)) is not None:
                break
        else:
            print("the page server did not start", file=sys.stderr)
            return 1
    port, page_idle = live
    url = f"http://127.0.0.1:{port}/"
    if page_idle < CLOSED_AFTER:  # an open page asks every POLL_MS
        print(f"already open: {url}")
        return 0
    if os.environ.get("CMUX_WORKSPACE_ID") and subprocess.run(["which", "cmux"], capture_output=True).returncode == 0:
        opened = subprocess.run(["cmux", "browser", "open-split", url], capture_output=True, text=True).stdout
        surface = re.search(r"surface=(\S+)", opened)
        print(f"opened beside the terminal: {url}")
        if surface:
            print(f"close with: cmux close-surface --surface {surface.group(1)}")
    else:
        subprocess.run(["open", url])
        print(f"opened in the browser: {url}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--serve"] and len(argv) == 2:
        serve(Path(argv[1]))
    elif argv[:1] == ["--html"] and len(argv) == 2:
        root = project_root(argv[1])
        print(page(root) if root else "no project here")
    elif len(argv) == 1 and not argv[0].startswith("-"):
        return open_page(argv[0])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
