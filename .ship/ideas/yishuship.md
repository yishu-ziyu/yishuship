---
idea: yishuship：一个想法从说出口到用户能用上，全程跟住
project: yishuship
status: waiting
waiting: 给一个真实的新想法，用 /yishuship:idea 从零走一遍
slice: 切片 5：用真实新想法走一遍 idea
ship_bar: 在自己的真实项目上连续用两周，每个想法都能从 idea 走到上线，中途不需要手动绕开它
updated: 2026-09-26
---

## 为什么做
一个人同时有多个项目和想法。想法在聊天里会丢、会断，做到一半会忘。
需要一层很薄的管理：记住每个想法到哪了，需要人决定时停下来问，做完时给出证据。

## 用户能看到的行为
- [x] /yishuship:idea 把一句话变成具体行为和第一小块，停下来等我决定
- [x] /yishuship:next 做下一小块，做完附改前改后证据
- [x] /yishuship:ideas 列出所有项目里活着的想法，包括暂停的
- [x] 终端底部一行显示当前想法和是否在等我
- [x] 做工程、设计、接 AI 能力时，按需去读外部规范，不塞进 yishuship
- [ ] 在 Codex 里也能用 → 待定

## 决定
- 2026-09-26 v3 只留 idea / next / ideas 三个入口 · 理由：试点证明管用的就这些
- 2026-09-26 Waza 只装 hunt、think、check、read · 理由：其余与已有的设计、写作、研究流程重叠
- 2026-09-26 上线标准（用户确认）：真实项目连续用两周，每个想法都能从 idea 走到上线 · 理由：它是给自己用的工作方式
- 2026-09-26 只放管理，做事方式按"什么时候"写进索引 · 理由：不是每一块都值得整套方法；索引按时机写才会被翻开
- 2026-09-26 uni-rag 规则只留三条命令说明，只在用户输入命令时用；Ponytail 段整段删去 · 理由：插件已不在本机
- 2026-09-26 索引分仓库版与本机版 · 理由：仓库公开，本机路径不外露
- 2026-09-26 v3 分支先用，顺手后再合并 main · 理由：留退路

## 切片
1. [done] v3 基础：三个命令、共用规则、四个脚本、插件安装 · 证据：ed2302a，/yishuship:ideas 与 /yishuship:next 真实调用
2. [done] 暂停的想法不再从列表消失 · 证据：87c5a49
3. [done] 改成"管理层 + 向外索引"：INDEX.md、~/.yishuship/INDEX.md、check-index.py；next 不再写死 TDD · 证据：64beb43、3.1.1（提问前必须先读规则），/yishuship:next 只读试跑两次
4. [done] 清理旧版残留：uni-rag 两份 CLAUDE.md 与入门文档改为新命令，删去失效的 Ponytail 段 · 证据：同一问题改前答"pm-intake → design → dev"，改后答"/yishuship:idea"
5. [now] 用一个真实新想法走一遍 /yishuship:idea
6. [next] 接入 Codex

## 下一步
切片 5：用户给一个真实的新想法，用 /yishuship:idea 从一句话开始走，检验"从 0 开始"这条路。

## 遗留
- 旧版 .ship/tasks 只读保留：red-herring-and-gun 23、tianshu-integrations 6、uni-rag 6、asset-agent 3、chrome-md-editor 2、vibereader 1
- uni-rag 与 vibereader 两个仓库里改好的规则文件尚未提交
- vibereader 上线暂停中，恢复需要用户本人新建 macOS 测试账户
- Codex 侧的 Waza 是 9-21 的旧版
