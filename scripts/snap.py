#!/usr/bin/env python3
"""Screenshot every picture under ## 看得见 so the agent can look at it before the user does.

  snap.py DIR     render each option (its mock, or its screenshot with the box drawn)
                  and each named thing, and print where the PNGs are

A mock that reads fine as code can still overlap, cut off, or hide the one
difference the option is about; a box can miss its target. Only looking finds
that. Uses the `playwright` command if it is installed (no Python packages
needed); without it, says so, and the agent looks at the side page instead.
"""
from __future__ import annotations

import hashlib
import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ideas import current, project_root, visuals  # noqa: E402

TIMEOUT = 90  # seconds per screenshot


def png_size(image: Path) -> tuple[int, int] | None:
    head = image.read_bytes()[:24]
    return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")) if head[:8] == b"\x89PNG\r\n\x1a\n" else None


def framed(image: Path, box: list[int] | None) -> str:
    """A throwaway page showing IMAGE with its box drawn where the side page would draw it."""
    size, mark = png_size(image), ""
    if box and size:
        (w, h), (x0, y0, x1, y1) = size, box
        mark = (f'<i style="position:absolute;border:3px solid #d06a12;left:{x0 / w:.2%};top:{y0 / h:.2%};'
                f'width:{(x1 - x0) / w:.2%};height:{(y1 - y0) / h:.2%}"></i>')
    return (f'<meta charset=utf-8><body style="margin:0;background:#fff"><div style="position:relative;line-height:0">'
            f'<img src="{html.escape(image.as_uri())}" style="width:100%">{mark}</div>')


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    root, idea = project_root(argv[0]), current(argv[0])
    seen = visuals(idea)
    items = ([(f'{g["q"][:1]}{o["letter"]}', o) for g in seen["options"] for o in g["opts"]]
             + [(f'词-{t["word"]}', t) for t in seen["terms"]])
    items = [(name, it) for name, it in items if it.get("src")]
    if not root or not items:
        print("nothing under ## 看得见 to look at")
        return 0
    tool = shutil.which("playwright")
    if not tool:
        print("no `playwright` command here: open the side page and look at every picture yourself")
        return 1
    out = Path(tempfile.gettempdir()) / f"yishuship-snap-{hashlib.sha1(str(root).encode()).hexdigest()[:10]}"
    out.mkdir(exist_ok=True)
    evidence = root / ".ship" / "evidence"
    failed = 0
    for name, it in items:
        source = evidence / it["src"][len("/evidence/"):]
        if source.suffix.lower() != ".html":
            page = out / f"{name}.html"
            page.write_text(framed(source, it.get("box")), encoding="utf-8")
            source = page
        png = out / f"{name}.png"
        try:
            subprocess.run([tool, "screenshot", "--viewport-size=900,700", "--full-page", "--wait-for-timeout=600",
                            source.as_uri(), str(png)], capture_output=True, timeout=TIMEOUT, check=True)
            print(f"{name}: {png}")
        except (subprocess.SubprocessError, OSError):
            failed += 1
            print(f"{name}: could not screenshot {source}")
    print("Open each PNG and look: no overlapping or cut-off text, every box on its thing, "
          "and the difference between the options visible at a glance. Fix and snap again.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
