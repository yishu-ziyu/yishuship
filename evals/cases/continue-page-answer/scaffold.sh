source "$(dirname "$0")/../../fixtures/setup.sh"
start todo
mkdir -p .ship/ideas .ship/evidence/2026-09-28-days-left
python3 - <<'PY'  # a small real picture of the new list, so the pointed spot exists
import struct, zlib
w, h = 640, 200
rows = b"".join(b"\x00" + bytes([250, 250, 250]) * w for _ in range(h))
png = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
open(".ship/evidence/2026-09-28-days-left/after.png", "wb").write(
    b"\x89PNG\r\n\x1a\n" + png(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + png(b"IDAT", zlib.compress(rows)) + png(b"IEND", b""))
PY
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
next: 等你看第一块满不满意
ship_bar:
appetite: 一块
updated: 2026-09-28
---

# 意图 · 为什么做、做什么

## 为什么做
看清单时只看到日期，要自己心算离今天还有几天；想一眼看出哪件快到了。

## 用户能看到的行为
- [x] 打 `todo.py list` → 有截止日期的待办后面写着还剩几天，写法「还剩 3 天」

## 这次不做
- 不改排序，不加颜色

# 任务 · 做到哪了

## 等你决定
无

## 你的反馈
- [ ] 2026-09-28 · 括号里太挤了，日期和天数挤在一起看不清 · ../evidence/2026-09-28-days-left/after.png#box=40,20,600,60
- [ ] 2026-09-28 · 你的回答：不行 · 只要天数，日期可以不显示

## 进度
- [ ] 第一块 list 显示还剩几天 · 服务：行为1

## 决定
| 日期 | 定了什么 | 为什么 |
|---|---|---|
| 2026-09-26 | 做，先做第一块 | 你说“做吧” |
| 2026-09-28 | 不行 | 在页面上点了不行：只要天数，日期可以不显示 |

## 证据
### 第一块 list 显示还剩几天
证明：行为1
![改之后 · 1. [ ] 买牛奶 (截止 2026-10-05，还剩 7 天)](../evidence/2026-09-28-days-left/after.png)
复查：python3 todo.py list

## 遗留
MD
finish
