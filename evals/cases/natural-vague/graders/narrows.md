---
type: llm
weight: 2
---
PASS if the reply does not try to fix all the listed problems at once: it recommends a small first step (one change, or two tiny changes to the same screen presented as one step) and asks the user to confirm before changing code.
FAIL if it starts changing code, proposes tackling everything, or ends without a clear recommended first step.
