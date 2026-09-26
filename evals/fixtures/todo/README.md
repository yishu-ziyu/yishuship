# todo

我自己用的命令行待办清单。数据存在 `todos.json`。

```
python3 todo.py add "买牛奶" --due 2026-10-01 --tag 家里
python3 todo.py list
python3 todo.py done 2
python3 export.py > todos.md     # 导出成 Markdown 清单
```

测试：`python3 -m unittest`
