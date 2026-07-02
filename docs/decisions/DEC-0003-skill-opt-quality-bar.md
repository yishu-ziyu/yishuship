# DEC-0003: yishuship 使用 Microsoft SkillOpt 训练 PM skill

> 日期: 2026-07-01
> 状态: 已接受

## 背景

yishuship 是插件，不是单个 skill。插件承载状态机、hooks、脚本、共享产物和多个阶段 skill；SkillOpt 训练的是可复用自然语言 skill artifact。

因此本轮不把整个插件交给优化器改写，而是先把 PM seed skill 作为可训练状态：target model 用 seed skill 生成 PM 阶段产出，`pm_scorer` 打分，optimizer 根据失败/成功轨迹提出 patch，只有验证集分数提升才接受候选 skill。

## 决策

采用 Microsoft SkillOpt 的训练循环，而不是本地静态文档评分器。

训练单元：

- 初始 skill: `benchmarks/skillopt-env/initial.md`
- 数据集: `benchmarks/yishuship_split/{train,val,test}/`
- 评分器: `benchmarks/pm_scorer.py`
- SkillOpt env: `benchmarks/skillopt-env/`
- 同步脚本: `scripts/sync-skillopt-env.sh`

验证门使用 `gate_metric: mixed`、`gate_mixed_weight: 0.5`。当前 seed skill 在小 test split 上 hard pass rate 已接近饱和，mixed gate 可以让 soft score 继续约束细粒度质量。

## 质量门

一个训练产物只有满足以下条件，才可以进入 yishuship 正式 skill：

1. baseline eval 和 train 均能在 SkillOpt 中跑通。
2. 验证集 gate 接受候选，不能只看训练集提升。
3. `best_skill.md` 相比 seed skill 的验证集 hard 或 mixed score 提升至少 5%。
4. test split 没有明显回退；若 test 变差，必须人工解释并扩大数据集后重训。
5. 人工审查确认没有把单个 benchmark 场景硬编码进 skill。
6. 合并到 `skills/pm-intake/SKILL.md` 前，必须通过 yishuship 本地 skill 校验和 PM scorer 测试。

## 为什么不用本地静态 scorer

本地文档评分只能做 lint，不能证明 skill 真的让模型产出更好。SkillOpt 的价值在于把 skill 放进任务轨迹里训练，并用 held-out validation gate 约束更新是否接受。

静态 skill 文档原则仍然有用：predictability、completion criterion、progressive disclosure、single source of truth、leading words、pruning。但它们是写 seed skill 和审查 `best_skill.md` 的标准，不叫 OPT，也不替代 SkillOpt。

## 接入要求

`scripts/sync-skillopt-env.sh` 必须把以下内容同步到 SkillOpt checkout：

- `skillopt/envs/yishuship/{adapter.py,dataloader.py,rollout.py,pm_scorer.py}`
- `skillopt/envs/yishuship/prompts/{analyst_error.md,analyst_success.md}`
- `skillopt/envs/yishuship/skills/initial.md`
- `configs/yishuship/default.yaml`
- `data/yishuship_split/`

脚本还必须把 `yishuship` 注册进 `scripts/train.py` 和 `scripts/eval_only.py` 的 env registry，否则 CLI 无法发现这个 benchmark。

## 下一步

1. 跑 baseline eval，记录 seed skill 分数。
2. 跑 3 epoch 小训练，检查 `best_skill.md`、history 和 gate 日志。
3. 审查 accepted edits 是否泛化。
4. 把通过审查的改动反向合并到 `skills/pm-intake/SKILL.md` 或更新 seed skill。
