# yishuship 开发日志

> 从原版 Ship 到 PM+工程一体化的超级个体。

## 2026-06-26 — 项目启动

### 背景

在开发 uni-rag（本地文档问答工具）的过程中，我们发现现有的 Ship 工作流有两个核心痛点：

1. **不够连贯** — 需求在聊天里飘，会话断了就断了，新会话要重新解释背景
2. **不够长程** — Ship 只管"这一次改动"，没有跨会话的产品记忆

更深层的问题：Ship 是一个工程 harness，不是产品管理工具。它回答"怎么做"，但不回答"做不做"。

### 调研

我们对 AI 编码工具中的"产品管理 + 工程执行一体化"做了系统调研：

| 工具 | PM 流程 | 成熟度 |
|------|---------|--------|
| **Cursor Spec Mode** | 专门的 AI-native planning 模式 | 已成熟 |
| **Lovable Brainstorming** | AI PM 角色，对话式澄清需求 | 已成熟 |
| **GitHub Copilot Workspace** | issue → plan → code → PR 全流程 | 已成熟 |
| **Devin** | 任务分析 → 拆解 → 沙盒执行 | 已成熟 |
| **heliohq/ship** | 对抗式设计 + 阶段隔离 + 证据分级 | 已成熟（开源） |

**关键发现**：没有工具同时做到"PM 调研→判断→决策" + "对抗式工程执行"。这是 yishuship 的空白地带。

### 原版 Ship 深度分析

完整阅读了 heliohq/ship 仓库（12 个 skill + hooks + 状态机），发现我们之前只用了简化版（阶段清单），丢掉了原版的核心机制：

| 机制 | 原版 Ship | 我们之前 |
|------|----------|---------|
| **intake** | 需求沉淀到磁盘 | 无 |
| **对抗式设计** | host + peer 并行调查 | 无 |
| **证据分级** | L1/L2/L3 | 无 |
| **阶段隔离** | reviewer 没看过实现 | 无 |
| **状态机** | 可暂停/恢复 | 无 |
| **fix loop** | CI 失败自动修 3 轮 | 无 |
| **智能路由** | 小改动走单 skill | 统一走 12 阶段 |

### 决策

**yishuship = 原版 Ship 工程层 + 新增 PM 层**

```
PM 层（新增）
  发现 → 定义 → 设计 → 验证
                          ↓
工程层（原版 Ship）
  对抗式设计 → 实现 → 测试 → QA → 发布
                          ↓
PM 层（新增）
  观察 → 学习 → 下一迭代
```

---

## 2026-06-26 — PM 全流程设计

### 第一版：5 个问题（被否决）

第一版 PM 层只有 5 个必答问题：
1. 用户是谁？
2. 痛点是什么？
3. 竞品怎么做？
4. 我们独特优势是什么？
5. 最小可行版本是什么？

**问题**：这是问卷，不是流程。没有退出标准，没有产出模板，没有阶段间的流转规则。

### 第二版：8 阶段全生命周期

重新设计，参考 Shape Up（Basecamp）、Lean Startup、Design Sprint 等框架，结合 AI agent 的执行约束：

| 阶段 | 目标 | 产出 | 退出标准 |
|------|------|------|----------|
| 1. 发现 | 识别真实问题 | 01-discovery.md | 用户画像+证据+竞品+机会判断 |
| 2. 定义 | 问题→产品方案 | 02-definition.md | 定位+旅程+指标+范围封顶 |
| 3. 设计 | 确定怎么做 | 03-design.md | 交互+技术+验收+风险 |
| 4. 验证 | 写代码前验证方向 | 04-validation.md | 假设+评审+最小验证 |
| 5. 实现 | 交给工程层 | 代码+测试 | 范围守护+验收通过 |
| 6. 发布 | 交给工程层 | 已发布产品 | 清单+回滚+监控 |
| 7. 观察 | 看真实数据 | 07-observation.md | 指标追踪+用户反馈 |
| 8. 学习 | 提取经验 | 08-learnings.md | 假设回顾+决策复盘 |

**核心设计原则**：
- 每个阶段有明确的输入、产出和退出标准
- 任何阶段不满足退出标准，不能进入下一阶段
- 快速通道：小改动可以跳过发现和定义
- PM 层包裹工程层，不是替代

### AI Agent 执行可行性分析

| 阶段 | AI Agent 能执行吗？ | 约束 |
|------|-------------------|------|
| 发现 | 部分能 | 竞品扫描可以（web search），用户访谈不能 |
| 定义 | 能 | 纯文档产出，LLM 擅长 |
| 设计 | 能 | 原版 Ship 已验证 |
| 验证 | 部分能 | 方案评审能做，用户反馈不能 |
| 实现 | 能 | 原版 Ship 已验证 |
| 发布 | 能 | 原版 Ship 已验证 |
| 观察 | 不能 | AI 无法访问真实用户数据 |
| 学习 | 能 | 纯文档产出 |

**诚实声明**：阶段 1、4、7 在"用户反馈"维度上受限于 AI agent 的能力边界。这些维度标记为"需要人工介入"。

---

## 2026-06-26 — 评分框架设计

### 设计原则

1. **可机械评估** — 每个维度必须能通过规则判断，不依赖"感觉好不好"
2. **0-3 分制** — 0=缺失 / 1=存在但不合格 / 2=合格 / 3=优秀
3. **正则优先** — 能用正则匹配的不用 LLM 判断
4. **内容质量兜底** — 只有无法机械判断的维度才用 LLM judge

### 评分维度

8 个阶段 × 63 个维度 × 0-3 分 = **189 分满分**

| 阶段 | 维度数 | 满分 | 合格线 |
|------|--------|------|--------|
| 发现 | 9 | 27 | 17 |
| 定义 | 10 | 30 | 19 |
| 设计 | 11 | 33 | 21 |
| 验证 | 6 | 18 | 12 |
| 实现 | 8 | 24 | 15 |
| 发布 | 7 | 21 | 14 |
| 观察 | 6 | 18 | 12 |
| 学习 | 6 | 18 | 12 |

### 评分函数验证

```python
# 空文档 → 0 分（正确拒绝）
score_stage('discover', '空的') → 0.0/27, pass=False

# 合格报告 → 18 分（通过）
score_stage('discover', 完整发现报告) → 18.0/27, pass=True

# 学习报告 → 17 分（几乎满分）
score_stage('learn', 完整学习报告) → 17.0/18, pass=True
```

---

## 2026-06-26 — SkillOpt 集成

### SkillOpt 是什么

微软的研究项目（[arXiv:2605.23904](https://arxiv.org/abs/2605.23904)），核心思想：

> 把 agent 的 SKILL.md 当作"可训练参数"，用训练神经网络的方式优化它。

训练循环：rollout → 评分 → 反思 → 聚合 → 选择 → 更新 skill → 验证

基准数据：在 GPT-5.5 上，优化后的 skill 比无 skill 提升 +23.5 分。

### 集成方式

```
yishuship pm_scorer.py（63 个评分函数）
    ↓ 作为 SkillOpt 的 scoring backend
SkillOpt 训练循环
    ├── Rollout: target model 用当前 skill 产出 PM 文档
    ├── Score: pm_scorer 评分（189 分满分）
    ├── Reflect: optimizer 分析低分产出
    ├── Update: 修改 skill 文档
    └── Gate: 验证集得分提升才接受
    ↓
best_skill.md（优化后的 skill 文档）
```

### 创建的 SkillOpt 组件

| 文件 | 作用 |
|------|------|
| `adapter.py` | EnvAdapter 子类，连接 SkillOpt 训练循环 |
| `dataloader.py` | 加载 PM 场景数据集（12 train / 4 val / 4 test） |
| `rollout.py` | 运行 target model + pm_scorer 评分 |
| `initial.md` | seed skill 文档（被 SkillOpt 优化的起点） |
| `analyst_error.md` | 失败分析 prompt（指导 optimizer 如何改进） |
| `analyst_success.md` | 成功分析 prompt（提取可复用模式） |
| `default.yaml` | 训练配置（3 epochs, batch_size=4, lr=3） |

### 验证结果

```
✅ Adapter 实例化成功
✅ Dataloader: train=12, val=4, test=4
✅ 8 个 PM 阶段全部覆盖
✅ pm_scorer 评分函数正常
```

---

## 架构总览

```
yishuship/
├── .claude-plugin/           Claude Code 插件元数据 + marketplace.json
├── skills/                   13 个 skill（pm-eval 已移到 benchmarks）
│   ├── use-yishuship/        路由脑（入口）
│   ├── pm-intake/            PM 全流程（130 行，Step 0-5 顺序执行）
│   ├── design/               对抗式设计（原版 Ship）
│   ├── dev/                  实现（原版 Ship）
│   ├── e2e/                  E2E 测试固化
│   ├── review/               bug 审查
│   ├── qa/                   独立 QA
│   ├── refactor/             四镜头扫描
│   ├── handoff/              PR + CI fix loop
│   ├── auto/                 全流程状态机
│   ├── arch-design/          系统设计
│   ├── visual-design/        DESIGN.md 视觉系统
│   └── write-docs/           文档生成
├── benchmarks/               SkillOpt 训练数据 + 评分框架
│   ├── pm_scorer.py          63 个评分函数（已验证 25/27）
│   ├── pm-eval-spec/         评分标准文档（从 skills/ 移出）
│   ├── skillopt-env/         SkillOpt benchmark 适配器
│   └── yishuship_split/      train/val/test 数据
├── hooks/
│   ├── hooks.json            4 个 hook（phase-guardrail + pm-gate + stop-gate + pm-verify）
│   └── ...
├── scripts/
│   ├── pm-gate.sh            PreToolUse: 工程层调用前检查 PM 产出物
│   ├── pm-verify.sh          Stop: PM 产出未完成时阻止退出
│   ├── pm-init.sh            初始化 PM 工作流
│   ├── phase-guardrail.sh    PreToolUse: QA/Review 独立性保护
│   ├── stop-gate.sh          Stop: 任务未完成阻止退出
│   └── ...
├── AGENTS.md
├── README.md
└── DEVLOG.md
```

---

## 2026-06-26 — 强制执行机制 + 端到端验证

### 问题发现

用户指出：skill 文档只是"建议"，agent 可以无视。需要强制执行机制。

同时发现 pm-eval（评分标准）不应该放在 skills/ 里——它是 SkillOpt 的损失函数，不是 agent 用的 skill。这是一个结构性错误。

### 修复

1. **pm-intake 重写**：从 387 行精简到 130 行，增加明确的 Step 0-5 顺序执行流程
   - Step 0: 初始化（创建 pm-state.yaml + 任务目录）
   - Step 1: 发现 → 写 01-discovery.md
   - Step 2: 定义 → 写 02-definition.md
   - Step 3: 设计 → 写 03-design.md
   - Step 4: 验证 → 写 04-validation.md
   - Step 5: 交接
   - 每步必须写文件 + 更新状态，不写不算完成

2. **PM 强制 hooks**：
   - `pm-gate.sh`：PreToolUse hook，没有 discovery.md 就不能调 /yishuship:design
   - `pm-verify.sh`：Stop hook，PM 产出没写完就阻止会话退出

3. **pm-init.sh**：独立初始化脚本，一键创建 PM 工作流

4. **pm-eval 移到 benchmarks/**：从 skills/ 移到 benchmarks/pm-eval-spec/

5. **pm_scorer 正则修复**：
   - score_existing_solution: 扩展关键词（现状/聊天式/手动）
   - score_problem_evidence: 支持无协议前缀的 URL
   - _count_table_rows: 从正则改为逐行扫描，修复加粗表头匹配

### 端到端测试

用真实 agent 执行 pm-intake Step 1（发现阶段），场景：yishuship 项目本身需要端到端测试流程。

**结果**：
- agent 成功读取 skill 并按模板执行
- 产出 01-discovery.md 质量 25/27（合格线 17）
- pm-state.yaml 自动更新为 phase: define
- 竞品扫描覆盖 4 个真实竞品（heliohq/ship、Cursor Plan Mode、GitHub Copilot Workspace、OpenAI Symphony）

**结论**：pm-intake 可以被 agent 执行，产出质量达标。

### 插件安装

- 创建 marketplace.json 支持本地安装
- yishuship@yishuship v0.1.0 已安装并启用
- 旧 ship@heliohq 插件已删除
- 旧 ~/.claude/skills/ship/ 目录已清理

---

## 下一步

- [ ] 运行 SkillOpt 训练循环，优化 seed skill
- [ ] 补全 PM 场景数据集（当前 12 个，目标 50+）
- [ ] 用 yishuship 完整流程做一个真实产品功能（端到端验证 PM→工程全流程）
- [ ] 集成 SkillOpt-Sleep（夜间自动优化）
- [ ] 补全 pm-intake Step 2-5 的端到端测试
