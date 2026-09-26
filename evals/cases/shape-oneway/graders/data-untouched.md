---
type: command
---
git diff --quiet base -- data/notes.json notes.py && ! ls *.db *.sqlite *.sqlite3 data/*.db data/*.sqlite 2>/dev/null | grep -q .
