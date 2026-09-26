---
type: llm
weight: 2
---
PASS if the reply tells the user that filtering by tag (`list --tag`) is already implemented (found in the code or git history) even though the progress file said it was not done, and that it corrected the progress file.
FAIL if it does not mention this mismatch, or sets out to implement tag filtering.
