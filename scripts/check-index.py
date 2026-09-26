#!/usr/bin/env python3
"""Check that every path and skill named in the yishuship index still exists.

Reads three levels when present: <repo>/INDEX.md (general),
~/.yishuship/INDEX.md (personal), and <project>/.ship/INDEX.md for the project
containing DIR (default: the current directory). Each table row's last cell
names targets in backticks:
  `skill:<name>`     an installed skill (Claude Code or ~/.agents)
  `~/...` or `/...`  a file or folder on this machine
  `notion:<page>`    a Notion page; cannot be checked from here, listed as unchecked
  anything else      relative to the index's own root (repo or project)

Exit 0 when everything resolves, 1 otherwise (missing targets are listed).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PERSONAL = Path(os.environ.get("YISHUSHIP_HOME") or Path.home() / ".yishuship").expanduser() / "INDEX.md"
SKILL_DIRS = [Path.home() / ".claude" / "skills", Path.home() / ".agents" / "skills"]
PLUGIN_CACHE = Path.home() / ".claude" / "plugins" / "cache"
TARGET = re.compile(r"`([^`]+)`")


def targets(index: Path) -> list[str]:
    found = []
    for line in index.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.lstrip().startswith("|") or len(cells) < 2 or set(cells[-1]) <= set("-: "):
            continue
        if cells[-1] == "Open":
            continue
        found += TARGET.findall(cells[-1])
    return found


def indexes(directory: str | None = None) -> list[tuple[Path, Path]]:
    """(index file, root that relative paths resolve against)."""
    found = [(REPO / "INDEX.md", REPO), (PERSONAL, Path.home())]
    here = Path(directory or ".").expanduser().resolve()
    project = next((r for r in (here, *here.parents) if (r / ".ship" / "INDEX.md").is_file()), None)
    if project:
        found.append((project / ".ship" / "INDEX.md", project))
    return [(f, root) for f, root in found if f.is_file()]


def exists(target: str, root: Path = REPO) -> bool:
    if target.startswith("notion:"):
        return True
    if target.startswith("skill:"):
        name = target.removeprefix("skill:")
        if any((d / name / "SKILL.md").is_file() for d in SKILL_DIRS):
            return True
        return any(PLUGIN_CACHE.glob(f"*/*/*/skills/{name}/SKILL.md"))
    if target.startswith(("~", "/")):
        return Path(target).expanduser().exists()
    return (root / target).exists()


def problems(directory: str | None = None) -> list[str]:
    return [f"{index}: {t}" for index, root in indexes(directory)
            for t in targets(index) if not exists(t, root)]


def main() -> int:
    directory = sys.argv[1] if len(sys.argv) > 1 else None
    missing = problems(directory)
    checked = [str(i) for i, _ in indexes(directory)]
    if missing:
        print("索引里有路径失效：")
        print("\n".join(f"  {m}" for m in missing))
        return 1
    unchecked = [t for index, _ in indexes(directory) for t in targets(index) if t.startswith("notion:")]
    print(f"索引路径全部有效（{', '.join(checked)}）")
    if unchecked:
        print(f"未检查（Notion，需用到时确认）：{', '.join(unchecked)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
