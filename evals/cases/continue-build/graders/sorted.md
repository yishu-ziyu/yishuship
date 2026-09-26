---
type: command
weight: 3
---
out=$(python3 todo.py list) || exit 1
echo "$out"
pos() { printf '%s\n' "$out" | grep -n "$1" | head -1 | cut -d: -f1; }
a=$(pos 报税); b=$(pos 交房租); c=$(pos 买牛奶); d=$(pos 置身事内)
[ -n "$a" ] && [ -n "$d" ] && [ "$a" -lt "$b" ] && [ "$b" -lt "$c" ] && [ "$c" -lt "$d" ]
