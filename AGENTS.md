# AGENTS.md

yishuship 是 Ship 增强版：PM 层 + 对抗式设计 + 工程执行一体化。

## 仓库结构

```
skills/
  use-yishuship/    路由脑（入口）
  matt/             Matt Pocock upstream skill 运行时适配器
  pm-intake/        产品生命周期入口：类型判断→战略→调研→规格→工程交接
  design/           对抗式设计（host + peer）
  dev/              实现（host + peer 交叉验证）
  e2e/              E2E 测试固化
  review/           bug 审查
  qa/               独立 QA
  refactor/         四镜头扫描
  handoff/          PR + CI fix loop
  arch-design/      系统设计
  visual-design/    DESIGN.md 视觉系统
  write-docs/       文档生成
  .shared/          共享参考（runtime-resolution, product-lifecycle-21, report-card, startup, cleanup）
hooks/              质量门 hooks
scripts/            状态机脚本
docs/               设计文档
vendor/mattpocock-skills/  Matt Pocock Skills For Real Engineers 原始标准层（MIT）
```

## 开发命令

```bash
# 验证 skill 文件
find skills -name "SKILL.md" | wc -l  # 应为 14

# 检查残留的 ship: 引用
grep -r "ship:" skills --include="*.md" | grep -v "yishuship"

# 测试 hooks
echo '{"cwd":"/path","tool_name":"Edit"}' | bash scripts/phase-guardrail.sh
```

## 约定

- 所有 skill 用 `/yishuship:` 前缀
- 产出物放 `.ship/tasks/<task_id>/`
- 决策沉淀到 `docs/decisions/DEC-NNNN.md`
- 非平凡工程流程遵循 `skills/.shared/matt-pocock-standard.md`，并按 phase 读取对应的 `vendor/mattpocock-skills/**/SKILL.md`
- Conventional Commits: `feat(pm):`, `fix(skill):`, `docs(readme):`
