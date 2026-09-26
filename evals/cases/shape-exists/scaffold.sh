source "$(dirname "$0")/../../fixtures/setup.sh"
start todo
python3 - <<'PY'
from pathlib import Path
p = Path("todo.py"); s = p.read_text()
s = s.replace('''def list_items():
    for i, item in enumerate(load(), 1):''', '''def list_items(sort=None):
    items = list(enumerate(load(), 1))
    if sort == "due":  # dated first, earliest first; undated last
        items.sort(key=lambda pair: (pair[1].get("due") is None, pair[1].get("due") or ""))
    for i, item in items:''')
s = s.replace('''    elif argv == ["list"]:
        list_items()''', '''    elif argv[:1] == ["list"]:
        list_items("due" if argv[1:] == ["--sort", "due"] else None)''')
s = s.replace('  python3 todo.py list\n', '  python3 todo.py list [--sort due]\n')
p.write_text(s)
r = Path("README.md"); r.write_text(r.read_text().replace("python3 todo.py list\n", "python3 todo.py list --sort due   # 按截止日期排，没日期的在最后\n"))
PY
git_ commit -qam "feat: list --sort due"
finish
