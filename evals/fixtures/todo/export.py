"""Export the todo list as a Markdown checklist."""
from todo import load


def to_markdown():
    lines = []
    for item in load():
        mark = "x" if item["done"] else " "
        lines.append(f"- [{mark}] {item['title']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(to_markdown(), end="")
