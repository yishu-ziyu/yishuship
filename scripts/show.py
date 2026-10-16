"""Draws the page beside the terminal that shows what the agent is talking about.

  show.py DIR

Reads DIR/.show/items.jsonl (one line per thing the agent put there: id, at, title, and either html or a
file under .show/files/) and writes DIR/index.html. The newest thing fills the page; older ones wait on a
timeline at the bottom, fainter the older they are, and a click brings one back. scripts/review.py serves
DIR, so each thing gets a 「说一句」 button and the page reloads itself when index.html changes.
"""
import datetime, html, json, sys
from pathlib import Path

ROOT = Path(sys.argv[1])
ITEMS = ROOT / ".show" / "items.jsonl"


def body(item):
    if "html" in item:
        return item["html"]
    src = html.escape(item["file"])
    suffix = Path(item["file"]).suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        return f'<img src="{src}" alt="{html.escape(item["title"])}">'
    if suffix in (".mp4", ".webm", ".mov"):
        return f'<video src="{src}" controls autoplay muted loop playsinline></video>'
    return f'<iframe src="{src}"></iframe>'


def clock(at):
    try:
        return datetime.datetime.fromisoformat(at.replace("Z", "+00:00")).astimezone().strftime("%H:%M")
    except ValueError:
        return ""


items = [json.loads(l) for l in ITEMS.read_text(encoding="utf-8").splitlines() if l.strip()] if ITEMS.exists() else []
sections = "\n".join(
    f'<section class="item" id="{html.escape(i["id"])}" data-review="{html.escape(i["id"])}">'
    f'<h2>{html.escape(i["title"])}</h2><div class="body">{body(i)}</div></section>' for i in items)
n = len(items)
chips = "\n".join(
    f'<a class="chip" href="#{html.escape(i["id"])}" style="opacity:{max(0.35, 1 - (n - 1 - k) * 0.12):.2f}">'
    f'<b>{clock(i["at"])}</b>{html.escape(i["title"])}</a>' for k, i in enumerate(items))

page = f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><title>此刻</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#faf8f4;color:#1d1b18;font:16px/1.65 -apple-system,"PingFang SC",sans-serif;
  display:flex;flex-direction:column;min-height:100vh}}
main{{flex:1;padding:28px 32px 120px;max-width:1100px;width:100%;margin:0 auto}}
.item{{display:none}} .item.on{{display:block;animation:in .25s ease-out}}
@keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.item h2{{font-size:20px;margin:0 0 14px}}
.body img,.body video{{max-width:100%;border-radius:10px;border:1px solid #e4ded3}}
.body iframe{{width:100%;height:70vh;border:1px solid #e4ded3;border-radius:10px;background:#fff}}
.body table{{border-collapse:collapse;background:#fff;font-size:15px}}
.body th,.body td{{border:1px solid #e4ded3;padding:6px 10px;text-align:left;vertical-align:top}}
.body th{{background:#f4f1ea}}
.old{{display:none;margin:-8px 0 14px;font-size:13px;color:#7a746a}} .old a{{color:#5b4a86}}
.empty{{color:#7a746a;margin-top:30vh;text-align:center}}
nav{{position:fixed;left:0;right:0;bottom:0;background:#fffdf9ee;border-top:1px solid #e4ded3;
  display:flex;gap:8px;overflow-x:auto;padding:10px 16px;backdrop-filter:blur(6px)}}
.chip{{flex:none;max-width:260px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:13px;
  color:#1d1b18;text-decoration:none;border:1px solid #e4ded3;border-radius:999px;padding:5px 12px;background:#fff}}
.chip b{{font-weight:600;color:#7a746a;margin-right:6px}}
.chip.on{{border-color:#5b4a86;box-shadow:0 0 0 2px #e9e2f8;opacity:1 !important}}
</style></head><body>
<main>
<p class="old">这是之前的。<a href="#" id="latest">回到最新的</a></p>
{sections or '<p class="empty">AI 还没放东西上来。它说到表、图、界面变化、计划或结果时，会出现在这里。</p>'}
</main>
<nav>{chips}</nav>
<script>
const items = [...document.querySelectorAll('.item')], chips = [...document.querySelectorAll('.chip')]
function show() {{
  if (!items.length) return
  const want = location.hash.slice(1)
  const at = Math.max(0, items.findIndex((s) => s.id === want))
  const i = want && items[at].id === want ? at : items.length - 1
  items.forEach((s, k) => s.classList.toggle('on', k === i))
  chips.forEach((c, k) => c.classList.toggle('on', k === i))
  document.querySelector('.old').style.display = i === items.length - 1 ? 'none' : 'block'
  chips[i].scrollIntoView({{inline: 'center', block: 'nearest'}})
}}
document.getElementById('latest').onclick = (e) => {{ e.preventDefault(); history.replaceState(null, '', location.pathname); show() }}
addEventListener('hashchange', show)
show()
</script>
</body></html>
"""
(ROOT / "index.html").write_text(page, encoding="utf-8")
