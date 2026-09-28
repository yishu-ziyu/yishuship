source "$(dirname "$0")/../../fixtures/setup.sh"
start todo
mkdir -p .ship/ideas
cat > .ship/ideas/days-left.md <<'MD'
---
title: 待办后面显示还剩几天
short: 剩几天
date: 2026-09-26
tags: [yishuship, todo]
project: todo
status: building
waiting:
slice: 第一块：list 显示还剩几天
now:
next: 做第一块
ship_bar:
appetite: 一块
updated: 2026-09-26
---

# 意图 · 为什么做、做什么

## 为什么做
看清单时只看到日期，要自己心算离今天还有几天；想一眼看出哪件快到了。

## 用户能看到的行为
- [ ] 打 `todo.py list` → 有截止日期的待办后面写着还剩几天 → 写法待定：「还剩 3 天」（推荐，一看就懂）或「3d」（更短）

## 这次不做
- 不改排序，不加颜色

# 任务 · 做到哪了

## 等你决定
无

## 进度
- [ ] 第一块 list 显示还剩几天 · 服务：行为1

## 决定
| 日期 | 定了什么 | 为什么 |
|---|---|---|
| 2026-09-26 | 做，先做第一块 | 你说“做吧” |

## 证据

## 遗留
MD
finish
