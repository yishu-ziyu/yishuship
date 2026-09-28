"""Serve the chain page for a project; the confirm buttons write back into that idea's 设计.md.

  chain_serve.py DIR [PORT]
"""
import datetime, http.server, json, re, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chain as render

ROOT = Path(sys.argv[1]).resolve()
SHIP = ROOT / ".ship"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765


def confirm(sid, ok, note):
    """sid like 003-§1: mark that section confirmed today, or record the requested change."""
    num, sec = sid.split("-", 1)
    folder = next(p for p in SHIP.iterdir() if p.name.startswith(num + "-"))
    f = folder / "设计.md"
    text = f.read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(sec)} .*?(?=^## |\Z)", text, re.M | re.S)
    if not m:
        raise ValueError(f"设计里没有 {sec}")
    part, today = m.group(0), datetime.date.today().isoformat()
    if ok:
        new = re.sub(r"^你确认了：.*$", f"你确认了：{today}", part, flags=re.M)
    else:
        new = re.sub(r"^(你确认了：.*)$", rf"要改（{today}）：{note.strip()}" + "\n\n" + r"\1", part, count=1, flags=re.M)
    f.write_text(text[:m.start()] + new + text[m.end():], encoding="utf-8")


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/f/"):
            target = (SHIP / urllib.parse.unquote(path[3:])).resolve()
            if not target.is_relative_to(SHIP.resolve()) or not target.is_file():
                self.send_error(404); return
            body, kind = target.read_bytes(), "image/png" if target.suffix == ".png" else "application/octet-stream"
        else:
            body, kind = render.build(ROOT, served=True).encode(), "text/html; charset=utf-8"
        self.send_response(200); self.send_header("Content-Type", kind); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        try:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            confirm(data["id"], bool(data["ok"]), data.get("note", ""))
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        except Exception as e:
            self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())

    def log_message(self, *_):
        pass


print(f"http://127.0.0.1:{PORT}/")
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
