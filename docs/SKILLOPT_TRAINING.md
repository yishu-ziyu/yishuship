# SkillOpt 训练循环启动指南

> 状态：yishuship benchmark env、数据、评分器和同步脚本已就绪。

## SkillOpt 在这里训练什么

SkillOpt 不是插件运行时，也不是静态 lint。它把一个自然语言 skill 文档当成可训练状态：target model 用该 skill 完成任务，rollout 产出轨迹，`pm_scorer` 打分，optimizer 根据轨迹生成 bounded edits，候选 skill 只有在验证集 gate 上提升才被接受。

yishuship 当前训练范围是 PM seed skill + Matt flow 路由矩阵：

| 部件 | 位置 |
|------|------|
| 初始 skill | `benchmarks/skillopt-env/initial.md` |
| SkillOpt env | `benchmarks/skillopt-env/` |
| 数据集 | `benchmarks/yishuship_split/{train,val,test}/` |
| 评分器 | `benchmarks/pm_scorer.py`, `benchmarks/matt_flow_scorer.py` |
| 同步脚本 | `scripts/sync-skillopt-env.sh` |

默认配置使用 mixed validation gate：hard pass rate 和 soft score 各占 50%。原因是当前 seed skill 在小 test split 上可能已经 hard 饱和，单看 hard gate 会让训练没有可接受的提升空间。

Matt flow 样本使用 `expected_flow.required` 做硬门。缺少任意 required 节点即 hard fail。当前节点包括：`alignment`、`shared_language`、`prd_test_seams`、`vertical_slices`、`tdd`、`two_axis_review`、`handoff`、`prototype`、`diagnosis`、`deep_module`。

## 数据规模

| Split | 数量 | 用途 |
|-------|------|------|
| train | 22 | rollout + reflect + patch |
| val | 7 | validation gate / selection |
| test | 7 | held-out test |

## 安装到 SkillOpt checkout

```bash
git clone https://github.com/microsoft/SkillOpt.git /tmp/SkillOpt
cd /Users/mahaoxuan/Developer/yishuship
scripts/sync-skillopt-env.sh /tmp/SkillOpt
```

同步脚本会复制 env、prompts、seed skill、`pm_scorer`、数据和 config，并把 `yishuship` 注册进 SkillOpt 的 `scripts/train.py` / `scripts/eval_only.py`。

## 本地结构检查

```bash
cd /tmp/SkillOpt
python3 -m py_compile skillopt/envs/yishuship/*.py
python3 - <<'PY'
from skillopt.config import flatten_config, load_config
from scripts import train

cfg = flatten_config(load_config("configs/yishuship/default.yaml"))
adapter = train.get_adapter(cfg)
adapter.setup(cfg)
print(type(adapter).__name__)
print(len(adapter.dataloader.train_items), len(adapter.dataloader.val_items), len(adapter.dataloader.test_items))
print(adapter.get_task_types())
PY
```

## 评估基线

需要配置 SkillOpt 支持的 target backend，例如 OpenAI/Azure/Claude/Qwen/MiniMax chat backend。

```bash
cd /tmp/SkillOpt
python scripts/eval_only.py \
  --config configs/yishuship/default.yaml \
  --skill skillopt/envs/yishuship/skills/initial.md \
  --split test \
  --out_root outputs/yishuship/eval_seed_$(date +%Y%m%d_%H%M%S)
```

## 训练

```bash
cd /tmp/SkillOpt
python scripts/train.py \
  --config configs/yishuship/default.yaml \
  --cfg-options env.out_root=outputs/yishuship/train_$(date +%Y%m%d_%H%M%S)
```

关键输出：

- `outputs/.../history.json`
- `outputs/.../best_skill.md`
- `outputs/.../selection_eval_*`
- `outputs/.../test_eval_*`
- `outputs/.../steps/*/rollout/predictions/<id>/conversation.json`

## 推荐后端示例

### MiniMax chat

```bash
export MINIMAX_API_KEY="..."
cd /tmp/SkillOpt
python scripts/train.py \
  --config configs/yishuship/default.yaml \
  --target_backend minimax_chat \
  --optimizer_backend minimax_chat \
  --minimax_model MiniMax-M2.7
```

### Claude chat

```bash
export ANTHROPIC_API_KEY="..."
cd /tmp/SkillOpt
python scripts/train.py \
  --config configs/yishuship/default.yaml \
  --target_backend claude_chat \
  --optimizer_backend claude_chat
```

## 验收标准

- baseline eval 能跑通，并写出 `rollouts.json` 和 per-task `conversation.json`。
- train 至少跑完 1 个 epoch，不出现 env registry、prompt schema、scorer import 错误。
- validation gate 接受的 `best_skill.md` 相比 seed skill 提升至少 5%。
- test split 没有明显回退。
- 人工审查确认 `best_skill.md` 没有硬编码单个场景。

## 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `Unknown environment 'yishuship'` | env 未注册 | 重新运行 `scripts/sync-skillopt-env.sh /tmp/SkillOpt` |
| `ModuleNotFoundError: pm_scorer` | env 内缺 PM 评分器 | 确认 `skillopt/envs/yishuship/pm_scorer.py` 存在 |
| `matt_flow_scorer unavailable` | env 内缺 Matt flow 评分器 | 重新运行同步脚本，确认 `skillopt/envs/yishuship/matt_flow_scorer.py` 存在 |
| reflect 没有 patches | 没有 per-task trajectory | 检查 `rollout/predictions/<id>/conversation.json` |
| analyst 输出无法解析 | prompt schema 错 | 使用 `benchmarks/skillopt-env/prompts` 同步后的 JSON object schema |
| 训练 OOM 或过慢 | batch / token 太大 | 下调 `train.batch_size`、`gradient.minibatch_size`、`env.max_completion_tokens` |
