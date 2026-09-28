---
type: command
---
python3 -m unittest test_todo 2>&1 | tail -1 | grep -q '^OK'
