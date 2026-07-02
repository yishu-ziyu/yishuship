# DEC-0002: yishuship 的「超级个体」质量标准

> 日期: 2026-07-01
> 状态: 已接受

## 背景

yishuship 的目标不是“很多命令的集合”，而是一个能把 idea 变成可交付结果的产品交付角色：理解意图、定义问题、研究方案、做产品决策、执行工程、验证质量、交付并沉淀学习。

因此评价标准必须从结果链条反推：

想要什么 → 定义问题 → 给出适合方案 → 产生实际效果 → 带来后续效应 → 形成满足与复用。

## 评分标准（10 分）

| 维度 | 分值 | 通过标准 |
|------|------|----------|
| 意图识别与路由 | 1.0 | 能区分聊天、调研、挑战前提、直接执行、全流程交付；不要求用户总是显式选命令。 |
| 产品定义能力 | 1.5 | 新 idea 必须先完成产品类型、用户、场景、问题、非目标、验收标准。 |
| 研究与决策质量 | 1.0 | 对关键假设、竞品、现状、技术选型有证据；能挑战错误前提。 |
| 工程执行编排 | 1.5 | 设计、实现、E2E、review、QA、refactor、handoff 有状态机，能暂停恢复。 |
| 验证闭环 | 1.5 | 每个阶段有磁盘产物和自动校验；不能只靠模型口头声明完成。 |
| 交付能力 | 1.0 | 能形成 PR/CI/发布交接，并处理失败循环。 |
| 自我改进 | 1.0 | 有评分器、训练数据、SkillOpt 或等价评估循环，低分能反向修改 skill。 |
| 可发现性与可靠安装 | 0.75 | 插件、skill、命令、hook 在 Codex/Claude 环境中可发现且一致。 |
| 协作人格与判断 | 0.75 | 能像工程负责人一样推进，也能像人一样讨论前提、价值和取舍。 |

## 为什么之前「idea → deliverable 超级个体」只给 4.5/10

当时的判断不是因为 skill 数量少，而是因为主链条断在最关键的位置：

1. `/yishuship:auto` 的脚本第一阶段直接进入 `design`，绕过了 `pm-intake`。这意味着“从 idea 到产品定义”的主承诺没有进入自动交付路径。
2. 自动模板仍调用 `Skill('ship:*')` 和 `/ship:auto`，PM Gate 难以可靠识别真实的 yishuship 工程阶段。
3. `pm-init.sh` 仍创建旧版 `pm/` 和 `discover` 状态，而 V2 skill 要求 `product/`、`delivery/`、`control/` 等目录。
4. PM Gate 声称要求完整 handoff，但实际只检查部分 product 文件，没有检查 `delivery/design-spec.md` 和 `plan/spec.md`。
5. 多个 SKILL.md frontmatter 带 `version:`，不符合 Codex skill 校验规范。
6. 普通阶段 retry 计数没有持久化，`complete` 独立调用后无法稳定升级为 blocked/escalate。
7. README 宣称存在 `/yishuship:pm-eval` 命令，但实际评分器是 `benchmarks/pm_scorer.py`。

这些问题让它更像“强工程流水线 + 一个 PM skill”，还不是稳定的“超级个体”。

## 本次反向塑造方案

本次修复把目标定义为：`/yishuship:auto` 必须能从原始 idea 开始，先产生产品生命周期 handoff，再进入工程状态机。

因此采取以下约束：

1. `auto-orchestrate.sh init` 的第一阶段改为 `pm_intake`。
2. `pm_intake` 成功必须通过脚本校验，至少包含完整 `product/00` 到 `product/09`、`control/lifecycle-checklist.yaml`、`delivery/design-spec.md`、`plan/spec.md`。
3. 自动模板全部使用 `yishuship:*`，不再遗留 `ship:*`。
4. `pm-intake` 在 `auto` 场景下复用已有 `task_id/task_dir`，避免产品文件和工程文件分裂。
5. `pm-init.sh` 改为初始化 V2 目录和 `product-type` 状态。
6. PM Gate 同时检查 product handoff、delivery handoff 和工程 spec。
7. retry 计数写回状态文件，阶段失败能形成真实的重试和升级。
8. 评分标准写入本决策文档，后续低分必须回到这里反向改 skill、脚本或测试。

## 重新评估条件

- `/yishuship:auto` 的 PM 阶段在真实项目中频繁产出空泛 PRD。
- E2E/QA 阶段无法覆盖真实用户体验。
- SkillOpt 训练循环不能证明 PM 文档质量提升。
- Codex 或 Claude 插件规范变化导致 skill/hook 发现机制失效。
