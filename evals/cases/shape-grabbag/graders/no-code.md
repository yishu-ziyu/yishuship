---
type: command
---
git diff --quiet base -- Sources README.md && ! git ls-files --others --exclude-standard | grep -v '^\.ship/'
