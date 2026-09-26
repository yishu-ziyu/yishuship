source "$(dirname "$0")/../../fixtures/setup.sh"
start todo
mkdir -p .ship/ideas
cat > .ship/ideas/due-sort.md <<'MD'
---
title: 待办列表能按截止日期排序
short: 截止排序
date: 2026-09-20
tags: [yishuship, todo]
project: todo
status: waiting
waiting: 做不做；没截止日期的放哪；默认排还是加参数
slice: 第一块：list 按截止日期排
next: 等你回答 1-3 后开始第一块
ship_bar:
updated: 2026-09-20
---

## 等你决定
```
[yishuship] 需要你决定


①  做不做
   │
   ├─ A  做，第一块：list 按截止日期排     ◀ 推荐
   │     每天打开就先看到最急的
   │
   └─ B  不做：继续按添加顺序
         什么都不用改


②  没写截止日期的待办放哪
   │
   ├─ A  排在最后                          ◀ 推荐
   │     有期限的先看到
   │
   └─ B  排在最前
         提醒你补日期，但会挡住快到期的事


③  什么时候按截止日期排
   │
   ├─ A  list 默认就排                     ◀ 推荐
   │     不用记参数
   │
   └─ B  加 --sort due 才排
         多记一个参数


回复示例：1A 2A 3A
```

## 进度
- [ ] 第一块 list 按截止日期排

## 决定
| 日期 | 定了什么 | 为什么 |
|---|---|---|

## 为什么做
每天早上看清单，想先看到最急的事；现在按添加顺序排，报税快到期了还排在最后。

## 用户能看到的行为
- [ ] 打 `todo.py list` → 有截止日期的按日期从早到晚排在前面 → ② ③ 待定

## 证据

## 遗留
MD
finish
