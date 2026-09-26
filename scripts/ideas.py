#!/usr/bin/env python3
"""List every idea in progress across registered projects.

Projects are registered in ~/.yishuship/projects (one absolute path per line).
Each project keeps one progress file per idea at .ship/ideas/<slug>.md.

  ideas.py                 print the overview
  ideas.py --json          machine-readable
  ideas.py --register DIR  add a project (idempotent)
  ideas.py --current DIR   the active idea for DIR, as JSON
  ideas.py --status-line DIR   one line for the terminal status line (empty if none)
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REGISTRY = Path.home() / ".yishuship" / "projects"
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
        if not meta.get("idea"):
            continue
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


def register(directory: str) -> None:
    root = Path(directory).expanduser().resolve()
    known = projects()
    if root not in known:
        REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        with REGISTRY.open("a", encoding="utf-8") as f:
            f.write(f"{root}\n")
    print(f"registered {root}")


def current(directory: str) -> dict | None:
    """Most recently updated active idea in the project containing DIRECTORY."""
    here = Path(directory).expanduser().resolve()
    for root in (here, *here.parents):
        if (root / ".ship" / "ideas").is_dir():
            active = [i for i in load(root) if i.get("status") in ACTIVE]
            return max(active, key=lambda i: (i.get("updated", ""), i["file"]), default=None)
    return None


def overview() -> tuple[dict[str, list[dict]], list[str]]:
    groups: dict[str, list[dict]] = {"waiting": [], "active": [], "quiet": [], "shipped": []}
    missing = []
    for root in projects():
        if not root.is_dir():
            missing.append(str(root))
            continue
        for idea in load(root):
            status, age = idea.get("status", ""), days_since(idea.get("updated", ""))
            idea["age"] = age
            if status == "shipped":
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
        "shipping": "准备上线", "shipped": "已上线"}


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
              "quiet": f"超过 {QUIET_DAYS} 天没动", "shipped": f"最近 {RECENT_SHIP_DAYS} 天上线"}
    print("[yishuship] 所有想法")
    if not any(groups.values()):
        print("\n  还没有记录中的想法。用 /yishuship:idea 开始一个。")
    for key, title in titles.items():
        if groups[key]:
            print(f"\n\n{title}")
            for idea in groups[key]:
                print("\n".join(describe(idea)))
    if missing:
        print("\n\n找不到目录（可能移动过）")
        for path in missing:
            print(f"  {path}")


def main(argv: list[str]) -> int:
    if argv[:1] == ["--register"] and len(argv) == 2:
        register(argv[1])
    elif argv[:1] == ["--current"] and len(argv) == 2:
        print(json.dumps(current(argv[1]), ensure_ascii=False))
    elif argv[:1] == ["--status-line"] and len(argv) == 2:
        idea = current(argv[1])
        if idea:
            step = idea.get("slice") or STEP.get(idea.get("status", ""), "")
            waiting = f"等你：{idea['waiting']}" if idea.get("waiting") else "等你：无"
            print(f"\033[2myishuship ▸ {idea['idea']} · {step} · {waiting}\033[0m")
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
