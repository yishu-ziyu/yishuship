---
type: llm
group: target
focus: 'file:.ship/PROJECT.md'
---
PASS if .ship/PROJECT.md exists and, in its own words, says what this product is (a command-line todo list kept in todos.json, with add / list / done and a markdown export) and how it is built (the files or parts and how they relate), consistent with the repository, and lists the new idea.
FAIL if the file is missing, its "这是什么" or "怎么搭的" part is empty or generic, or it contradicts the repository.
