# yishuship

## 这是什么
给产品人用的 Claude Code 插件：只打一个 /yishuship，把一个想法从一句话跟到用户能用上。你管用户看到什么、做什么，Agent 管里面的一切；需要你决定时停下来问，做完拿改前改后的证据。（出自 AGENTS.md、README.md）

## 怎么搭的
```
你打 /yishuship ──▶ skills/yishuship  读 ideas.py --route，决定去哪
                        ├─▶ skills/idea   想法成形
                        ├─▶ skills/next   做一块 / 问你 / 上线
                        └─▶ skills/ideas  所有想法
                   idea、next 都按 skills/shared 的规则：怎么问、怎样算做完、进度文件
                   具体做法不写在技能里，查 INDEX.md 三层索引

项目里的 .ship/ ── PROJECT.md · ideas/*.md · evidence/ · screens/
     ▲ 写                         │ 读
   Agent               scripts/ideas.py  总览 · 路由 · 追踪 · 生成 PROJECT.md 下半
                                  ├─▶ statusline.sh  终端底栏
                                  └─▶ page.py        终端旁边的页面
```

## 界面现在长什么样
- 终端旁边的页面（没有 Agent 在做时）· screens/side-page.png · 2026-09-28
- 终端底栏 · screens/status-line.txt · 2026-09-28
- 所有想法（/yishuship:ideas）· screens/overview.txt · 2026-09-28

<!-- 以下由 ideas.py --project 生成，不要手改 -->

## 现在能做什么
- 用户在 Agent 运行中看状态栏 → 看到 `在验证 · 行为2 · 1✓ 2… 3○` · 来自「Agent 干活的时候，我也跟得上」 · 旧格式，没写复查
- 用户看"影响" → 看到的是用户行为，不是文件 · 来自「Agent 干活的时候，我也跟得上」 · 旧格式，没写复查
- 只打 /yishuship：带一句话是新想法或回答，不带就自己判断下一步 · 来自「一个想法从说出口到用户能用上，全程跟住」 · 旧格式，没写复查
- 需要我决定时停下来问，竖着排、写后果、标推荐 · 来自「一个想法从说出口到用户能用上，全程跟住」 · 旧格式，没写复查
- 做完时给改前改后的证据，截图放在终端旁边的页面里 · 来自「一个想法从说出口到用户能用上，全程跟住」 · 旧格式，没写复查
- 终端底部一行：状态在前，看得出有没有在等我 · 来自「一个想法从说出口到用户能用上，全程跟住」 · 旧格式，没写复查
- 做工程、设计、接 AI 能力时，按需去读外部规范 · 来自「一个想法从说出口到用户能用上，全程跟住」 · 旧格式，没写复查

## 想法
- Agent 干活的时候，我也跟得上 · 在做 · [ideas/agent-now.md](ideas/agent-now.md)
- 一个想法从说出口到用户能用上，全程跟住 · 在做 · [ideas/yishuship.md](ideas/yishuship.md)

## 待办和技术债
- skills 总行数 399/400：第一块删掉了 progress-file.md 里讲 Obsidian 链接的两行（脚本自己会做） · 来自「Agent 干活的时候，我也跟得上」
- 窗口约 50 列时，"2…" 会和截断补的 "…" 连成 "2……"，看着含糊 · 来自「Agent 干活的时候，我也跟得上」
- Claude Code 自带任务清单只显示前 5 项（anthropics/claude-code#54355），状态栏脚本读不到它 · 来自「Agent 干活的时候，我也跟得上」
- 同一天更新的两个想法，状态栏按文件名选中了"想法跟到上线"，没显示这个在等你决定的想法（`ideas.py` 的 `current` 只按 updated 和文件名排序） · 来自「Agent 干活的时候，我也跟得上」
- "碰到了哪些行为"目前是整个想法的行为清单，还分不出哪几条是这一块碰到的；需要进度文件记下每块的行为（第三块越界提醒也要用） · 来自「Agent 干活的时候，我也跟得上」
- 两次真实会话都没出现"在验证"这一步：Agent 把验证并进了"在写"，页面上看不出它在跑产品验证 · 来自「Agent 干活的时候，我也跟得上」
- vibereader-macos 没有 DESIGN.md（原生界面参考已指向 Notion "Apple Design"） · 来自「一个想法从说出口到用户能用上，全程跟住」
- 原生客户端读 SSE 未验证（sse-streaming-cors 组件已标注） · 来自「一个想法从说出口到用户能用上，全程跟住」
- 旧版 .ship/tasks 只读保留：red-herring-and-gun 23、tianshu-integrations 6、uni-rag 6、asset-agent 3、chrome-md-editor 2、vibereader 1 · 来自「一个想法从说出口到用户能用上，全程跟住」
- vibereader 上线暂停中，恢复需要你本人新建 macOS 测试账户 · 来自「一个想法从说出口到用户能用上，全程跟住」
- Codex 侧的 Waza 是 9-21 的旧版 · 来自「一个想法从说出口到用户能用上，全程跟住」
- 插件装好后当前会话调不到 /yishuship，必须开新会话 · 来自「一个想法从说出口到用户能用上，全程跟住」

<!-- /生成 -->
