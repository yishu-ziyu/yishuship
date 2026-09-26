#!/usr/bin/env bash
# Put screenshots in front of the user: a temporary page opened beside the
# terminal (cmux split) or in the default browser.
#
#   show-evidence.sh "<title>" "<image>|<caption>" ["<image>|<caption>" ...]
#
# Pairs are laid out two per row, so pass before/after in order. Prints the
# command that closes the page and deletes the temporary folder.
set -euo pipefail
[ "$#" -ge 2 ] || { echo "usage: show-evidence.sh <title> <image|caption>..." >&2; exit 2; }

dir=$(mktemp -d /tmp/yishuship-evidence.XXXXXX)
python3 - "$dir" "$@" <<'PY'
import html, shutil, sys
from pathlib import Path

out, title, *items = sys.argv[1], sys.argv[2], *sys.argv[3:]
figures = []
for n, item in enumerate(items):
    path, _, caption = item.partition("|")
    src = Path(path).expanduser()
    if not src.is_file():
        sys.exit(f"missing image: {src}")
    name = f"{n:02d}{src.suffix.lower()}"
    shutil.copy(src, Path(out) / name)
    figures.append(f'<figure><img src="{name}"><figcaption>{html.escape(caption)}</figcaption></figure>')

Path(out, "index.html").write_text(f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>{html.escape(title)}</title><style>
body{{margin:0;background:#111;color:#ddd;font:14px/1.5 -apple-system,"PingFang SC",sans-serif}}
main{{max-width:1500px;margin:0 auto;padding:24px}} h1{{font-size:17px;margin:0 0 20px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} figure{{margin:0}}
figcaption{{color:#aaa;font-size:12px;margin:6px 2px 0}}
img{{width:100%;border-radius:8px;border:1px solid #333;display:block;cursor:zoom-in}}
img.big{{position:fixed;inset:0;width:auto;max-width:98vw;max-height:98vh;margin:auto;z-index:9;
cursor:zoom-out;box-shadow:0 0 0 100vmax rgba(0,0,0,.85)}}
</style></head><body><main><h1>{html.escape(title)}</h1><div class="grid">{"".join(figures)}</div>
<p style="color:#777;font-size:12px">点图放大，再点还原</p></main>
<script>document.querySelectorAll('img').forEach(i=>i.onclick=()=>i.classList.toggle('big'))</script>
</body></html>""", encoding="utf-8")
PY

page="file://$dir/index.html"
if command -v cmux >/dev/null 2>&1 && [ -n "${CMUX_WORKSPACE_ID:-}" ]; then
  opened=$(cmux browser open-split "$page" --focus true)
  surface=$(printf '%s' "$opened" | sed -n 's/.*surface=\([^ ]*\).*/\1/p')
  echo "opened in cmux: $page"
  echo "close with: cmux close-surface --surface $surface && rm -rf $dir"
else
  open "$page"
  echo "opened in browser: $page"
  echo "close with: rm -rf $dir"
fi
