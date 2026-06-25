## 发现报告

> 任务 ID: 20260626-044005 | 阶段: 发现 | 日期: 2026-06-26

### 用户画像

- **谁**: 使用 Claude Code 进行产品开发的独立开发者 / 小团队（1-3 人），典型角色是全栈工程师兼产品经理。技术水平中高级，熟悉 CLI、Git、终端工作流，但不是专业 PM。
- **场景**: 有一个产品想法，需要从模糊需求推进到可交付代码。当前流程是"聊天里说想法 → 直接让 AI 写代码 → 反复返工"，缺乏结构化的需求梳理和决策沉淀。
- **不满**: 聊天式开发丢失上下文，需求在会话间断裂；小改动可以直接写，但中大型功能缺乏"先想清楚再动手"的纪律；没有机制防止 scope creep 和做着做着忘了为什么做。

### 问题验证

- **证据**:
  - DEVLOG.md 记录了 yishuship 的起源故事："在开发 uni-rag 的过程中，发现现有 Ship 工作流有两个核心痛点：不够连贯（需求在聊天里飘）+ 不够长程（没有跨会话的产品记忆）"（来源: `/Users/mahaoxuan/Developer/yishuship/DEVLOG.md` 第 9-12 行）
  - ThoughtWorks Radar 2026-04 将 Claude Code 移至 Adopt，指出"harness engineering"正成为确保 agentic workflow 可靠的关键实践（来源: thoughtworks.cn, 2026-04-15）
  - 2026 年行业数据显示：84% 开发者使用/计划使用 AI 工具，但 2/3 的开发者对结果不满意；企业代码生成 AI 支出达 40 亿美元，但"采用不等于满意"（来源: Stack Overflow Developer Survey 2025, Menlo Ventures 2025, 引自 medium.com/@haberlah）
  - Reddit r/ClaudeWorkflows 社区已出现 "Multi-Agent SDLC Workflow: Claude as PM/CTO" 的手动组合方案（来源: reddit.com/r/ClaudeWorkflows, 2026-06-09），说明需求真实存在但缺乏开箱即用的方案
- **频率**: 每次中大型功能开发都会遇到，对于独立开发者约每周 2-5 次
- **严重程度**: 中等。不是阻塞型问题（开发者仍然能完成工作），但是效率和质量的持续损耗。小改动可以跳过（SKILL.md 中有"快速通道"机制），但中大型功能的返工成本显著

### 竞品扫描

| 竞品 | 方案 | 优势 | 劣势 |
|------|------|------|------|
| **heliohq/ship** | Claude Code 插件，12 个 skill 构成对抗式工程 harness（intake → design → dev → review → QA → handoff）。host + peer 并行设计、证据分级（L1/L2/L3）、状态机暂停/恢复 | 开源成熟，工程层机制完善（对抗式设计、阶段隔离、fix loop）；社区验证过（Reddit/GitHub 有大量讨论） | **没有 PM 层**：直接进 design，跳过"做不做"的判断；没有竞品调研、用户画像、决策沉淀；适合"已经知道要做什么"的场景 |
| **Cursor Plan Mode** | IDE 内置的 Plan 模式，先分析代码库 → 生成实现计划 → 用户确认后才写代码。支持 @ 引用文件和文档 | IDE 原生体验，零安装成本；模型聚合器（可切换 GPT/Claude/Gemini）；Composer Agent 模式支持多文件编辑 | **没有持久化**：计划存在临时文件中，会话断了就丢；**没有 PM 流程**：Plan 模式只做"怎么做"，不做"做不做"；**绑定 IDE**：不支持 CLI/Terminal 工作流 |
| **GitHub Copilot Workspace** | Issue → Plan → Code → PR 全流程，基于 GitHub 生态。强制"计划模式"（spec coding），AI 在生成代码前先产出实施计划 | 深度集成 GitHub（Issue/PR/Actions/Codespaces）；100 万 token 上下文支持（2026-03）；企业级安全 | 技术预览已于 2025-05 结束，用户手册已归档（2025-09），状态不明；**没有 PM 调研层**：从 Issue 开始，假设需求已经定义好；绑定 GitHub 生态 |
| **OpenAI Symphony** | 开源的 long-running automation service。从 Linear 拉 issue → 创建隔离 workspace → 运行 coding agent → CI/PR review → 落 PR。强调 proof of work | 解决"持续任务流"问题（不只是单次对话）；workspace 隔离降低上下文污染；WORKFLOW.md 配置化 | engineering preview 阶段，非即用产品；**没有 PM 层**：假设 issue 已经写好；依赖 Linear + 本地 coding agent；Elixir 参考实现，学习成本高 |

### 机会判断

- **值得做**: 是
- **理由**:
  1. 竞品全部聚焦"工程执行层"（怎么写代码），没有任何工具系统性地解决"PM 层"（做不做、为什么做、做完怎么验证方向）。yishuship 的 PM intake（发现→定义→设计→验证）填补了这个空白。
  2. 行业趋势明确：从 Vibe Coding 走向 Spec Coding / Harness Engineering。GitHub 官方已声明"specification becomes the source of truth"（来源: github.com, 2025a）。yishuship 的结构化 PM 流程正好契合这个方向。
  3. SkillOpt 训练循环是独有的技术壁垒：通过数据驱动优化 skill 文档，越用越好。竞品的 workflow 是静态的 prompt 模板。
  4. yishuship 基于 Claude Code 生态（Skill + Plugin + Hook），与现有工具链兼容，不需要替换开发环境。
- **我们的优势**:
  1. **唯一集成 PM + 工程的 harness**: 竞品要么只做工程（ship）、要么只做 IDE 内计划（Cursor）、要么只做任务调度（Symphony），yishuship 是唯一把"发现→定义→设计→验证→实现→发布→观察→学习"串成完整闭环的方案。
  2. **证据驱动的质量门**: 63 维度评分框架（pm_scorer）+ SkillOpt 训练循环，用数据而非感觉判断 PM 文档质量。
  3. **对抗式设计**: host + peer 并行调研 + diff 辩论，防止单一视角盲区。这在竞品中只有 ship 有类似机制，但 ship 没有 PM 层前置。
  4. **磁盘沉淀**: 所有产物持久化在 `.ship/tasks/<task_id>/`，支持跨会话恢复和决策追溯。竞品大多依赖会话内上下文。
- **不做的代价**:
  - 独立开发者/小团队继续在"聊天式开发"中反复返工，每次中大型功能浪费 30-60% 时间在需求澄清和返工上
  - Claude Code 生态中缺乏结构化的 PM 工具，harness engineering 只停留在工程层，PM 判断仍依赖个人经验和记忆
  - SkillOpt 的 PM 评分训练循环无法验证——没有真实端到端运行，63 维度评分框架无法证明其有效性
