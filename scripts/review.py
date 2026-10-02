"""Serve a folder of pages the agent made, so the user can comment on any part of a page without leaving it.

  review.py DIR [PORT]

Every HTML page it serves gets a small script: each section of the page shows a 「说一句」 button; what the
user writes (or dictates) there goes to DIR/.review/inbox.jsonl with the part it points at. The hooks module
watches that file and hands each comment to the agent; the agent's answer goes to DIR/.review/replies.jsonl
and shows on the page next to the same part.
"""
import datetime, http.server, json, sys, urllib.parse, uuid
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8770
BOX = ROOT / ".review"
BOX.mkdir(exist_ok=True)
INBOX, REPLIES = BOX / "inbox.jsonl", BOX / "replies.jsonl"

SCRIPT = r"""
(() => {
  const page = location.pathname.replace(/^\//, '')
  // The parts a user can point at: what the page marks, else its sections and cards.
  const parts = [...document.querySelectorAll('[data-review], section, .card')]
    .filter((el, i, all) => !all.some((o) => o !== el && o.contains(el) && !o.matches('main, body')))
  const css = document.createElement('style')
  css.textContent = `
    .rv-host{position:relative}
    .rv-btn{position:absolute;top:8px;right:8px;z-index:20;font:600 12px/1 -apple-system,"PingFang SC",sans-serif;
      background:#1d1b18;color:#fff;border:0;border-radius:999px;padding:6px 10px;cursor:pointer;opacity:0;transition:opacity .15s}
    .rv-host:hover>.rv-btn,.rv-btn.rv-on{opacity:1}
    .rv-pop{position:absolute;top:40px;right:8px;z-index:30;width:min(360px,90%);background:#fff;border:1px solid #d9d3c7;
      border-radius:12px;box-shadow:0 10px 30px #0002;padding:10px;font:14px/1.5 -apple-system,"PingFang SC",sans-serif;color:#1d1b18}
    .rv-pop textarea{width:100%;min-height:72px;border:1px solid #e2ddd3;border-radius:8px;padding:8px;font:inherit;resize:vertical}
    .rv-pop .rv-row{display:flex;justify-content:space-between;align-items:center;margin-top:6px;font-size:12px;color:#7a746a}
    .rv-pop button{background:#1d1b18;color:#fff;border:0;border-radius:8px;padding:6px 12px;font:inherit;cursor:pointer}
    .rv-thread{margin-top:10px;display:flex;flex-direction:column;gap:6px}
    .rv-msg{border-radius:10px;padding:8px 10px;font:14px/1.55 -apple-system,"PingFang SC",sans-serif;max-width:640px}
    .rv-you{background:#f1ecfb;color:#3b2a5a;align-self:flex-start}
    .rv-ai{background:#e7f6ec;color:#1d4d31;align-self:flex-start}
    .rv-wait{background:#f4f1ea;color:#7a746a;align-self:flex-start}
    .rv-msg b{font-weight:600;margin-right:6px}`
  document.head.appendChild(css)

  const label = (el) => (el.querySelector('h1,h2,h3,b,strong')?.textContent || el.textContent || '').trim().slice(0, 40)
  const threads = new Map()
  parts.forEach((el, i) => {
    const id = el.dataset.review || `part-${i + 1}`
    el.classList.add('rv-host')
    const btn = document.createElement('button')
    btn.className = 'rv-btn'
    btn.textContent = '说一句'
    const thread = document.createElement('div')
    thread.className = 'rv-thread'
    el.appendChild(btn)
    el.appendChild(thread)
    threads.set(id, thread)
    btn.onclick = (ev) => {
      ev.stopPropagation()
      document.querySelectorAll('.rv-pop').forEach((p) => p.remove())
      const pop = document.createElement('div')
      pop.className = 'rv-pop'
      pop.innerHTML = '<textarea placeholder="对这一块的意见。可以打字，也可以按两下 fn 说话"></textarea>' +
        '<div class="rv-row"><span>⌘ + 回车 发送</span><button>发给 AI</button></div>'
      el.appendChild(pop)
      const box = pop.querySelector('textarea')
      box.focus()
      const send = async () => {
        const text = box.value.trim()
        if (!text) return
        const r = await fetch('/__comment', { method: 'POST', headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ page, part: id, label: label(el), text }) })
        if (!r.ok) { pop.querySelector('.rv-row span').textContent = '没发出去：' + r.status; return }
        pop.remove()
        refresh()
      }
      pop.querySelector('button').onclick = send
      box.onkeydown = (k) => { if (k.key === 'Enter' && (k.metaKey || k.ctrlKey)) send(); if (k.key === 'Escape') pop.remove() }
    }
  })

  // Comments and answers for this page, shown under the part they belong to.
  let shown = ''
  async function refresh() {
    const r = await fetch('/__thread?page=' + encodeURIComponent(page))
    if (!r.ok) return
    const items = await r.json()
    const key = JSON.stringify(items)
    if (key === shown) return
    shown = key
    threads.forEach((t) => (t.innerHTML = ''))
    for (const c of items) {
      const t = threads.get(c.part)
      if (!t) continue
      const you = document.createElement('div')
      you.className = 'rv-msg rv-you'
      you.innerHTML = '<b>你</b>'
      you.append(c.text)
      t.appendChild(you)
      const replies = c.replies.length ? c.replies : [{ text: 'AI 收到了，正在看……', wait: true }]
      for (const a of replies) {
        const m = document.createElement('div')
        m.className = 'rv-msg ' + (a.wait ? 'rv-wait' : 'rv-ai')
        m.innerHTML = a.wait ? '' : '<b>AI</b>'
        m.append(a.text)
        t.appendChild(m)
      }
    }
  }
  refresh()
  setInterval(refresh, 1500)

  // Any picture on the page opens full size on click; a click or Esc closes it.
  const zoomCss = document.createElement('style')
  zoomCss.textContent = `
    main img,section img{cursor:zoom-in}
    .rv-zoom{position:fixed;inset:0;z-index:100;background:#000d;display:flex;align-items:center;justify-content:center;cursor:zoom-out;padding:24px}
    .rv-zoom img{max-width:100%;max-height:100%;object-fit:contain;border-radius:12px;box-shadow:0 20px 60px #0008}`
  document.head.appendChild(zoomCss)
  document.addEventListener('click', (ev) => {
    const img = ev.target.closest && ev.target.closest('img')
    // Pages mark their own interactive areas (prototypes) with data-no-zoom.
    if (!img || img.closest('.rv-zoom') || img.closest('[data-no-zoom]')) return
    ev.preventDefault()
    const box = document.createElement('div')
    box.className = 'rv-zoom'
    const big = document.createElement('img')
    big.src = img.currentSrc || img.src
    box.appendChild(big)
    box.onclick = () => box.remove()
    document.body.appendChild(box)
  })
  document.addEventListener('keydown', (k) => { if (k.key === 'Escape') document.querySelectorAll('.rv-zoom').forEach((z) => z.remove()) })
})()
"""


def lines(f):
    if not f.exists():
        return []
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]


class H(http.server.BaseHTTPRequestHandler):
    def send(self, code, body, kind):
        self.send_response(code)
        self.send_header("content-type", kind)
        self.send_header("cache-control", "no-store")
        self.send_header("accept-ranges", "bytes")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/__review.js":
            return self.send(200, SCRIPT.encode(), "text/javascript; charset=utf-8")
        if url.path == "/__thread":
            page = urllib.parse.parse_qs(url.query).get("page", [""])[0]
            replies = lines(REPLIES)
            items = [{**c, "replies": [r for r in replies if r["id"] == c["id"]]} for c in lines(INBOX) if c["page"] == page]
            return self.send(200, json.dumps(items, ensure_ascii=False).encode(), "application/json")
        target = (ROOT / urllib.parse.unquote(url.path.lstrip("/"))).resolve()
        if not target.is_relative_to(ROOT) or not target.is_file():
            return self.send_error(404)
        body = target.read_bytes()
        if target.suffix == ".html":
            body = body.replace(b"</body>", b'<script src="/__review.js"></script></body>') if b"</body>" in body \
                else body + b'<script src="/__review.js"></script>'
            return self.send(200, body, "text/html; charset=utf-8")
        kinds = {".png": "image/png", ".jpg": "image/jpeg", ".js": "text/javascript", ".css": "text/css", ".mp4": "video/mp4", ".webm": "video/webm"}
        kind = kinds.get(target.suffix, "application/octet-stream")
        # WebKit (the browser pane beside the terminal) plays video only when byte ranges are served.
        rng = self.headers.get("Range", "")
        if rng.startswith("bytes="):
            start_s, _, end_s = rng[6:].partition("-")
            start = int(start_s) if start_s else max(0, len(body) - int(end_s))
            end = min(int(end_s), len(body) - 1) if end_s and start_s else len(body) - 1
            part = body[start:end + 1]
            self.send_response(206)
            self.send_header("content-type", kind)
            self.send_header("accept-ranges", "bytes")
            self.send_header("content-range", f"bytes {start}-{end}/{len(body)}")
            self.send_header("content-length", str(len(part)))
            self.end_headers()
            self.wfile.write(part)
            return
        return self.send(200, body, kind)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/__comment":
            return self.send_error(404)
        c = json.loads(self.rfile.read(int(self.headers["content-length"])))
        if not all(isinstance(c.get(k), str) and c[k] for k in ("page", "part", "text")):
            return self.send_error(400)
        item = {"id": uuid.uuid4().hex[:8], "at": datetime.datetime.now().isoformat(timespec="seconds"),
                "page": c["page"], "part": c["part"], "label": c.get("label", ""), "text": c["text"]}
        with INBOX.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        self.send(200, b"{}", "application/json")

    def log_message(self, *args):
        pass


print(f"http://127.0.0.1:{PORT}/", flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
