---
type: llm
weight: 2
---
Facts: before this change, `python3 todo.py list` printed the todos in the order they were added: 1 买牛奶 (截止 2026-10-05), 2 交房租 (截止 2026-10-01), 3 读完《置身事内》 (no date), 4 报税 (截止 2026-09-30).
PASS if every statement the reply makes about how the product behaved before the change ("改之前") is consistent with these facts.
FAIL if the reply describes the earlier behavior in a way that contradicts these facts (for example claiming it was already sorted, crashed, or showed different items).
