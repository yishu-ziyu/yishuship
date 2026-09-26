#!/usr/bin/env python3
"""A tiny todo list for the command line. Items live in todos.json.

  python3 todo.py add "买牛奶" [--due 2026-10-01] [--tag 家里]
  python3 todo.py list
  python3 todo.py done 2
"""
import datetime
import json
import sys
from pathlib import Path

DATA = Path(__file__).with_name("todos.json")


def load():
    return json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else []


def save(items):
    DATA.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add(text, due=None, tag=None):
    if due:
        datetime.date.fromisoformat(due)  # reject bad dates before saving
    items = load()
    items.append({"text": text, "due": due, "tag": tag, "done": False})
    save(items)


def done(number):
    items = load()
    items[number - 1]["done"] = True
    save(items)


def list_items():
    for i, item in enumerate(load(), 1):
        mark = "x" if item.get("done") else " "
        due = f"  (截止 {item['due']})" if item.get("due") else ""
        print(f"{i}. [{mark}] {item['text']}{due}")


def main(argv):
    if argv[:1] == ["add"] and len(argv) >= 2:
        opts = dict(zip(argv[2::2], argv[3::2]))
        add(argv[1], opts.get("--due"), opts.get("--tag"))
    elif argv[:1] == ["done"] and len(argv) == 2:
        done(int(argv[1]))
    elif argv == ["list"]:
        list_items()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
