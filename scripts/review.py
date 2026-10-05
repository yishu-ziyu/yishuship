"""Serve a folder of pages the agent made, so the user can comment on any part of a page without leaving it.

  review.py DIR [PORT]

Every HTML page it serves gets a small script: each section of the page shows a 「说一句」 button, and so
do words the user selects; from the comment box the user can also click one element on the page. What the
user writes (or dictates) goes to DIR/.review/inbox.jsonl with the part, and the quoted words or the
element (selector, tag, first words) it points at. The hooks module watches that file and hands each
comment to the agent; the agent's answer goes to DIR/.review/replies.jsonl and shows on the page next to
the same part. When a file in DIR changes, open pages reload at the same scroll position.
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
    .rv-btn,.rv-sel{font:600 12px/1 -apple-system,"PingFang SC",sans-serif;background:#1d1b18;color:#fff;border:0;
      border-radius:999px;padding:6px 10px;cursor:pointer}
    .rv-btn{position:absolute;top:8px;right:8px;z-index:20;opacity:0;transition:opacity .15s}
    .rv-host:hover>.rv-btn{opacity:1}
    .rv-sel{position:absolute;z-index:40;box-shadow:0 4px 14px #0003}
    .rv-pop{position:absolute;z-index:50;width:360px;max-width:calc(100vw - 16px);box-sizing:border-box;background:#fff;
      border:1px solid #d9d3c7;border-radius:12px;box-shadow:0 10px 30px #0002;padding:10px;
      font:14px/1.5 -apple-system,"PingFang SC",sans-serif;color:#1d1b18}
    .rv-pop textarea{width:100%;box-sizing:border-box;min-height:72px;border:1px solid #e2ddd3;border-radius:8px;padding:8px;font:inherit;resize:vertical}
    .rv-ref{font-size:12px;color:#5b4a86;background:#f1ecfb;border-radius:6px;padding:4px 8px;margin-bottom:6px;word-break:break-all}
    .rv-pop .rv-row{display:flex;gap:10px;align-items:center;margin-top:6px;font-size:12px;color:#7a746a}
    .rv-pop .rv-row span{margin-left:auto}
    .rv-pick{color:#5b4a86;text-decoration:underline;cursor:pointer}
    .rv-pop button{background:#1d1b18;color:#fff;border:0;border-radius:8px;padding:6px 12px;font:inherit;cursor:pointer}
    .rv-thread{margin-top:10px;display:flex;flex-direction:column;gap:6px}
    .rv-page{max-width:720px;margin:24px auto;padding:0 16px}
    .rv-msg{border-radius:10px;padding:8px 10px;font:14px/1.55 -apple-system,"PingFang SC",sans-serif;max-width:640px}
    .rv-you{background:#f1ecfb;color:#3b2a5a;align-self:flex-start}
    .rv-ai{background:#e7f6ec;color:#1d4d31;align-self:flex-start}
    .rv-wait{background:#f4f1ea;color:#7a746a;align-self:flex-start}
    .rv-msg b{font-weight:600;margin-right:6px}
    .rv-at{font:12px/1.4 -apple-system,"PingFang SC",sans-serif;color:#5b4a86;padding:0 10px;cursor:pointer;align-self:flex-start}
    .rv-lost{color:#a15c1f;cursor:default}
    .rv-mark{position:fixed;z-index:90;pointer-events:none;outline:2px solid #7c5cff;background:#7c5cff1a;border-radius:4px;display:none}
    .rv-tip{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:95;background:#1d1b18;color:#fff;
      padding:8px 14px;border-radius:999px;font:13px/1.4 -apple-system,"PingFang SC",sans-serif;box-shadow:0 6px 20px #0003}
    .rv-picking,.rv-picking *{cursor:crosshair !important}`
  document.head.appendChild(css)

  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim()
  const clip = (s, n) => (s.length > n ? s.slice(0, n) + '…' : s)
  const ui = (tag, cls) => { const e = document.createElement(tag); e.className = 'rv-ui ' + cls; return e }
  // What this script adds is never pointed at, quoted or searched.
  const isUi = (n) => !!(n && (n.nodeType === 1 ? n : n.parentElement)?.closest('.rv-ui'))
  const label = (el) => (el.querySelector('h1,h2,h3,b,strong')?.textContent || el.textContent || '').trim().slice(0, 40)

  const ids = new Map()
  const threads = new Map()
  const partOf = (node) => {
    const el = node.nodeType === 1 ? node : node.parentElement
    const p = parts.find((p) => p.contains(el))
    return p ? { id: ids.get(p), label: label(p) } : { id: 'page', label: '整页' }
  }

  // One outline box, for the element under the mouse while picking and for the spot a comment points at.
  const mark = ui('div', 'rv-mark')
  document.body.appendChild(mark)
  const showMark = (r) => Object.assign(mark.style, { display: 'block', left: r.left - 2 + 'px', top: r.top - 2 + 'px', width: r.width + 4 + 'px', height: r.height + 4 + 'px' })
  const hideMark = () => (mark.style.display = 'none')

  // How a spot is written down: the selected words, or one element by selector, tag and its first words.
  const snippetOf = (el) => /^(IMG|VIDEO)$/.test(el.tagName)
    ? (el.getAttribute('alt') || el.getAttribute('src') || '').slice(0, 60) : norm(el.textContent).slice(0, 60)
  function selectorOf(el) {
    const path = []
    for (let e = el; e && e !== document.body; e = e.parentElement) {
      if (e.id) { path.unshift('#' + CSS.escape(e.id)); break }
      const same = [...e.parentElement.children].filter((s) => s.tagName === e.tagName)
      const tag = e.tagName.toLowerCase()
      path.unshift(same.length > 1 ? `${tag}:nth-of-type(${same.indexOf(e) + 1})` : tag)
    }
    return (path[0]?.startsWith('#') ? '' : 'body > ') + path.join(' > ')
  }
  const elementAnchor = (el) => ({ selector: selectorOf(el), tag: el.tagName.toLowerCase(), snippet: snippetOf(el) })
  const kinds = { img: '图片', video: '视频', button: '按钮', a: '链接', h1: '标题', h2: '标题', h3: '标题', h4: '标题', p: '段落', li: '列表项', table: '表格' }
  const describe = (a) => a.quote ? `「${clip(a.quote, 60)}」`
    : `${kinds[a.tag] || a.tag}${a.snippet ? `「${clip(a.snippet, 40)}」` : ''}`

  // Finds words on the page again, ignoring how whitespace and line breaks fall.
  function findText(q) {
    q = norm(q)
    if (!q) return null
    const map = []
    let s = '', space = true
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT,
      { acceptNode: (n) => (n.parentElement.closest('.rv-ui, script, style') ? 2 : 1) })
    for (let n; (n = walk.nextNode());) {
      for (let i = 0; i < n.data.length; i++) {
        if (/\s/.test(n.data[i])) { if (space) continue; s += ' '; space = true } else { s += n.data[i]; space = false }
        map.push([n, i])
      }
    }
    const at = s.indexOf(q)
    if (at < 0) return null
    const r = document.createRange()
    r.setStart(map[at][0], map[at][1])
    r.setEnd(map[at + q.length - 1][0], map[at + q.length - 1][1] + 1)
    return r
  }
  // Where a comment points after the page changed: the same element first, then the only element of that
  // kind with the same first words, then the same words anywhere, else nowhere.
  function locate(c) {
    if (c.selector) {
      let el = null
      try { el = document.querySelector(c.selector) } catch { /* not a valid selector any more */ }
      if (el && !isUi(el) && el.tagName.toLowerCase() === c.tag && snippetOf(el) === (c.snippet || '')) return el
      const same = c.snippet ? [...document.getElementsByTagName(c.tag)].filter((e) => !isUi(e) && snippetOf(e) === c.snippet) : []
      if (same.length === 1) return same[0]
    }
    return findText(c.quote || c.snippet)
  }

  // Picking: the element under the mouse is outlined; a click takes it, Esc gives up.
  let picking = false
  function pick(done) {
    picking = true
    document.body.classList.add('rv-picking')
    const tip = ui('div', 'rv-tip')
    tip.textContent = '点一下页面上你要说的地方；按 Esc 取消'
    document.body.appendChild(tip)
    const pickable = (el) => !isUi(el) && el !== document.body && el !== document.documentElement
    const move = (ev) => { if (pickable(ev.target)) showMark(ev.target.getBoundingClientRect()); else hideMark() }
    const click = (ev) => {
      if (isUi(ev.target)) return
      ev.preventDefault()
      ev.stopPropagation()
      if (pickable(ev.target)) finish(ev.target)
    }
    const key = (k) => { if (k.key === 'Escape') { k.preventDefault(); k.stopPropagation(); finish(null) } }
    const finish = (el) => {
      picking = false
      document.body.classList.remove('rv-picking')
      tip.remove()
      hideMark()
      removeEventListener('mousemove', move, true)
      removeEventListener('click', click, true)
      removeEventListener('keydown', key, true)
      done(el)
    }
    addEventListener('mousemove', move, true)
    addEventListener('click', click, true)
    addEventListener('keydown', key, true)
  }

  function openPop(target, anchor, x, y) {
    document.querySelectorAll('.rv-pop').forEach((p) => p.remove())
    const pop = ui('div', 'rv-pop')
    pop.style.left = Math.max(scrollX + 8, Math.min(x, scrollX + innerWidth - 368)) + 'px'
    pop.style.top = y + 'px'
    pop.innerHTML = '<div class="rv-ref"></div><textarea placeholder="你的意见。可以打字，也可以按两下 fn 说话"></textarea>' +
      '<div class="rv-row"><a class="rv-pick"></a><span>⌘ + 回车 发送</span><button>发给 AI</button></div>'
    document.body.appendChild(pop)
    const ref = pop.querySelector('.rv-ref')
    const link = pop.querySelector('.rv-pick')
    const show = () => {
      ref.textContent = anchor ? '指的是：' + describe(anchor) : `说的是「${target.label}」这一块`
      link.textContent = anchor?.selector ? '换一个位置' : '指到页面上的具体位置'
    }
    show()
    const box = pop.querySelector('textarea')
    box.focus()
    link.onclick = () => {
      box.blur() // a hidden box keeping focus would swallow Esc
      pop.style.display = 'none'
      pick((el) => {
        pop.style.display = ''
        if (el) { anchor = elementAnchor(el); target = partOf(el); show() }
        box.focus()
      })
    }
    const send = async () => {
      const text = box.value.trim()
      if (!text) return
      const r = await fetch('/__comment', { method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ page, part: target.id, label: target.label, text, ...anchor }) })
      if (!r.ok) { pop.querySelector('.rv-row span').textContent = '没发出去：' + r.status; return }
      pop.remove()
      refresh()
    }
    pop.querySelector('button').onclick = send
    box.onkeydown = (k) => { if (k.key === 'Enter' && (k.metaKey || k.ctrlKey)) send(); if (k.key === 'Escape') pop.remove() }
  }

  parts.forEach((el, i) => {
    const id = el.dataset.review || `part-${i + 1}`
    ids.set(el, id)
    el.classList.add('rv-host')
    const btn = ui('button', 'rv-btn')
    btn.textContent = '说一句'
    const thread = ui('div', 'rv-thread')
    el.appendChild(btn)
    el.appendChild(thread)
    threads.set(id, thread)
    btn.onclick = (ev) => {
      ev.stopPropagation()
      const r = el.getBoundingClientRect()
      openPop({ id, label: label(el) }, null, r.right + scrollX - 368, r.top + scrollY + 40)
    }
  })
  // Comments on something outside every part go under the page.
  const pageThread = ui('div', 'rv-thread rv-page')
  document.body.appendChild(pageThread)
  threads.set('page', pageThread)

  // Selecting words shows a 「说一句」 button beside them; the comment then quotes them.
  const selBtn = ui('button', 'rv-sel')
  selBtn.textContent = '说一句'
  selBtn.style.display = 'none'
  document.body.appendChild(selBtn)
  let sel = null
  document.addEventListener('mouseup', () => setTimeout(() => {
    if (picking) return
    const s = getSelection()
    const quote = s && !s.isCollapsed ? norm(s.toString()).slice(0, 300) : ''
    if (!quote || isUi(s.anchorNode) || isUi(s.focusNode)) { selBtn.style.display = 'none'; return }
    const range = s.getRangeAt(0)
    const r = range.getBoundingClientRect()
    sel = { quote, target: partOf(range.commonAncestorContainer), x: r.left + scrollX, y: r.bottom + scrollY + 8 }
    // above the words: browser extensions tend to put their own bar below a selection
    const top = r.top > 40 ? r.top - 32 : r.bottom + 6
    Object.assign(selBtn.style, { display: '', left: Math.min(r.right + scrollX - 28, scrollX + innerWidth - 70) + 'px', top: top + scrollY + 'px' })
  }))
  selBtn.onmousedown = (ev) => ev.preventDefault() // keep the selection while clicking
  selBtn.onclick = () => { selBtn.style.display = 'none'; openPop(sel.target, { quote: sel.quote }, sel.x, sel.y + 30) }

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
      // a comment that points at a spot goes under the part that holds the spot now
      const spot = (c.quote || c.selector) && locate(c)
      const t = threads.get(spot ? partOf(spot.nodeType === 1 ? spot : spot.startContainer).id : c.part)
      if (!t) continue
      const you = ui('div', 'rv-msg rv-you')
      you.innerHTML = '<b>你</b>'
      you.append(c.text)
      t.appendChild(you)
      if (c.quote || c.selector) {
        const at = ui('div', 'rv-at')
        if (spot) {
          at.textContent = '指的是：' + describe(c)
          at.onmouseenter = () => { const spot = locate(c); if (spot) showMark(spot.getBoundingClientRect()) }
          at.onmouseleave = hideMark
          at.onclick = () => {
            const spot = locate(c)
            if (!spot) return
            ;(spot.nodeType === 1 ? spot : spot.startContainer.parentElement).scrollIntoView({ block: 'center' })
            showMark(spot.getBoundingClientRect())
          }
        } else {
          at.classList.add('rv-lost')
          at.textContent = '页面改过，原位置对不上了：' + describe(c)
        }
        t.appendChild(at)
      }
      const replies = c.replies.length ? c.replies : [{ text: 'AI 收到了，正在看……', wait: true }]
      for (const a of replies) {
        const m = ui('div', 'rv-msg ' + (a.wait ? 'rv-wait' : 'rv-ai'))
        m.innerHTML = a.wait ? '' : '<b>AI</b>'
        m.append(a.text)
        t.appendChild(m)
      }
    }
  }

  const refreshed = refresh()

  // When the agent changes a file in the folder, the page reloads at the same place. It waits while the
  // user is writing a comment or picking a spot.
  const KEY = 'rv-scroll:' + page
  const back = sessionStorage.getItem(KEY)
  if (back !== null) {
    sessionStorage.removeItem(KEY)
    // again once pictures and the comments above have taken their space
    scrollTo(0, +back)
    addEventListener('load', () => scrollTo(0, +back))
    refreshed.then(() => scrollTo(0, +back), () => undefined)
    const toast = ui('div', 'rv-tip')
    toast.textContent = 'AI 改了页面，已经刷新'
    document.body.appendChild(toast)
    setTimeout(() => toast.remove(), 3000)
  }
  let version = null
  let stale = false
  async function watch() {
    const r = await fetch('/__version').catch(() => null)
    if (!r || !r.ok) return
    const v = (await r.json()).v
    if (version === null) version = v
    else if (v !== version) stale = true
    if (stale && !picking && !document.querySelector('.rv-pop')) {
      sessionStorage.setItem(KEY, String(scrollY))
      location.reload()
    }
  }
  watch()
  setInterval(() => { refresh(); watch() }, 1500)

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
    const box = ui('div', 'rv-zoom')
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
        if url.path == "/__version":
            files = [f for f in ROOT.rglob("*") if f.is_file() and not any(p.startswith(".") for p in f.relative_to(ROOT).parts)]
            v = max((f.stat().st_mtime_ns for f in files), default=0)
            return self.send(200, json.dumps({"v": str(v)}).encode(), "application/json")
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
        # where in the part: words the user selected, or one element they clicked
        item.update({k: c[k][:300] for k in ("quote", "selector", "tag", "snippet") if isinstance(c.get(k), str) and c[k]})
        with INBOX.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        self.send(200, b"{}", "application/json")

    def log_message(self, *args):
        pass


print(f"http://127.0.0.1:{PORT}/", flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
