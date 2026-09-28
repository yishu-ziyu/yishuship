"""Read yishuship's .ship records into one data.json the prototype versions share. Read-only."""
import json, re
from pathlib import Path
SHIP = Path(__file__).resolve().parents[2]
IT = SHIP / "003-项目管理体系"
items = {}

def imgs(text, base=""):
    return [{"alt": a, "src": "/ship/" + (base + p if not p.startswith("../") else p[3:])}
            for a, p in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text)]
def strip_imgs(t): return re.sub(r"!\[[^\]]*\]\([^)]+\)\n?", "", t).strip()
def add(i): items[i["id"]] = {"up": [], "down": [], "fields": [], "images": [], "date": "", **i}

# 需求
FIELDS = ["来源", "日期", "原话", "当时看到的", "我们的理解", "怎样算解决", "去向"]
text = (SHIP / "需求.md").read_text(encoding="utf-8")
for m in re.finditer(r"^## (R-\d+) (.+?)\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S):
    rid, title, body = m.groups()
    f, cur = {}, None
    for line in body.splitlines():
        h = re.match(r"^(" + "|".join(FIELDS) + r")[：:](.*)$", line)
        if h: cur = h.group(1); f[cur] = h.group(2).strip(); continue
        if cur: f[cur] += "\n" + line
    go = f.get("去向", "")
    first = re.split(r"[；;。]", go.strip())[0]
    if re.match(r"(做完|做了)", first): st = "done"
    elif "搁置" in first or "没进意图" in first: st = "parked"
    elif re.match(r"(待定|还没|没开始)", first) or first.startswith("R-010 到"): st = "open"
    else: st = "doing"
    add({"id": rid, "type": "需求", "title": title.strip(), "status": st, "date": f.get("日期", "").strip(),
         "source": f.get("来源", "").split("·")[0].strip(),
         "fields": [[k, strip_imgs(f[k])] for k in FIELDS if k in f and k not in ("日期",) and strip_imgs(f[k])],
         "images": imgs(body)})

# 意图
t = (IT / "意图.md").read_text(encoding="utf-8")
title = re.search(r"^# 003 意图[：:](.+)$", t, re.M).group(1).strip()
secs = re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", t, flags=re.M | re.S)
add({"id": "003", "type": "意图", "title": title, "status": "doing", "date": "2026-09-28",
     "fields": [[h, b.strip()] for h, b in secs],
     "up": re.findall(r"R-\d+", re.search(r"^来自[：:](.+)$", t, re.M).group(1))})

# 设计
t = (IT / "设计.md").read_text(encoding="utf-8")
for m in re.finditer(r"^## (§\d+) (.+?)\n(.*?)(?=^## |\Z)", t, flags=re.M | re.S):
    sid, ttl, body = m.groups()
    ok = re.search(r"你确认了[：:]\s*(\S+)", body)
    add({"id": "003-" + sid, "type": "设计", "title": ttl.strip(), "status": "done" if ok else "wait",
         "date": ok.group(1) if ok else "", "fields": [["内容", strip_imgs(re.sub(r"你确认了.*", "", body))]],
         "images": imgs(body, "003-项目管理体系/"), "up": ["003"]})

# 任务 + 验证
v = (IT / "验证.md").read_text(encoding="utf-8")
ver = {m.group(1): m.group(2).strip() for m in re.finditer(r"^## (003-T\d+) .*?\n(.*?)(?=^## |\Z)", v, flags=re.M | re.S)}
t = (IT / "任务.md").read_text(encoding="utf-8")
STM = {"做完": "done", "在做": "doing", "返工": "redo", "没开始": "open"}
for m in re.finditer(r"^## (003-T\d+) (.+?)\n(.*?)(?=^## |\Z)", t, flags=re.M | re.S):
    tid, ttl, body = m.groups()
    steps = re.findall(r"^- \[([ xX])\] (.+)$", body, re.M)
    st = re.search(r"^状态[：:](.+)$", body, re.M).group(1).strip()
    src = re.search(r"^来自[：:](.+)$", body, re.M).group(1)
    fields = [["步骤", "\n".join(("✓ " if d.strip() else "○ ") + s for d, s in steps)]]
    if tid in ver: fields.append(["怎么验的", ver[tid]])
    add({"id": tid, "type": "任务", "title": ttl.strip(), "status": STM.get(st, "open"), "statusText": st,
         "progress": [sum(1 for d, _ in steps if d.strip()), len(steps)], "fields": fields,
         "up": re.findall(r"R-\d+", src) + ["003"], "dep": re.findall(r"003-T\d+", re.search(r"^依赖[：:](.+)$", body, re.M).group(1))})

# 问题
t = (IT / "问题.md").read_text(encoding="utf-8")
for row in re.findall(r"^\| (003-P\d+) \| (.+?) \| (.+?) \| (.+?) \|$", t, re.M):
    pid, found, what, how = row
    add({"id": pid, "type": "问题", "title": what, "status": "done" if "修好" in how or "已改" in how else "open",
         "fields": [["发现于", found], ["现象", what], ["处理", how]], "up": re.findall(r"003-T\d+", found),
         "down": re.findall(r"R-\d+", how)})

# 决定：ADR + 各想法文件里的决定表
for f in sorted((SHIP / "决定").glob("*.md")):
    t = f.read_text(encoding="utf-8")
    m = re.match(r"# (ADR-\d+) (.+)", t)
    secs = re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", t, flags=re.M | re.S)
    add({"id": m.group(1), "type": "决定", "title": m.group(2).strip(), "status": "wait" if "提议" in t else "done",
         "date": (re.search(r"^日期[：:](.+)$", t, re.M) or [None, ""])[1].strip(),
         "fields": [[h, b.strip()] for h, b in secs], "up": ["003"]})
n = 0
for f in sorted((SHIP / "ideas").glob("*.md")):
    t = f.read_text(encoding="utf-8")
    idea = re.search(r"^title:(.+)$", t, re.M).group(1).strip()
    for d, what, why in re.findall(r"^\| *(20\d\d-\d\d-\d\d) *\| *(.+?) *\| *(.+?) *\|$", t, re.M):
        n += 1
        add({"id": f"D-{n:02d}", "type": "决定", "title": what, "status": "done", "date": d,
             "fields": [["为什么", why], ["出自想法", idea]]})

# 反向链接
for i in list(items.values()):
    for u in i["up"]:
        if u in items and i["id"] not in items[u]["down"]: items[u]["down"].append(i["id"])
    for d in i["down"]:
        if d in items and i["id"] not in items[d]["up"]: items[d]["up"].append(i["id"])

proj = (SHIP / "PROJECT.md").read_text(encoding="utf-8")
what = re.search(r"## 这是什么\n(.+?)\n", proj).group(1)
what = re.sub(r"（出自.*?）", "", what)
data = {"project": "yishuship", "what": what, "order": ["需求", "意图", "设计", "任务", "问题", "决定"], "items": items}
Path(__file__).with_name("data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
print(Counter(i["type"] for i in items.values()), Counter((i["type"], i["status"]) for i in items.values() if i["type"] == "需求"))
missing = [im["src"] for i in items.values() for im in i["images"] if not (SHIP / im["src"][6:]).exists()]
print("missing images:", missing)
