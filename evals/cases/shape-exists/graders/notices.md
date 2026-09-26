---
type: llm
weight: 2
---
PASS if the reply clearly tells the user that sorting by due date already exists in this project (the `list --sort due` option), and recommends either not building it or only a small change on top (for example making it the default), as a decision for the user.
FAIL if it does not notice the existing option, or plans to build due-date sorting from scratch.
