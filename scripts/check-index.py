#!/usr/bin/env python3
"""Check that every path and skill named in the yishuship index still exists.

Reads <repo>/INDEX.md and ~/.yishuship/INDEX.md (if present). Each table row's
last cell names targets in backticks:
  `skill:<name>`     an installed skill (Claude Code or ~/.agents)
  `~/...` or `/...`  a file or folder on this machine
  `docs/...`         a path inside this repository

Exit 0 when everything resolves, 1 otherwise (missing targets are listed).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INDEXES = [REPO / "INDEX.md", Path.home() / ".yishuship" / "INDEX.md"]
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


def exists(target: str) -> bool:
    if target.startswith("skill:"):
        name = target.removeprefix("skill:")
        if any((d / name / "SKILL.md").is_file() for d in SKILL_DIRS):
            return True
        return any(PLUGIN_CACHE.glob(f"*/*/*/skills/{name}/SKILL.md"))
    if target.startswith(("~", "/")):
        return Path(target).expanduser().exists()
    return (REPO / target).exists()


def problems() -> list[str]:
    missing = []
    for index in INDEXES:
        if not index.is_file():
            continue
        missing += [f"{index}: {t}" for t in targets(index) if not exists(t)]
    return missing


def main() -> int:
    missing = problems()
    checked = [str(i) for i in INDEXES if i.is_file()]
    if missing:
        print("索引里有路径失效：")
        print("\n".join(f"  {m}" for m in missing))
        return 1
    print(f"索引路径全部有效（{', '.join(checked)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
