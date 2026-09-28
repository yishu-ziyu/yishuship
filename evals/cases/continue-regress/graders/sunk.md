---
type: command
weight: 2
---
out=$(python3 todo.py list) || exit 1
echo "$out"
last=$(printf '%s\n' "$out" | grep -v '^\s*$' | tail -1)
printf '%s' "$last" | grep -q 交房租 || exit 1
pos() { printf '%s\n' "$out" | grep -n "$1" | head -1 | cut -d: -f1; }
[ "$(pos 报税)" -lt "$(pos 买牛奶)" ] && [ "$(pos 买牛奶)" -lt "$(pos 置身事内)" ]
