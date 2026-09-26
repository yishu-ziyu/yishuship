source "$(dirname "$0")/../../fixtures/setup.sh"
start todo
mkdir -p .ship/ideas
cat > .ship/ideas/tags.md <<'MD'
---
title: 按标签看待办
short: 标签筛选
date: 2026-09-10
tags: [yishuship, todo]
project: todo
status: building
waiting:
slice: 第二块：list 按标签筛选
next: 做第二块：list --tag 家里 只列出这个标签的
ship_bar: 我自己每天用，能只看"工作"的事
updated: 2026-09-12
---

## 等你决定
无

## 进度
- [x] 第一块 add 时能写 --tag · `init`
- [ ] 第二块 list --tag 只列出这个标签的

## 决定
| 日期 | 定了什么 | 为什么 |
|---|---|---|
| 2026-09-10 | 一条待办只有一个标签 | 够用，简单 |

## 为什么做
工作和家里的事混在一起，上班时只想看工作的。

## 用户能看到的行为
- [x] `add ... --tag 工作` → 这条带上标签
- [ ] `list --tag 工作` → 只列出工作的

## 证据

## 遗留
MD
git_ add -A; git_ commit -qm "docs: progress file"
python3 - <<'PY'
from pathlib import Path
p = Path("todo.py"); s = p.read_text()
s = s.replace('''def list_items():
    for i, item in enumerate(load(), 1):''', '''def list_items(tag=None):
    for i, item in enumerate(load(), 1):
        if tag and item.get("tag") != tag:
            continue''')
s = s.replace('''    elif argv == ["list"]:
        list_items()''', '''    elif argv[:1] == ["list"]:
        list_items(argv[2] if argv[1:2] == ["--tag"] else None)''')
p.write_text(s)
PY
git_ commit -qam "feat: list --tag filters by tag"
finish "chore: nothing"
