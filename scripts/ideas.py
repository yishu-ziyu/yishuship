#!/usr/bin/env python3
"""List every idea in progress across registered projects.

Projects are registered in ~/.yishuship/projects (one absolute path per line).
Each project keeps one progress file per idea at .ship/ideas/<slug>.md.

  ideas.py                 print the overview
  ideas.py --json          machine-readable
  ideas.py --register DIR  add a project (idempotent); links it into Obsidian if configured
  ideas.py --link-all      (re)create the Obsidian links for every registered project
  ideas.py --refresh FILE  rewrite the "走到哪了" summary of a progress file from its front matter
  ideas.py --current DIR   the active idea for DIR, as JSON
  ideas.py --status-line DIR   one line for the terminal status line (empty if none)
  ideas.py --route DIR     where /yishuship should go from DIR, as JSON
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

REGISTRY = Path.home() / ".yishuship" / "projects"
CONFIG = Path.home() / ".yishuship" / "config"
ACTIVE = {"shaping", "building", "waiting", "shipping"}
QUIET_DAYS = 7
RECENT_SHIP_DAYS = 30


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
          "continue" the current idea has work to do
          "overview" no idea in progress here; show every idea
    Free text the user typed is judged by the skill, not here.
    """
    here = Path(directory).expanduser().resolve()
    root = next((r for r in (here, *here.parents) if (r / ".ship" / "ideas").is_dir()), None)
    ideas = load(root) if root else []
    active = sorted((i for i in ideas if i.get("status") in ACTIVE),
                    key=lambda i: (i.get("updated", ""), i["file"]), reverse=True)
    current_idea = active[0] if active else None
    if current_idea is None:
        step = "overview"
    elif current_idea.get("waiting"):
        step = "ask"
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
    groups: dict[str, list[dict]] = {"waiting": [], "active": [], "quiet": [], "paused": [], "shipped": []}
    missing = []
    for root in projects():
        if not root.is_dir():
            missing.append(str(root))
            continue
        for idea in load(root):
            status, age = idea.get("status", ""), days_since(idea.get("updated", ""))
            idea["age"] = age
            if status == "paused":
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


def status_line(idea: dict, columns: int | None = None) -> str:
    """State first and in color, then which idea, then what to type.

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
    elif idea.get("status") == "shipping":
        color, state, action = cyan, "● 准备上线", "打 /yishuship 继续"
    else:
        color, state = green, "● 在做"
        action, hint = idea.get("slice") or "打 /yishuship 继续", not idea.get("slice")
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
    titles = {"waiting": "在等你决定", "active": "进行中",
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
        idea = current(argv[1])
        columns = os.environ.get("COLUMNS", "")
        if idea:
            print(status_line(idea, int(columns) if columns.isdigit() else None))
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
