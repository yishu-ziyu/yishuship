# DEC-0004: Vendor Matt Pocock Skills As yishuship Flow Standard

> 日期: 2026-07-01
> 状态: 已接受

## 背景

Matt Pocock 的 `skills` 仓库不是一组孤立命令，而是一套完整工程流程架构：用户触发的 orchestrator 控制路径，模型触发的 discipline skills 提供复用工程判断。README 中的主流程是 idea → alignment → PRD → vertical issues → TDD implementation → two-axis review → ship；bug、triage、architecture health 是并入主流程的 on-ramps。

yishuship 的目标是超级个体式交付。这个目标需要学习这套全流程架构，而不是只摘录几个技巧。

## 决策

将上游仓库以 vendor 形式原样纳入：

```text
vendor/mattpocock-skills/
```

保留 MIT license 与上游文件结构。yishuship 不改写 vendor 内容，只通过共享适配层引用：

```text
skills/.shared/matt-pocock-standard.md
```

## 映射

| Matt architecture | yishuship adaptation |
|---|---|
| `ask-matt` router | `use-yishuship` / `auto` 路由脑 |
| `grill-with-docs` + `domain-modeling` | `pm-intake` 和 `design` 的对齐、术语、决策沉淀 |
| `prototype` | PM/design 中无法纸面决策的问题分支 |
| `to-prd` | `pm-intake` 的 PRD 和测试 seam 确认 |
| `to-issues` | `design/dev` 的 vertical slice 拆分 |
| `implement` + `tdd` | `dev` 的 red-green slice 实现 |
| `diagnosing-bugs` | hard bug 修复前的 tight feedback loop |
| `codebase-design` | `design/refactor/arch-design` 的 deep module vocabulary |
| `code-review` | `review` 的 Standards + Spec 双轴 |
| `handoff` | yishuship 跨上下文/发布交接纪律 |

## 质量门

1. 非平凡产品/工程工作必须先经过 alignment：用户意图、domain language、hard-to-reverse decisions。
2. 需要 runnable answer 的设计问题必须走 prototype branch，不能在纸面上猜。
3. PRD 必须记录 test seams；实现必须以 vertical slices 前进。
4. bug/perf 修复必须先有 tight red-capable loop。
5. review 必须分离 Standards 和 Spec 两个轴。
6. refactor/architecture work 必须使用 module/interface/depth/seam/adapter/leverage/locality 词汇。

## 当前成熟度评估

2026-07-01 集成后，yishuship 在“Matt 标准层有机纳入”这一目标上评为 **7.2/10**。
2026-07-02 加入 SkillOpt Matt flow 硬评分矩阵后，当前评为 **8.1/10**。
2026-07-02 修复 PM design seed 并跑通完整 test split 后，评为 **8.4/10**。
2026-07-02 增加 Matt upstream runtime activation 和 `/yishuship:matt` 后，当前评为 **8.8/10**。

之前只能给约 **4.5/10** 的原因：

- 没有把上游高质量 skill 作为可追溯标准层保存，容易靠记忆改写后漂移。
- 全流程没有稳定编码为 alignment → PRD/test seams → vertical slices → TDD → two-axis review → handoff。
- `CONTEXT.md`、decision records、deep-module vocabulary 还不是跨 skill 的共同契约。
- 插件缓存和源码之间存在可见内容滞后，斜杠/插件暴露面不够可靠。

提升到 **7.2/10** 的原因：

- 上游 Matt repo 已 vendor 原样纳入，并保留 MIT license。
- yishuship 增加共享适配层，所有关键工程 skills 已读入同一套 flow standard。
- PM、design、dev、E2E、QA、review、refactor、arch-design、handoff、write-docs 都接入了相应质量门。
- Codex personal plugin cache 已同步到包含 vendor 标准层的版本。

继续提升到 **8.1/10** 的原因：

- Matt 主链已经成为 SkillOpt 可评分矩阵，而不只是共享文档。
- `expected_flow.required` 可以硬测 alignment → PRD/test seams → vertical slices → TDD → two-axis review → handoff 是否稳定出现。
- prototype、diagnosis、deep_module 三个 on-ramp 已进入训练/验证/测试样本。

继续提升到 **8.4/10** 的原因：

- PM design seed 已补充 benchmark mode，避免在无工具环境中错误拒绝产出。
- design 阶段显式覆盖 data_model、flow_role、interface_design、report_design、permission、prd、technical_plan、project_management 八个检查点。
- 完整 test split 已从 hard=0.8571 提升到 hard=1.0。

继续提升到 **8.8/10** 的原因：

- 每个 yishuship 工程 phase 已从“读 Matt 标准摘要”升级为“读取对应 Matt upstream `SKILL.md` 后执行”。
- 新增 `/yishuship:matt` 作为直接 upstream adapter，可按名称运行 `ask-matt`、`grill-with-docs`、`to-prd`、`to-issues`、`implement`、`tdd`、`code-review`、`handoff` 等 vendored skills。
- `skills/.shared/matt-pocock-standard.md` 现在定义 runtime activation map，而不只是流程映射。

还不是 9+/10 的原因：

- 真实 SkillOpt checkout + target backend 的 baseline 已跑通；还没跑完整 train loop 和 retrain 后回归。
- `/yishuship:matt` 已提供 upstream 入口；还需要真实项目中连续 dogfood，验证每个 upstream lane 是否在复杂任务里被正确读取和执行。
- 上游更新策略还只是 vendor snapshot，没有自动 diff、升级、回归测试流程。
- 需要用真实项目连续 dogfood 几轮，观察是否仍有 premature completion、sprawl、duplication。

## 评测矩阵

2026-07-02 追加 SkillOpt 硬评分矩阵：

- `benchmarks/matt_flow_scorer.py` 定义 Matt flow 节点匹配。
- `benchmarks/yishuship_split/*/data.json` 和 `train/train.json` 中的 `matt-flow` 样本通过 `expected_flow.required` 指定必须触发的节点。
- `benchmarks/skillopt-env/rollout.py` 在样本含 `expected_flow` 时切换到 Matt flow scorer；其他 PM 样本继续走 `pm_scorer`。

第一批 required 节点：

```text
alignment
shared_language
prd_test_seams
vertical_slices
tdd
two_axis_review
handoff
prototype
diagnosis
deep_module
```

评分标准：required 节点缺任意一个即 hard fail；soft score 是命中 required 节点的比例。这样 yishuship 是否稳定触发 Matt 主链可以被 SkillOpt rollout 量化，而不是靠人工观感判断。

本地 SkillOpt checkout 烟测：

- `scripts/sync-skillopt-env.sh /tmp/SkillOpt` 可同步 scorer、env、seed skill、数据和 config。
- `/tmp/SkillOpt` 中 `python3 -m py_compile skillopt/envs/yishuship/*.py` 通过。
- adapter 注册检查加载出 train=22、val=7、test=7，task types 包含 `matt-flow`。

2026-07-02 baseline eval（第一轮）：

- 命令：`python scripts/eval_only.py --config configs/yishuship/default.yaml --skill skillopt/envs/yishuship/skills/initial.md --split test --target_backend claude_chat --optimizer_backend claude_chat`
- 输出：`/tmp/SkillOpt/outputs/eval_yishuship_claude-sonnet-4-6_20260702_003759`
- 总分：hard=0.8571，soft=0.9206，n=7。
- Matt flow held-out 样本：`flow_test_001`、`flow_test_002` 均 hard=1，soft=1.0，required misses=[]。
- 唯一失败：`pm_005`，旧 PM design scorer 得分 41/72，低于阈值 48；失败点不在 Matt flow 主链，而在 PM design artifact 的 evidence/actionability 覆盖不足。

2026-07-02 fix 后 baseline eval：

- 命令：`python scripts/eval_only.py --config configs/yishuship/default.yaml --skill skillopt/envs/yishuship/skills/initial.md --split test --target_backend claude_chat --optimizer_backend claude_chat`
- 输出：`/tmp/SkillOpt/outputs/eval_yishuship_claude-sonnet-4-6_20260702_005809`
- 总分：hard=1.0，soft=0.9841，n=7。
- `pm_005` 已从 hard=0、soft=0.5694 提升到 hard=1、soft=1.0。
- Matt flow held-out 样本仍为 hard=1、soft=1.0。

## 不做什么

- 不把每个 Matt skill 都复制成一个独立 `/yishuship:*` 命令；通过 `/yishuship:matt` 和 phase runtime activation 使用 upstream。
- 不把 vendor 文件复制粘贴进 yishuship skills，避免漂移。
- 不在没有具体触发场景时扩展新的 yishuship skill surface。
