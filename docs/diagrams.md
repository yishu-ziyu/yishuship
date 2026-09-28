# Showing structure to the user

The user judges behavior. A wall of prose makes them rebuild the structure in
their head; a small diagram hands it over. The design of a slice is shown so
they can confirm it before any code is written: code is costly to undo, and a
design left in chat is lost at the next session.

## Which view, when

| Moment | Show |
|---|---|
| Behaviors cross more than one screen | The screen flow: each screen, what the user can act on there, an arrow to where it leads. No visual detail. |
| A behavior branches (works / fails, empty / loading / error) | A state diagram, or a sequence diagram with both branches. |
| Before building a slice | The design: the parts involved and how data or requests move between them (a box-and-arrow picture), marking what is new or changed; as before → after when an existing shape changes. For a bug, the same picture with the broken step marked. |
| Done | Before → after, as in `skills/shared/done.md`. |
| A decision | The layout in `skills/shared/asking.md`. |

Writing the screen flow out is what surfaces the missing path ("where does it
go when generation fails?"). If a question like that appears, it goes to the
user with the other open behaviors.

```
[导出设置页]
  选格式：PDF / Word
  「开始导出」 ──▶ [生成中]
                     「取消」 ──▶ [导出设置页]
                     完成后 ──▶ [下载完成]
                                  「打开文件」
```

## Drawing

For the page, draw it as a small HTML file in the evidence folder (boxes, arrows,
labels in product words), list it under `## 看得见`, and check it with
`scripts/snap.py` like any other picture. In the terminal, text art.

- The smallest view that answers the current question. Keep only the screens,
  calls, files, states, and boundaries it needs; one question, one zoom level.
- Mermaid (`flowchart`, `sequenceDiagram`, `stateDiagram-v2`) only where the
  terminal renders it; otherwise text art in a code block.
- Within 72 columns, about 36 Chinese characters. A Chinese character takes two
  columns: when boxes or aligned columns hold Chinese, pad by display width
  (`unicodedata.east_asian_width(c) in "WF"` counts two) with a script, and
  print the result before pasting it.
- Labels in the user's language and product words. Trade-offs and causes go in
  two or three plain sentences beside the diagram, not in bullets.
- A one-line fact or a trivial edit gets no diagram. A layout too dense for
  text art goes into the progress file as a picture, where the page beside the
  terminal shows it (`skills/shared/asking.md`).

## Sources

- Screen flow: Basecamp, *Shape Up*, "Find the Elements" (breadboarding).
- Code shape views: HumanLayer, `show-me` skill (humanlayer/skills).
- One zoom level per diagram: Simon Brown, C4 model.
- Trade-offs as sentences: Amazon, 2017 shareholder letter (narrative memos).
