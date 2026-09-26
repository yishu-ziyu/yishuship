source "$(dirname "$0")/../../fixtures/setup.sh"
start todo
mkdir -p .ship/ideas
idea() {  # file title short slice updated
cat > ".ship/ideas/$1.md" <<MD
---
title: $2
short: $3
date: 2026-09-01
tags: [yishuship, todo]
project: todo
status: building
waiting:
slice: $4
next: 做$4
ship_bar: 我自己每天用
updated: $5
---

## 等你决定
无

## 进度
- [ ] $4

## 决定
| 日期 | 定了什么 | 为什么 |
|---|---|---|

## 为什么做
自己用。

## 用户能看到的行为
- [ ] $4

## 证据

## 遗留
MD
}
idea due-sort "待办列表能按截止日期排序" "截止排序" "第一块：list 按截止日期排" 2026-09-25
idea export-md "把待办导出成 Markdown 清单" "导出清单" "第一块：修好 export.py 导出" 2026-09-20
finish
