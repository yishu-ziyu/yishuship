# yishuship 决策画布设计

日期：2026-07-13
状态：已完成产品讨论，待用户审阅书面规格

## 决定

yishuship 增加原生“决策画布”，把项目事实、用户意图、Agent 提案、已批准决定、执行状态与验证证据放进同一个可编辑空间。

画布不是项目状态看板，也不是 Canvasight 的移植版。它的唯一任务是帮助用户决定下一步，并把已确认的决定安全地交给 Codex、Claude Code 或其他 Agent 执行。

第一版采用本地决策服务：浏览器通过 HTTP 提交命令、通过 SSE 接收更新；Agent 通过统一的 MCP 工具读写同一协议，hooks 只负责在安全边界提醒待处理决定；稳定语义写入 `.ship`，界面坐标保存在仓库外的本地缓存。

## 目标

- 从真实仓库事实生成项目图，而不是展示 yishuship 阶段名称。
- 同时支持 Agent 提案和用户提案。
- 用户批准前不产生开发指令。
- 用户批准后进入持久执行队列，不强行打断 Agent 当前原子动作。
- Codex、Claude Code 和浏览器看到同一份决定与执行状态。
- Agent 执行后必须回填来源、结果和验证证据，才能完成闭环。

## 非目标

- 不安装或依赖 Canvasight。
- 不把 React、XYFlow、MCP daemon 等 Canvasight 实现整体搬入 yishuship。
- 第一版不做云同步、多人实时协作、移动端编辑或跨设备账户系统。
- 第一版不自动打断正在运行的 Agent。
- 画布不取代 Git、测试、代码或现有 `.ship/tasks/` 产物的事实权威。
- 不允许拖动节点、改变颜色等纯视觉动作直接触发开发。

## 权威边界

| 内容 | 权威来源 | 画布权限 |
|---|---|---|
| 目标、约束、优先级、取舍 | 用户确认的决定 | 用户可批准、修改、否决 |
| 代码与提交事实 | Git 和工作树 | 只读投影 |
| 正确性与完成证据 | 测试、Review、QA、E2E、Handoff | 只读投影；Agent 可追加新证据 |
| 工作流状态 | `.ship/tasks/*/control/run_state.yaml` 等现有产物 | 只读投影；通过现有 yishuship 流程更新 |
| 解释、风险、选项、建议 | Agent | 明确标记为提案，不冒充事实或决定 |
| 节点位置、缩放、面板状态 | 用户本地界面偏好 | 本地可改，不进入 Git |

## 交互模型

主状态链：

```text
事实 → 提案 → 用户批准 → 等待队列 → Agent 领取 → 执行 → 证据回填
```

### 事实

事实节点来自代码、Git、测试和 `.ship`。用户可以查看来源和要求 Agent 解释，但不能在画布里直接改写事实。事实变化必须来自原始来源。

### 提案

用户和 Agent 都能创建提案。提案至少包含：建议动作、理由、依据、预期影响、替代方案、风险和基于哪个项目 revision 生成。

用户可以：

- 修改提案；
- 要求替代方案；
- 否决；
- 批准并入队。

### 决定与执行

批准后的提案成为带 revision 的不可静默改写决定。Agent 只在完成当前原子动作后领取队列中的下一项。

执行中的新用户意见不会强行终止当前动作，而是生成新提案。若新决定取代旧决定，必须以 `supersedes` 关系追加事件，不能重写历史。

完成必须附带验证证据。没有可检查证据的执行只能停在 `reported` 或 `needs_verification`，不能进入 `completed`。

## 画布内容

主画布只出现真实项目对象：

- 产品目标；
- 用户问题或业务结果；
- 能力、功能、模块和任务；
- 依赖关系；
- 证据；
- 风险与未决问题；
- 提案、决定和执行结果。

yishuship 的 `design`、`dev`、`review`、`qa` 等阶段只作为节点元数据或过滤条件，不作为主图节点。

选择节点时，右侧检查器显示：当前含义、来源、影响、相关决定和下一步。提案节点额外显示“修改”“要求替代方案”“否决”“批准并入队”。事实节点只显示“解释依据”和“查看来源”。

## 架构

```text
浏览器决策画布
      ↕ HTTP commands + SSE events
yishuship 本地决策服务
      ↕ MCP tools + boundary hooks
Codex · Claude Code · 其他 Agent
      ↕
Git · tests · .ship/tasks
```

### 项目事实投影器

读取现有仓库状态并生成标准项目图。第一版读取：

- 当前 Git 分支、HEAD、工作树变化；
- `.ship/pm-state.yaml`；
- `.ship/tasks/*/control/run_state.yaml`；
- 当前任务的产品、规格、Review、QA、E2E 和 Handoff 产物；
- repo 已声明的测试命令和最近可验证结果。

投影器只保存来源引用、摘要和摘要生成时的 commit/revision，不复制完整源码成为第二真源。

### 本地决策服务

服务绑定 `127.0.0.1`，负责：

- 读取并验证事件；
- 生成当前画布状态；
- 管理 revision；
- 将更新推送到浏览器；
- 向 Agent 暴露统一命令；
- 在重启后从 `.ship` 恢复。

第一版不引入数据库。项目规模允许每次启动重放事件日志；事件量达到实际性能瓶颈后再增加快照。

### Agent adapter

各宿主只做协议适配，不复制决策逻辑。最小能力为：

- `get_project_state`
- `submit_proposal`
- `claim_next_decision`
- `report_execution`

批准、修改和否决提案只通过用户界面命令完成，不作为 Agent MCP 工具暴露。Codex 与 Claude Code 使用同一组 Agent 语义；hooks 在会话开始、阶段切换和停止边界提示未处理决定。需要持续会话时可以增加 stream adapter，但第一版不能依赖“中途向模型强塞消息”。

用户从 Codex 或 Claude Code 输入 `/yishuship:canvas` 时，adapter 只负责启动或连接本地服务并打开项目画布。画布仍是批准决定的唯一界面。

## 持久化与并发

项目级语义事件追加到：

```text
.ship/decision-canvas/events.jsonl
```

事件至少包含：

```text
event_id
project_revision
base_revision
actor
type
proposal_or_decision_id
task_id
payload
evidence_refs
created_at
```

首批事件类型：

```text
proposal.created
proposal.revised
proposal.rejected
decision.approved
decision.superseded
execution.claimed
execution.reported
execution.interrupted
execution.completed
execution.failed
```

本地服务是每个项目的单一写入者，以项目锁阻止第二个服务实例同时写日志。事件使用原子追加；命令携带 `base_revision` 做乐观并发。版本过期时拒绝写入并返回变化摘要，用户必须基于新事实重新确认。

节点位置、缩放、面板开关保存在仓库外的本地缓存，例如：

```text
~/.cache/yishuship/<repo-id>/decision-canvas-view.json
```

事件日志进入 Git；本地视图状态不进入 Git。队列由事件重放得到，不维护第二份可漂移的 queue 文件。

## 多端行为

### Agent 在线

Agent 完成当前原子动作后调用 `claim_next_decision`。若有已批准决定，则领取并记录 `execution.claimed`；浏览器立即显示领取者和状态。

### Agent 离线

决定保留在事件日志中。Agent 下次进入项目时，SessionStart/hook 或 MCP 状态读取会提示待处理决定。离线不会丢失，也不会假装已送达。

### 多个 Agent 同时在线

领取操作按 revision 原子提交。同一决定只能有一个 active claim。其他 Agent 收到已被领取的明确结果，不得重复执行。

## 失败处理

- **服务断开**：浏览器切换只读并显示断开状态；不接受看似成功的本地修改。
- **服务重启**：重放最后一条合法事件以前的日志，恢复画布和队列。
- **日志损坏**：停在最后合法 revision，报告损坏行；不跳过并继续写。
- **版本过期**：拒绝批准或修改，展示事实变化，要求重新确认。
- **Agent 崩溃**：记录 `execution.interrupted`。不自动重新执行，避免重复产生部分副作用。
- **证据缺失**：拒绝 `execution.completed`，保留为待验证。
- **来源消失**：事实节点标记 `source_missing`，不把旧摘要继续显示为当前事实。

## 本地安全

- 服务只监听 loopback，不默认开放局域网。
- 每次启动生成本地会话 token，浏览器与 adapter 必须携带。
- adapter 只能操作明确授权的项目根目录。
- 默认只投影路径、摘要和必要证据，不把 secret 文件内容写入事件日志。
- 所有执行仍受 Codex/Claude Code 自己的权限与 yishuship gates 约束；画布批准不是绕过权限的通行证。

## 第一版验收

必须用一个真实 yishuship 项目完成以下验证：

1. 从 Git、`.ship` 和测试证据生成真实项目图，主节点不是阶段名称。
2. Agent 创建提案后，浏览器无需刷新即可看到。
3. 用户修改并批准后，Codex 与 Claude Code 读取到相同决定和 revision。
4. Agent 正在执行原子动作时不会被打断；动作结束后能领取新决定。
5. 两个 Agent 同时领取时只有一个成功。
6. 使用旧 revision 批准会被拒绝，并展示变化原因。
7. 杀掉并重启本地服务后，提案、决定和队列完整恢复。
8. Agent 执行中断后不会自动重跑。
9. 没有验证证据时不能标记完成。
10. 整个功能不依赖 Canvasight 或另一个需用户安装的插件。

验证层次：

- 事件 reducer 与 revision：单元测试；
- 服务重启、并发领取和日志恢复：集成测试；
- Codex/Claude Code adapter：协议契约测试；
- 浏览器提案到完成闭环：端到端测试；
- 真实项目内容是否有决策价值：人工 QA。

## 第一版交付边界

第一版交付五件事：

1. 项目事实投影；
2. 本地决策服务；
3. 浏览器决策画布；
4. Codex 与 Claude Code adapter；
5. 提案、批准、领取、执行和证据回填闭环。

云同步、多人权限、远程协作、移动端和复杂模板库在出现真实需求后再设计。

## 与现有 yishuship 的关系

这不是新增一个与 yishuship 平行的工作流。它是现有产品层和工程层的决策界面：

```text
pm-intake / design / dev / review / qa / handoff
                     ↕
                  决策画布
                     ↕
           用户判断与 Agent 执行
```

现有技能、hooks、gates 和 `.ship/tasks/` 保持权威。画布只把它们投影成可理解、可决策、可执行的共同界面。
