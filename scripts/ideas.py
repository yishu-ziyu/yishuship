#!/usr/bin/env python3
"""List every idea in progress across registered projects.

Projects are registered in ~/.yishuship/projects (one absolute path per line);
set YISHUSHIP_HOME to use another folder than ~/.yishuship.
Each project keeps one progress file per idea at .ship/ideas/<slug>.md.

  ideas.py                 print the overview
  ideas.py --json          machine-readable
  ideas.py --register DIR  add a project (idempotent); links it into Obsidian if configured
  ideas.py --link-all      (re)create the Obsidian links for every registered project
  ideas.py --refresh FILE  rewrite the "走到哪了" summary of a progress file from its front matter
  ideas.py --current DIR   the active idea for DIR, as JSON
  ideas.py --status-line DIR   one line for the terminal status line (empty if none)
  ideas.py --route DIR     where /yishuship should go from DIR, as JSON
  ideas.py --visuals DIR   the pictures under ## 看得见 of the active idea, and any file missing
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

HOME = Path(os.environ.get("YISHUSHIP_HOME") or Path.home() / ".yishuship").expanduser()
REGISTRY = HOME / "projects"
CONFIG = HOME / "config"
ACTIVE = {"shaping", "building", "waiting", "shipping"}
QUIET_DAYS = 7
RECENT_SHIP_DAYS = 30
STALE_MINUTES = 15  # `now` unchanged this long may be left over from a stopped run


def read_front_matter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta


def idea_files(project: Path) -> list[Path]:
    return sorted((project / ".ship" / "ideas").glob("*.md"))


def load(project: Path) -> list[dict]:
    ideas = []
    for f in idea_files(project):
        meta = read_front_matter(f)
        if not (meta.get("idea") or meta.get("title")):
            continue
        meta.setdefault("idea", meta.get("title", ""))
        meta["file"] = str(f)
        meta.setdefault("project", project.name)
        meta["project_root"] = str(project)
        ideas.append(meta)
    return ideas


def days_since(date_text: str) -> int | None:
    try:
        return (dt.date.today() - dt.date.fromisoformat(date_text)).days
    except ValueError:
        return None


def projects() -> list[Path]:
    if not REGISTRY.exists():
        return []
    return [Path(p) for p in REGISTRY.read_text(encoding="utf-8").splitlines() if p.strip()]


def config() -> dict[str, str]:
    if not CONFIG.exists():
        return {}
    pairs = (line.partition("=") for line in CONFIG.read_text(encoding="utf-8").splitlines())
    return {k.strip(): v.strip() for k, sep, v in pairs if sep and not k.startswith("#")}


def link_into_obsidian(root: Path) -> str | None:
    """<obsidian_dir>/<project>/{ideas,evidence} -> <root>/.ship/{ideas,evidence}.

    Same names on both sides, so relative image links in a progress file
    (../evidence/...) resolve in the repo and in Obsidian alike.
    """
    target_dir = config().get("obsidian_dir")
    if not target_dir:
        return None
    folder = Path(target_dir).expanduser() / root.name
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("ideas", "evidence"):
        source = root / ".ship" / name
        source.mkdir(parents=True, exist_ok=True)
        link = folder / name
        if link.is_symlink() and link.resolve() == source.resolve():
            continue
        if link.exists() or link.is_symlink():
            raise SystemExit(f"{link} exists and is not a link to {source}; not touching it")
        link.symlink_to(source, target_is_directory=True)
    return str(folder)


def register(directory: str) -> None:
    root = Path(directory).expanduser().resolve()
    known = projects()
    if root not in known:
        REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        with REGISTRY.open("a", encoding="utf-8") as f:
            f.write(f"{root}\n")
    print(f"registered {root}")
    linked = link_into_obsidian(root)
    if linked:
        print(f"linked into Obsidian: {linked}")


SUMMARY_START, SUMMARY_END = "<!-- 走到哪了：由 ideas.py --refresh 生成，不要手改 -->", "<!-- /走到哪了 -->"


def refresh(path: str) -> None:
    """Rewrite the summary callout at the top of a progress file from its front matter."""
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    meta = read_front_matter(file)
    if meta.get("waiting"):
        count = len([q for q in re.split(r"[；;]", meta["waiting"]) if q.strip()])
        state = f"在等你决定 {count} 项" if count > 1 else "在等你决定"
    else:
        state = STEP.get(meta.get("status", ""), meta.get("status", ""))
    lines = [SUMMARY_START, "> [!NOTE]", f"> **走到哪了 · ● {state}**"]
    if meta.get("slice"):
        lines.append(f"> {meta['slice']}")
    if meta.get("waiting"):
        lines.append(f"> 等你：{meta['waiting']}")
    if meta.get("next"):
        lines.append(f"> 下一步：{meta['next']}")
    lines += [f"> 上次更新：{meta.get('updated', '')}", SUMMARY_END]
    block = "\n".join(lines)
    if SUMMARY_START in text:
        text = re.sub(re.escape(SUMMARY_START) + r".*?" + re.escape(SUMMARY_END), lambda _: block, text, flags=re.S)
    else:
        end = text.index("\n---", 3) + 4  # after the closing front-matter fence
        text = text[:end] + "\n\n" + block + text[end:]
    file.write_text(text, encoding="utf-8")
    print(f"refreshed {file}")


def review_due(idea: dict) -> bool:
    """Shipped, its review date has come, and nobody has looked back yet."""
    days = days_since(idea.get("review_on", ""))
    return idea.get("status") == "shipped" and not idea.get("reviewed") and days is not None and days >= 0


def project_root(directory: str) -> Path | None:
    here = Path(directory).expanduser().resolve()
    return next((r for r in (here, *here.parents) if (r / ".ship" / "ideas").is_dir()), None)


def current(directory: str) -> dict | None:
    """Most recently updated active idea in the project containing DIRECTORY."""
    here = Path(directory).expanduser().resolve()
    for root in (here, *here.parents):
        if (root / ".ship" / "ideas").is_dir():
            active = [i for i in load(root) if i.get("status") in ACTIVE]
            return max(active, key=lambda i: (i.get("updated", ""), i["file"]), default=None)
    return None


def route(directory: str) -> dict:
    """What /yishuship should do from DIRECTORY, decided from disk alone.

    step: "ask"      the current idea waits on the user
          "review"   a shipped idea is due for a look back at whether it worked
          "continue" the current idea has work to do
          "start"    inside a project (progress folder or git repo) with no idea
                     in progress; talk about this project only
          "overview" outside any project; show every idea
    Free text the user typed is judged by the skill, not here.
    """
    here = Path(directory).expanduser().resolve()
    root = next((r for r in (here, *here.parents) if (r / ".ship" / "ideas").is_dir()), None)
    root = root or next((r for r in (here, *here.parents) if (r / ".git").exists()), None)
    ideas = load(root) if root else []
    active = sorted((i for i in ideas if i.get("status") in ACTIVE),
                    key=lambda i: (i.get("updated", ""), i["file"]), reverse=True)
    current_idea = active[0] if active else None
    due = [i for i in ideas if review_due(i)]
    if current_idea is not None and current_idea.get("waiting"):
        step = "ask"
    elif due:
        step, current_idea = "review", due[0]
    elif current_idea is None:
        step = "start" if root else "overview"
    else:
        step = "continue"
    brief = lambda i: {k: i.get(k, "") for k in ("idea", "status", "waiting", "slice", "file", "updated")}
    return {
        "step": step,
        "project_root": str(root) if root else None,
        "current": brief(current_idea) if current_idea else None,
        "other_active": [brief(i) for i in active[1:]],
        "paused": [brief(i) for i in ideas if i.get("status") == "paused"],
    }


def overview() -> tuple[dict[str, list[dict]], list[str]]:
    groups: dict[str, list[dict]] = {"review": [], "waiting": [], "active": [], "quiet": [], "paused": [], "shipped": []}
    missing = []
    for root in projects():
        if not root.is_dir():
            missing.append(str(root))
            continue
        for idea in load(root):
            status, age = idea.get("status", ""), days_since(idea.get("updated", ""))
            idea["age"] = age
            if review_due(idea):
                groups["review"].append(idea)
            elif status == "paused":
                groups["paused"].append(idea)
            elif status == "shipped":
                if age is not None and age <= RECENT_SHIP_DAYS:
                    groups["shipped"].append(idea)
            elif status in ACTIVE and idea.get("waiting"):
                groups["waiting"].append(idea)
            elif status in ACTIVE and age is not None and age > QUIET_DAYS:
                groups["quiet"].append(idea)
            elif status in ACTIVE:
                groups["active"].append(idea)
    for items in groups.values():
        items.sort(key=lambda i: i.get("updated", ""), reverse=True)
    return groups, missing


STEP = {"shaping": "想法成形中", "building": "在做", "waiting": "等你决定",
        "shipping": "准备上线", "paused": "暂停中", "shipped": "已上线"}


def width(text: str) -> int:
    """Columns the text takes in a terminal: CJK and full-width characters take two."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def clip(text: str, limit: int) -> str:
    if width(text) <= limit:
        return text
    kept = ""
    for char in text:
        if width(kept + char) > limit - 1:
            break
        kept += char
    return kept + "…"


def slice_things(idea: dict) -> list[tuple[bool, str]]:
    """The current slice's things: the indented checklist under its line in ## 进度."""
    key = re.match(r"[\s\"']*(第.+?块)", idea.get("slice", ""))
    if not key or not idea.get("file"):
        return []
    body = Path(idea["file"]).read_text(encoding="utf-8")
    section = re.search(r"^## 进度\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    things, inside = [], False
    for line in (section.group(1) if section else "").splitlines():
        top = re.match(r"- \[[ xX]\] +(.+)", line)
        sub = re.match(r"\s+- \[([ xX])\] +(.+)", line)
        if top:
            inside = top.group(1).lstrip("\"'").startswith(key.group(1))
        elif sub and inside:
            things.append((sub.group(1).lower() == "x", sub.group(2).strip()))
    return things


def questions(idea: dict) -> list[dict]:
    """## 问题, one per line: `- [ ] 第一块 · <question> · 要你：<action>` (or Agent：/ 实测：…)."""
    if not idea.get("file"):
        return []
    body = Path(idea["file"]).read_text(encoding="utf-8")
    section = re.search(r"^## 问题\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    found = []
    for line in (section.group(1) if section else "").splitlines():
        item = re.match(r"- \[([ xX])\] +(.+)", line)
        if not item:
            continue
        parts = [part.strip() for part in item.group(2).split(" · ")]
        where = parts.pop(0) if len(parts) > 1 and re.fullmatch(r"第.+?块", parts[0]) else ""
        detail = " · ".join(parts[1:])
        asks = re.findall(r"要你[：:]\s*([^；;]+)", detail)
        found.append({"closed": item.group(1).lower() == "x", "slice": where, "text": parts[0],
                      "detail": detail, "ask": asks[-1].strip() if asks else ""})
    return found


def done_slices(idea: dict) -> set[str]:
    """The slices ticked off in ## 进度, by their `第…块` name."""
    body = Path(idea["file"]).read_text(encoding="utf-8") if idea.get("file") else ""
    section = re.search(r"^## 进度\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    return set(re.findall(r"^- \[[xX]\] +(第.+?块)", section.group(1) if section else "", flags=re.M))


def slice_names(idea: dict) -> dict[str, str]:
    """`第一块` → what that slice is, from its line in ## 进度."""
    body = Path(idea["file"]).read_text(encoding="utf-8") if idea.get("file") else ""
    section = re.search(r"^## 进度\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    return {m.group(1): m.group(2).split(" · ")[0].strip()
            for m in re.finditer(r"^- \[[ xX]\] +(第.+?块)\s*(.*)$", section.group(1) if section else "", flags=re.M)}


def evidence_note(idea: dict | None, question: str) -> str:
    """The note under ## 证据 headed `### <question>`: what the evidence shows, one level down."""
    if not idea or not idea.get("file"):
        return ""
    body = Path(idea["file"]).read_text(encoding="utf-8")
    section = re.search(r"^## 证据\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    key = question.rstrip("？?").strip()
    for m in re.finditer(r"^### +(.+?)\n(.*?)(?=^### |\Z)", section.group(1) if section else "", flags=re.M | re.S):
        if m.group(1).rstrip("？?").strip() == key:
            return m.group(2).strip()
    return ""


def visual(ref: str) -> dict:
    """`../evidence/x.png#box=10,20,300,200` → where the page fetches it and the box to draw."""
    path, _, frag = ref.strip().partition("#")
    box = re.fullmatch(r"box=(\d+),(\d+),(\d+),(\d+)", frag)
    src = "/evidence/" + path.split("../evidence/", 1)[1] if "../evidence/" in path else ""
    return {"src": src, "box": [int(n) for n in box.groups()] if box else None}


def visuals(idea: dict | None) -> dict:
    """## 看得见: a picture for every option of the pending question and for every thing it names.

    `### ① <question>` then one line per option:
        `- A ◀ 推荐 · <做法> · <做出来的样子> · 真实截图|示意|没有图 · ../evidence/<file>[#box=x0,y0,x1,y1]`
    `### 词` then one line per thing the question names:
        `- <词> · <它是什么> · ../evidence/<file>#box=x0,y0,x1,y1`
    """
    out = {"options": [], "terms": []}
    if not idea or not idea.get("file"):
        return out
    body = Path(idea["file"]).read_text(encoding="utf-8")
    section = re.search(r"^## 看得见\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    for m in re.finditer(r"^### +(.+?)\n(.*?)(?=^### |\Z)", section.group(1) if section else "", flags=re.M | re.S):
        title, lines = m.group(1).strip(), re.findall(r"^- +(.+)$", m.group(2), flags=re.M)
        for line in lines:
            parts = [p.strip() for p in line.split(" · ")]
            ref = parts.pop() if parts and "../evidence/" in parts[-1] else ""
            if title == "词":
                if parts:
                    out["terms"].append({"word": parts[0], "what": " · ".join(parts[1:]), **visual(ref)})
                continue
            head = re.match(r"([A-Z])\s*(◀\s*推荐)?", parts[0]) if parts else None
            if not head:
                continue
            kind = parts.pop() if len(parts) > 1 and parts[-1] in ("真实截图", "示意", "没有图") else ("示意" if ref else "没有图")
            if not out["options"] or out["options"][-1]["q"] != title:
                out["options"].append({"q": title, "opts": []})
            out["options"][-1]["opts"].append({"letter": head.group(1), "rec": bool(head.group(2)),
                                               "label": parts[1] if len(parts) > 1 else "",
                                               "looks": " · ".join(parts[2:]), "kind": kind, **visual(ref)})
    return out


def visual_problems(idea: dict | None, seen: dict, root: Path | None) -> list[str]:
    """What stops the user from seeing the pending question: an option or a question with no picture, a missing file."""
    if not idea or not idea.get("waiting"):
        return []
    body = Path(idea["file"]).read_text(encoding="utf-8")
    section = re.search(r"^## 等你决定\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    asked: dict[str, list[str]] = {}
    for line in (section.group(1) if section else "").splitlines():
        head = re.match(r"\s*([①-⑩])", line)
        if head:
            asked[head.group(1)] = []
        opt = re.match(r"\s*[├└]─\s*([A-Z])\b", line)
        if opt and asked:
            asked[list(asked)[-1]].append(opt.group(1))
    problems = []
    for mark, letters in asked.items():
        group = next((g for g in seen["options"] if g["q"].startswith(mark)), None)
        if group is None:
            problems.append(f"{mark}: no `### {mark} …` under ## 看得见")
            continue
        have = {o["letter"]: o for o in group["opts"]}
        for letter in letters:
            if letter not in have:
                problems.append(f"{mark} {letter}: no line for this option")
            elif not have[letter]["src"]:
                problems.append(f"{mark} {letter}: no picture (a screenshot, or a 示意 HTML built from real content)")
    block = section.group(1) if section else ""
    for term in seen["terms"]:
        if term["word"] not in block:
            problems.append(f"词 {term['word']}: not in the question as written; name things the question actually says")
    if asked and not seen["terms"]:
        problems.append("### 词 is empty: box every on-screen thing the question names")
    for where, src in ([(f'{g["q"]} {o["letter"]}', o["src"]) for g in seen["options"] for o in g["opts"]]
                       + [(t["word"], t["src"]) for t in seen["terms"]]):
        if src and root and not (root / ".ship" / "evidence" / src[len("/evidence/"):]).is_file():
            problems.append(f"{where}: {src} is missing")
    return problems


def doing(idea: dict) -> tuple[str, str, int, int]:
    """From `now` (`<step> · <thing>`): the step, the thing, its place among the slice's things, and how many."""
    step, _, thing = idea.get("now", "").partition("·")
    step, thing = step.strip(), thing.strip()
    things = slice_things(idea)
    place = next((n for n, (_, text) in enumerate(things, 1) if thing and (thing in text or text in thing)), 0)
    return step, thing, place, len(things)


def quiet_for(idea: dict) -> str:
    """How long the progress file has gone unwritten, once that is long enough to doubt `now`."""
    minutes = int((dt.datetime.now().timestamp() - Path(idea["file"]).stat().st_mtime) // 60)
    if minutes < STALE_MINUTES:
        return ""
    return f"{minutes} 分钟前" if minutes < 60 else f"{minutes // 60} 小时前"


def status_line(idea: dict, columns: int | None = None) -> str:
    """State first and in color, then which idea, then what it is doing now or what to type.

    Uses the idea's short name. When COLUMNS says the terminal is too narrow,
    the tail goes first (next step, then the name); the state is never cut.
    """
    yellow, green, cyan, dim, reset = "\033[1;33m", "\033[32m", "\033[36m", "\033[2m", "\033[0m"
    name = f"{idea.get('project', '')} · {idea.get('short') or idea['idea']}"
    hint = True  # a command hint is shown whole or not at all; a slice may be clipped
    if idea.get("waiting"):
        count = len([q for q in re.split(r"[；;]", idea["waiting"]) if q.strip()])
        color, state = yellow, f"● 等你决定 {count} 项" if count > 1 else "● 等你决定"
        action = "打 /yishuship 查看"
    elif idea.get("status") == "review":
        color, state, action = cyan, "● 该回头看", "打 /yishuship 查看"
    else:
        shipping = idea.get("status") == "shipping"
        color, state = (cyan, "● 准备上线") if shipping else (green, "● 在做")
        now = idea.get("now")
        if now:
            step, thing, place, total = doing(idea)
            now = " · ".join(x for x in (step, thing, f"{place}/{total}" if place else "") if x)
        text = now or (None if shipping else idea.get("slice"))
        action, hint = text or "打 /yishuship 继续", not text
        if idea.get("now") and (age := quiet_for(idea)):
            state += f" · {age}"  # part of the state, so a narrow terminal never hides it
    if columns:
        room = columns - 2 - width(state) - 2  # 2 for a margin; the state always fits whole
        if width(name) + 2 + width(action) > room:
            spare = room - width(name) - 2
            action = clip(action, spare) if spare >= 8 and not hint else ""
        if width(name) > room:
            name = clip(name, room) if room >= 6 else ""
    line = f"{color}{state}{reset}"
    if name:
        line += f"  {name}"
    if action:
        line += f"  {dim}{action}{reset}"
    return line


def describe(idea: dict) -> list[str]:
    head = f"  {idea['project']} · {idea['idea']}"
    step = idea.get("slice") or STEP.get(idea.get("status", ""), idea.get("status", ""))
    lines = [head, f"    {step} · {idea['age']} 天前更新" if idea.get("age") is not None else f"    {step}"]
    if idea.get("waiting"):
        lines.append(f"    等你：{idea['waiting']}")
    lines.append(f"    {idea['project_root']}")
    return lines


def print_overview() -> None:
    groups, missing = overview()
    titles = {"review": "该回头看：上线后做对了没有", "waiting": "在等你决定", "active": "进行中",
              "quiet": f"超过 {QUIET_DAYS} 天没动", "paused": "暂停中", "shipped": f"最近 {RECENT_SHIP_DAYS} 天上线"}
    print("[yishuship] 所有想法")
    if not any(groups.values()):
        print("\n  还没有记录中的想法。打 /yishuship 加一句你的想法，开始第一个。")
    for key, title in titles.items():
        if groups[key]:
            print(f"\n\n{title}")
            for idea in groups[key]:
                print("\n".join(describe(idea)))
    if missing:
        print("\n\n找不到目录（可能移动过）")
        for path in missing:
            print(f"  {path}")
    broken = index_problems()
    if broken:
        print("\n\n索引里有路径失效（修正 INDEX.md 里的那一行）")
        for item in broken:
            print(f"  {item}")


def index_problems() -> list[str]:
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_index", Path(__file__).with_name("check-index.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.problems()


def main(argv: list[str]) -> int:
    if argv[:1] == ["--register"] and len(argv) == 2:
        register(argv[1])
    elif argv == ["--link-all"]:
        for root in projects():
            if root.is_dir():
                print(link_into_obsidian(root) or "obsidian_dir not configured")
    elif argv[:1] == ["--refresh"] and len(argv) == 2:
        refresh(argv[1])
    elif argv[:1] == ["--current"] and len(argv) == 2:
        print(json.dumps(current(argv[1]), ensure_ascii=False))
    elif argv[:1] == ["--status-line"] and len(argv) == 2:
        idea, root = current(argv[1]), project_root(argv[1])
        due = [i for i in load(root) if review_due(i)] if root else []
        if due and not (idea and idea.get("waiting")):
            idea = dict(due[0], status="review")
        columns = os.environ.get("COLUMNS", "")
        if idea:
            print(status_line(idea, int(columns) if columns.isdigit() else None))
    elif argv[:1] == ["--visuals"] and len(argv) == 2:
        idea, root = current(argv[1]), project_root(argv[1])
        seen = visuals(idea)
        problems = visual_problems(idea, seen, root)
        print(json.dumps({**seen, "problems": problems}, ensure_ascii=False, indent=2))
        return 1 if problems else 0
    elif argv[:1] == ["--route"] and len(argv) == 2:
        print(json.dumps(route(argv[1]), ensure_ascii=False, indent=2))
    elif argv == ["--json"]:
        groups, missing = overview()
        print(json.dumps({"groups": groups, "missing": missing}, ensure_ascii=False, indent=2))
    elif not argv:
        print_overview()
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
