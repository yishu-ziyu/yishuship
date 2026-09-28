source "$(dirname "$0")/../../fixtures/setup.sh"
start todo
python3 - <<'PY'
from pathlib import Path
p = Path("todo.py"); s = p.read_text()
s = s.replace('''def list_items():
    for i, item in enumerate(load(), 1):''', '''def list_items():
    items = sorted(enumerate(load(), 1), key=lambda p: (p[1].get("due") is None, p[1].get("due") or ""))
    for i, item in items:''')
p.write_text(s)
PY
git_ commit -qam "feat: list sorts by due date"
mkdir -p .ship/ideas
cat > .ship/ideas/due-sort.md <<'MD'
---
title: 待办列表能按截止日期排序
short: 截止排序
date: 2026-09-01
tags: [yishuship, todo]
project: todo
status: shipped
waiting:
slice: 第一块：list 按截止日期排（已上线）
next: 已上线
ship_bar: 我自己每天早上用
appetite: 一块
shipped: 2026-09-10
review_on: 2026-09-17
reviewed:
updated: 2026-09-10
---

## 等你决定
无

## 进度
- [x] 第一块 list 按截止日期排 · `feat: list sorts by due date`

## 决定
| 日期 | 定了什么 | 为什么 |
|---|---|---|
| 2026-09-02 | 没日期的排最后，list 默认就排 | 有期限的先看到，不用记参数 |

## 为什么做
每天早上看清单，想先看到最急的事；报税快到期了还排在最后。

## 怎样算做对了
每天早上只看 list 的前两条就知道先做什么，不再从头到尾找最急的。
从哪看出来：usage.log 里每天早上的 list 记录，和我勾掉的是不是前两条

## 这次不做
- 按标签分组、提醒通知

## 最危险的假设
我会不会真的每天早上看 list · 怎么验证：上线一周后问自己

## 用户能看到的行为
- [x] `todo.py list` → 报税（09-30）、交房租（10-01）、买牛奶（10-05）、读完《置身事内》

## 证据

## 遗留
MD
cat > usage.log <<'LOG'
2026-09-11 08:03 list
2026-09-11 08:05 done 4
2026-09-12 08:10 list
2026-09-12 08:11 done 2
2026-09-13 08:01 list
2026-09-15 08:20 list
2026-09-15 08:24 done 1
2026-09-16 08:02 list
2026-09-18 08:07 list
2026-09-22 08:12 list
LOG
finish
