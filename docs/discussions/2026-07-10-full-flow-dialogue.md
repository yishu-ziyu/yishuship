# yishuship 全流程共读 · 对话记忆

> Living document.
> One segment at a time.
> Update after every segment is closed.

## Meta

| Field | Value |
|-------|-------|
| Started | 2026-07-10 |
| Goal | 把 yishuship 全流程搞明白，并形成可执行判断 |
| Method | 分段讨论 + 认知负荷控制 + 磁盘记忆 |
| Source of truth | 本文件 + 仓库 skill/脚本实现 |

## Collaboration protocol (agreed)

1. One segment per turn unless user asks for more.
2. Each segment ends with: key claim / open question / next segment name.
3. User can say: `下一段` / `重讲` / `卡住` / `写入：...` / `改结论：...`
4. Long waterfall answers are a process bug, not a feature.
5. Naked next-steps forbidden: always effect + presentation + preview when recommending action.
6. **X / web sources**: when research cites X, reply MUST include clickable link to the original post AND a short explanation of what that post claims (not bare name-drop).
7. **Provenance + pressure**: prefer source tracing (user's X/Git refs, DEVLOG, upstream repos) over vibes; cold critique of weak claims; accumulate sources in this doc's Provenance section.
8. **Tone**: calm-cruel useful pressure - challenge mush, not perform agreement.

## Cognitive load contract (why we segment)

Working memory is limited.
Flooding it with a full pipeline dump raises **extraneous load** and blocks **germane load** (schema building).
Result: loss, bias, and wrong judgments - even when the content is "correct".

Three loads (Sweller et al.):

| Load | Meaning | Our rule |
|------|---------|----------|
| Intrinsic | 材料本身多复杂 | 一次只攻一个子系统 |
| Extraneous | 呈现方式制造的额外负担 | 禁瀑布；分段；先结论 |
| Germane | 真正用于形成图式的努力 | 每段只留 1-3 个可复用结论 |

X-side signal (paraphrase, not gospel):

- More information can make decisions worse under overload.
- When environment complexity cannot be reduced, people reduce strategy complexity (shallow thinking).
- Chunking: roughly few chunks at a time; content-aware cuts beat firehose.

## Map of segments (table of contents)

| # | Segment | Status | Closed claim |
|---|---------|--------|--------------|
| 0 | 协作方式 + 认知负荷 | closed | 分段+落盘；禁瀑布 |
| 1 | yishuship 是什么 / 不是什么 | **current** | |
| 2 | 进态 Activation + State Sense | pending | |
| 3 | 产品层 pm-intake 骨架 | pending | |
| 4 | 产品层 21 checkpoints 怎么用 | pending | |
| 5 | 工程 design 对抗式 | pending | |
| 6 | 工程 dev 垂直切片 + TDD | pending | |
| 7 | e2e / review / qa 验证三角 | pending | |
| 8 | handoff + auto 状态机 | pending | |
| 9 | 强制力 hooks 与跨宿主缺口 | pending | |
| 10 | 全流程一张因果图 + 你的决策 | pending | |

## Segment log

### Segment 0 - 协作方式 + 认知负荷 (2026-07-10)

**User intent**

流式过长 → 跟不上 → 信息损耗、偏漏、判断错误。
要求：分段讨论 + 具体文档记忆过程。
要求：优先从 X 获得线索，并结合认知负荷理论。

**Agreement**

- 采用分段共读。
- 本文件为过程记忆。
- 每段可讨论后再进下一段。

**Research notes (compact)**

- CLT: intrinsic / extraneous / germane; optimize presentation to free capacity for schema.
- Overload pathology: more raw info can degrade sensemaking.
- Chunking and content-aware segmentation are the practical fix.

**Open**

- User confirmed: start Segment 1 (2026-07-10).

### Segment 1 - yishuship 是什么 / 不是什么 (2026-07-10)

**Claim (one sentence)**

yishuship is a pluggable product-delivery runtime for coding agents - not a chat Agent product, not a prompt pack, not a replacement for writing code.

**Is**

| | |
|--|--|
| Form | Plugin / skill pack + hooks + scripts + `.ship` state |
| Job | Constrain the path from idea → judgment → build → evidence → ship |
| Layers | Product (pm-intake) + Engineering (Ship-style) + Matt standards (vendor) |
| Value unit | Executed constraints on disk, not beautiful SKILL.md text |

**Is not**

| Common confusion | Reality |
|------------------|---------|
| Kimi-like personal Agent | Optional future shell only; core is runtime |
| "Just install and model will always obey" | Needs **tell agent to use yishuship** + enter state |
| Full replacement for human judgment | It forces process; you still decide do/don't and taste |
| Mandatory 21-phase every typo | Checkpoints ≠ always-on heavy auto; L0 bypass exists |
| Pure Ship clone | Ship = eng harness; yishuship adds PM lifecycle + Matt map |

**Causal picture (tiny)**

```text
Coding agent (host)
   + yishuship (constraints + artifacts)
   → delivery that can resume and prove itself
```

Without enter-state, the plugin is dead weight.

**Effect of accepting this definition**

You optimize activation + gates + artifact contracts first; not more skills or a website Agent.

**Presentation (how you verify you "got it")**

You can answer in one line: "It is a delivery OS for coding agents."  
You refuse: "It is my personal chatbot."

**Preview**

Next segment only: how enter + State Sense work (Activation). No pm-intake detail yet.

**User Q (same segment): 为什么是 插件+skills+hooks+scripts+.ship？**

See reply in chat; summary:

| Piece | Why |
|-------|-----|
| Plugin | distribution + one install surface on host agents |
| Skills | human-invokable process modules; model can load on demand |
| Hooks | mechanical force (enter/block/stop) when host supports it |
| Scripts | deterministic logic out of LLM (state machine, gates, hash) |
| `.ship` | durable state outside chat; resume + evidence |

Rejected alternatives: multi-plugin (UX/state split), pure prompts (no teeth), pure monolithic agent app (wrong host for coding delivery).

**Open for user**

- Agree / adjust the one-sentence claim?
- Why-form answered; next: Segment 2 or more on form?

---

## Running decisions

| ID | Decision | Date |
|----|----------|------|
| D1 | 主形态 = 可插拔 Delivery Runtime，不是独立聊天 Agent | 2026-07-10 |
| D2 | 进态主路径 = 被告知用 yishuship + 服从落盘 | 2026-07-10 |
| D3 | 进态后默认 State Sense（现在/缺什么/下一步因果） | 2026-07-10 |
| D4 | 建议必须带 effect + presentation + preview | 2026-07-10 |
| D5 | 长讨论必须分段 + 落盘记忆 | 2026-07-10 |
| D6 | 定义：可插拔交付 Runtime，不是聊天 Agent / 不是纯 prompt 包 | 2026-07-10 |
| D7 | 引用 X 必须附原帖超链 + 内容解释 | 2026-07-10 |
| D8 | 讨论要溯源 + 冷静加压；经验写入 Provenance | 2026-07-10 |

## Provenance map (seed - incomplete)

| Source | What yishuship took | Link / where |
|--------|---------------------|--------------|
| heliohq/ship | Eng harness: adversarial design, phase isolation, evidence, auto state machine | https://github.com/heliohq/ship |
| mattpocock/skills | grill → PRD → vertical slices → TDD → two-axis review | https://github.com/mattpocock/skills |
| microsoft/SkillOpt | Train/eval skill text against scorers | https://github.com/microsoft/SkillOpt |
| Cursor Spec / Lovable / Copilot Workspace / Devin | Competitive scan (PM-ish tooling) - noted in DEVLOG, not forked | DEVLOG 2026-06-26 |
| User X bookmarks | **Not yet indexed in repo** - gap | need user dump or path |

**Pressure note:** Without indexing the original X→Git trail the user used at build time, "溯源" is theater. Next: user points to bookmark list / notes path, or we harvest from chat history later.

## Code already landed (context)

| Matt 1.1.0 sync | DEC-0006 vendor `d574778`; `to-spec`/`to-tickets`/`wayfinder`/`research` |


| Commit | What |
|--------|------|
| d7bf7c7 | Activation bootstrap status/enter |
| 09ac6e4 | State Sense fields on status |
| 2663447 | Router requires causal next step |

## Parking lot (questions for later)

- (empty)
