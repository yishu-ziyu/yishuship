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
t = Path("test_todo.py"); s = t.read_text()
s = s.replace('''

if __name__''', '''

class SortTest(unittest.TestCase):
    def test_list_sorts_by_due(self):
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            todo.list_items()
        lines = out.getvalue().splitlines()
        order = [n for l in lines for n in ["报税", "交房租", "买牛奶", "置身事内"] if n in l]
        self.assertEqual(order, ["报税", "交房租", "买牛奶", "置身事内"])


if __name__''')
t.write_text(s)
PY
git_ commit -qam "feat: list sorts by due date"
python3 todo.py done 2
git_ commit -qam "chore: rent paid"
mkdir -p .ship/ideas
cat > .ship/ideas/due-sort.md <<'MD'
---
title: 待办列表能按截止日期排序
short: 截止排序
date: 2026-09-20
tags: [yishuship, todo]
project: todo
status: building
waiting:
slice: 第二块：做完的沉到最后
now:
next: 做第二块，做完给你看前后对比
ship_bar: 我自己每天早上用
appetite: 两块
updated: 2026-09-24
---

## 等你决定
无

## 进度
- [x] 第一块 list 按截止日期排 · 服务：行为1 · `feat: list sorts by due date`
- [ ] 第二块 做完的沉到最后 · 服务：行为2
  - [ ] 做完的待办排在所有没做完的后面

## 决定
| 日期 | 定了什么 | 为什么 |
|---|---|---|
| 2026-09-20 | 没日期的排最后，list 默认就排 | 有期限的先看到，不用记参数 |
| 2026-09-23 | 做完的沉到最后，不隐藏 | 还想看到今天做完了什么 |

## 设计
### 第一块 list 按截止日期排
服务：行为1
list 输出前按截止日期排，没日期的放最后。
不这样做：存的时候就排好，会打乱 done 用的编号。
你确认了 2026-09-20

### 第二块 做完的沉到最后
服务：行为2
排序时先看做没做完，再看截止日期；编号仍是原来的编号。
不这样做：做完就从列表隐藏，你说还想看到。
你确认了 2026-09-23

## 为什么做
每天早上看清单，想先看到最急的事；报税快到期了还排在最后。

## 怎样算做对了
每天早上只看 list 的前两条就知道先做什么。
从哪看出来：我自己每天早上用一周

## 这次不做
- 按标签分组、提醒通知

## 用户能看到的行为
- [x] `todo.py list` → 报税（09-30）、交房租（10-01）、买牛奶（10-05）、读完《置身事内》，有日期的从早到晚在前
- [x] 交房租做完后 `todo.py list` → 报税、买牛奶、读完《置身事内》，最后是打了 x 的交房租

## 证据
### 第一块 list 按截止日期排
证明：行为1
改之后：4. 报税 (09-30) / 2. 交房租 (10-01) / 1. 买牛奶 (10-05) / 3. 读完《置身事内》
复查：python3 -m unittest test_todo.SortTest

## 遗留
MD
finish
