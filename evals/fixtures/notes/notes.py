#!/usr/bin/env python3
"""My notes. Everything lives in data/notes.json.

  python3 notes.py new "标题" "正文"
  python3 notes.py list
  python3 notes.py find 关键词
"""
import datetime
import json
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data" / "notes.json"


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def save(notes):
    DATA.write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv):
    notes = load()
    if argv[:1] == ["new"] and len(argv) == 3:
        notes.append({"title": argv[1], "body": argv[2], "created": datetime.date.today().isoformat()})
        save(notes)
    elif argv == ["list"]:
        for n in notes:
            print(f"{n['created']}  {n['title']}")
    elif argv[:1] == ["find"] and len(argv) == 2:
        for n in notes:
            if argv[1] in n["title"] or argv[1] in n["body"]:
                print(f"{n['created']}  {n['title']}")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
