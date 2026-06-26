# SkillOpt 训练循环启动指南

> 状态：种子 + 数据 + 评分器已就绪，等待用户运行

## 已完成

| 改动 | 位置 |
|------|------|
| pm_scorer 新增 arch-decision 5 维度（15 分） | `benchmarks/pm_scorer.py` |
| pm-intake Step 1.5 架构选型子阶段 | `skills/pm-intake/SKILL.md` v0.4.0 |
| 路由脑加架构选型入口 | `skills/use-yishuship/SKILL.md` v0.2.0 |
| arch-design 入口分流 | `skills/arch-design/SKILL.md` v0.2.0 |
| 种子 skill 包含 arch-decision 阶段说明 | `benchmarks/skillopt-env/initial.md` + `/tmp/skillopt/skillopt/envs/yishuship/skills/initial.md` |
| 训练数据增加 4 个 arch-decision 例子 | `benchmarks/yishuship_split/{train,val,test}/` |

## 数据规模

| Split | 数量 | arch-decision |
|-------|------|---------------|
| train | 16 | 4 |
| val | 5 | 1 |
| test | 5 | 1 |

## 推荐运行命令

### 评估基线（先跑一次看分数）

```bash
cd /tmp/skillopt
python scripts/eval_only.py \
  --config configs/yishuship/default.yaml \
  --skill skillopt/envs/yishuship/skills/initial.md \
  --split_dir /Users/mahaoxuan/Developer/yishuship/benchmarks/yishuship_split \
  --out_root outputs/eval_seed_$(date +%Y%m%d_%H%M%S)
```

### 训练（基线评估后启动）

```bash
cd /tmp/skillopt
python scripts/train.py \
  --config configs/yishuship/default.yaml \
  --split_dir /Users/mahaoxuan/Developer/yishuship/benchmarks/yishuship_split \
  --skill_init /tmp/skillopt/skillopt/envs/yishuship/skills/initial.md
```

## LLM 后端选择

环境变量配置（`/tmp/skillopt/configs/_base_/default.yaml` 默认 Azure OpenAI）：

### 选项 A：Azure OpenAI（默认，需 `AZURE_OPENAI_API_KEY` + endpoint）

```bash
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

### 选项 B：MiniMax M3 via Claude Code CLI（**本机推荐**，已购套餐不计费）

> SkillOpt 自带的 `minimax_chat` 后端走 OpenAI 协议，与本机 MiniMax 的 Anthropic 协议不兼容。最简方案：用 `claude_chat` 后端让本地 `claude` CLI 路由到 MiniMax M3。

```bash
# 1. 确认环境
env | grep ANTHROPIC_AUTH_TOKEN  # 应有 token
env | grep ANTHROPIC_BASE_URL    # 应是 https://api.minimaxi.com/anthropic
which claude                      # 应在 PATH

# 2. 跑基线评估
cd /tmp/skillopt
export OPTIMIZER_BACKEND=claude_chat
export TARGET_BACKEND=claude_chat
export OPTIMIZER_DEPLOYMENT=MiniMax-M3
export TARGET_DEPLOYMENT=MiniMax-M3

python scripts/eval_only.py \
  --config configs/yishuship/default.yaml \
  --skill skillopt/envs/yishuship/skills/initial.md \
  --split_dir /Users/mahaoxuan/Developer/yishuship/benchmarks/yishuship_split \
  --out_root outputs/eval_seed_$(date +%Y%m%d_%H%M%S)
```

跑通后，把 `eval_only` 换成 `python scripts/train.py ...` 跑训练（其他参数不变）。

## 预期成本与时长

- **数据量**：12 train + 4 val（eval-only 不跑 train）
- **每次 rollout**：1 次 LLM 调用（target 模型）输出 PM 文档
- **训练循环**：3 epochs × 16 train / 4 batch_size = 12 步 + 每步 minibatch analyst 调用
- **总 LLM 调用估算**：~50-100 次（target 推理）+ 30-60 次（optimizer 分析）
- **时长**：取决于后端延迟，Azure OpenAI 通常 30-60 分钟；Claude Code CLI 走本机可更快
- **成本估算**：Azure OpenAI GPT-5.5 约 $0.50-$2.00；Claude Sonnet 约 $0.30-$1.00；MiniMax M3 已购套餐不计费

## 评分体系

- 8 个标准阶段 × 各 18-33 分 = 187 分
- 1 个 arch-decision 阶段 × 15 分
- **全流程总分：202 分（189 + 13 = 修正后）**

> 注：原 `pm_scorer.py` 总分 189 (8 阶段)，加 arch-decision 后应为 189 + 15 = 204。但 `score_full_pipeline` 总分算法未更新——本指南**不算**总分，仅按阶段看分数。

## 验收标准

- **基线（seed skill）**：
  - train 阶段 8/9 阶段达标（17/27 discover, 19/30 define 等）
  - arch-decision 新阶段 8/15（10/15 pass threshold 较难达）
- **训练后**：
  - 验证集分数提升 ≥ 5%
  - arch-decision 通过率从 60% → 80%+
  - skill 文件未被破坏，仍可读

## 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: pm_scorer` | yishuship benchmarks 未在 sys.path | `export PYTHONPATH=$PYTHONPATH:/Users/mahaoxuan/Developer/yishuship/benchmarks` |
| Azure auth 失败 | 缺 endpoint / key | 设置 `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` |
| Claude CLI 调用失败 | 未登录 | `claude login` |
| 训练 OOM | batch_size 太大 | `--batch_size 2 --gradient.minibatch_size 2` |
| Skill 优化后变空白 | optimizer 过激修改 | 减小 `optimizer.learning_rate` (默认 3) → 2 |
