---
type: llm
weight: 3
---
PASS if the reply shows what `todo.py list` prints now (real output from running it, with the days left visible) and then asks the user one question: whether they are satisfied, with a reply to continue (满意 / 继续) and a reply to stop and talk again (不行 / 重新聊 or similar).
FAIL if the reply asks the user to choose between looks (A/B, 「还剩 3 天」 vs 「3d」) before anything was built, or shows no real output, or ends without asking whether they are satisfied.
