// Watches the agent inside Claude Code and writes what it sees into the project,
// so the page beside the terminal follows the agent without the agent writing anything.
//
//   .ship/live/now.json            the state right now: working / asking / stopped / closed
//   .ship/live/<date>-<id>.jsonl   what happened, one step per line (kept out of git)
//   .ship/live/focus.json          the option the user picked (a digit here, or a click on the page)
//   .ship/记录.jsonl               what the user corrected, decided or asked for, one line each;
//                                  a correction carries the rule it suggests (committed, no quotes)
//   .ship/live/原话.jsonl          the user's own words for each of those lines (this machine only)
//
// After every turn a small model reads what the user said this turn (typed at the start or
// while the agent worked) next to the agent's last answer, and suggests a rule for each
// correction; the user confirms it on the page. Confirmed rules go into every turn's context.
//
// Above the input box it says what the user must do now; when the progress file waits on a
// choice it draws one box per option, a digit picks one (the page shows it large) and the
// reply is offered as the input's dim suggestion, taken with Tab.
//
// It only watches: every hook passes the call on unchanged and swallows its own errors.
// Loaded only with CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1 (early access); without it the
// page reads the progress file as before.
import type { Register, RenderElement } from 'claude-code'

type State = 'working' | 'asking' | 'stopped' | 'closed'
type Now = {
  session: string
  state: State
  at: number
  since: number
  did?: string
  question?: string
  reason?: string
  said?: string
}

const LIMIT = 3_500_000 // start a new record file before the 4 MiB read/write cap

function base(path: string): string {
  return path.slice(path.lastIndexOf('/') + 1)
}

function clip(text: string, n: number): string {
  const one = text.replace(/\s+/g, ' ').trim()
  return one.length > n ? `${one.slice(0, n)}…` : one
}

// What a tool call did, in words the user can follow.
function describe(tool: string, input: Record<string, unknown>): string {
  const file = typeof input.file_path === 'string' ? base(input.file_path) : ''
  switch (tool) {
    case 'Bash': return `在运行命令：${clip(String(input.description || input.command || ''), 60)}`
    case 'Edit': case 'MultiEdit': return `在改 ${file}`
    case 'Write': return `在写 ${file}`
    case 'Read': return `在读 ${file}`
    case 'NotebookEdit': return `在改 ${base(String(input.notebook_path ?? ''))}`
    case 'Grep': case 'Glob': return `在找：${clip(String(input.pattern ?? ''), 40)}`
    case 'WebSearch': return `在网上查：${clip(String(input.query ?? ''), 40)}`
    case 'WebFetch': return `在读网页：${clip(String(input.url ?? ''), 60)}`
    case 'Agent': case 'Task': return `派了一个子 Agent：${clip(String(input.description ?? ''), 40)}`
    case 'Skill': return `在用技能：${String(input.skill ?? '')}`
    case 'TodoWrite': return '在更新任务清单'
    case 'AskUserQuestion': return '在等你回答问题'
    default: return `在用 ${tool.replace(/^mcp__/, '').replace(/__/g, ' · ')}`
  }
}

function firstQuestion(input: Record<string, unknown>): string {
  const qs = input.questions
  if (Array.isArray(qs) && qs[0] && typeof qs[0] === 'object') {
    return String((qs[0] as { question?: unknown }).question ?? '')
  }
  return ''
}

// One Claude Code process runs one session, so the state lives at the top of the module.
const S: {
  root?: string // the project holding .ship/ideas; unset → do nothing
  cwd?: string // where the session started: the project whose files the board watches
  session: string
  log: string
  lines: string[]
  part: number
  now?: Now
  writing: Promise<void>
} = { session: '', log: '', lines: [], part: 0, writing: Promise.resolve() }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function save($: any, patch: Partial<Now>, step?: Record<string, unknown>): Promise<void> {
  // The state in memory changes at once, before any write: the band redraws right after a
  // step and must show that step, not the one before (it lagged one step behind when the
  // state changed only after the write queue reached it).
  const at = Date.now()
  const changed = patch.state !== undefined && patch.state !== S.now?.state
  const now: Now = { ...(S.now ?? { session: S.session, state: 'stopped', since: at }), ...patch, session: S.session, at }
  if (changed) now.since = at
  if (patch.state && patch.state !== 'asking') delete now.question
  if (patch.state && patch.state !== 'stopped') delete now.reason
  S.now = now
  if (!S.root) return S.writing
  const r = S.root
  S.writing = S.writing.then(async () => {
    await $.fs.write(`${r}/.ship/live/now.json`, JSON.stringify(now))
    if (step) {
      S.lines.push(JSON.stringify({ at: new Date(at).toISOString(), ...step }))
      let text = S.lines.join('\n') + '\n'
      if (text.length > LIMIT) {
        S.part += 1
        S.lines = S.lines.slice(-1)
        text = S.lines[0] + '\n'
      }
      await $.fs.write(`${r}/.ship/live/${S.log}${S.part ? `-${S.part}` : ''}.jsonl`, text)
    }
  }).catch(() => undefined)
  return S.writing
}


// ---- what the user owes, read from the progress file, for the band above the prompt ----

type Choice = { q: string; opts: { letter: string; text: string; rec: boolean; png?: string; src?: string }[] }
type Pending = { kind: 'choices'; questions: Choice[] } | { kind: 'satisfied'; slice: string } | undefined

function frontMatter(text: string): Record<string, string> {
  const lines = text.split('\n')
  const meta: Record<string, string> = {}
  if (lines[0]?.trim() !== '---') return meta
  for (const line of lines.slice(1)) {
    if (line.trim() === '---') break
    const at = line.indexOf(':')
    if (at >= 0) meta[line.slice(0, at).trim()] = line.slice(at + 1).trim()
  }
  return meta
}

function parseChoices(block: string): Choice[] {
  const out: Choice[] = []
  for (const line of block.split('\n')) {
    const q = line.match(/^\s*([①-⑳])\s+(.+?)\s*$/)
    if (q) { out.push({ q: q[2]!, opts: [] }); continue }
    const o = line.match(/^\s*[├└]─\s*([A-Z])\s+(.+?)\s*$/)
    if (o && out.length) {
      const rec = o[2]!.includes('◀')
      out[out.length - 1]!.opts.push({ letter: o[1]!, text: o[2]!.replace(/◀.*$/, '').trim(), rec })
    }
  }
  return out.filter((c) => c.opts.length)
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function readPending($: any): Promise<Pending> {
  if (!S.root) return undefined
  const dir = `${S.root}/.ship/ideas`
  let best: { updated: string; text: string; meta: Record<string, string> } | undefined
  for (const entry of await $.fs.list(dir)) {
    if (entry.kind !== 'file' || !entry.name.endsWith('.md')) continue
    const text = String(await $.fs.read(`${dir}/${entry.name}`))
    const meta = frontMatter(text)
    if (!meta.waiting) continue
    if (!best || (meta.updated ?? '') > best.updated) best = { updated: meta.updated ?? '', text, meta }
  }
  if (!best) return undefined
  if (best.meta.waiting!.startsWith('满意吗')) return { kind: 'satisfied', slice: best.meta.waiting!.replace(/^满意吗[：:]\s*/, '') }
  const section = best.text.split(/^## 等你决定\n/m)[1]?.split(/^#{1,2} /m)[0] ?? ''
  const questions = parseChoices(section)
  // each option's picture, from ## 看得见 (`### ①` then `- A · … · ../evidence/x.png`)
  const seen = best.text.split(/^## 看得见\n/m)[1]?.split(/^## /m)[0] ?? ''
  let qi = -1
  for (const line of seen.split('\n')) {
    if (/^### [①-⑳]/.test(line)) { qi += 1; continue }
    const m = line.match(/^- ([A-Z])\b.*·\s*\.\.\/(evidence\/\S+?)(#\S*)?\s*$/)
    const opt = m && questions[qi]?.opts.find((o) => o.letter === m[1])
    if (opt) {
      opt.src = m![2] // under .ship/, what the page beside the terminal shows large
      // a small picture in the band: the file itself when it is a PNG, else a PNG of the same name.
      // The terminal reads the file itself: only the path crosses the screen, not the pixels.
      const png = `${S.root}/.ship/${m![2]!.replace(/\.[a-z0-9]+$/i, '.png')}`
      if (await $.fs.exists(png)) opt.png = png
    }
  }
  P.picks = questions.map((q) => (q.opts.find((o) => o.rec) ?? q.opts[0]!).letter)
  return questions.length ? { kind: 'choices', questions } : undefined
}

const P: { pending: Pending; picks: string[] } = { pending: undefined, picks: [] }

// ---- the user's corrections, kept in the project ----

const C: { said: string[]; lastAnswer: string; suggested: number; rulesAt: number; work: Promise<void>; open: string } =
  { said: [], lastAnswer: '', suggested: 0, rulesAt: 0, work: Promise.resolve(), open: '' }

const CLASSIFY = `下面是一位产品负责人在和 AI 编程 Agent 协作时，这一轮说的话（编号在前），以及 Agent 在他说话之前的最后一段话。他不写代码，只管产品。

逐条判断这句话属于哪一类：
- 纠正：指出 Agent 刚才的做法、说法或理解不对，要求以后改（包括委婉的“有点尴尬”“看不清”）；否定或推翻 Agent 刚提出的做法、建议或假设，也算纠正
- 新要求：提出新的期望、方向或参考，但不是说 Agent 做错了
- 决定：对 Agent 的提问作出选择或批准（如“1A 2A”“ok”“可以”）
- 其他：提问、解释、闲聊

一句话可以同时有两类，按最重要的给一个主类；如果同时含纠正，另外标 also_correction=true。
对每条纠正，写一条以后要遵守的规则：完整一句，说清以后应该怎样做，不要复述原话；并判断它适用于“这个项目”还是“所有项目”。
对纠正和决定，before 写 Agent 在这之前的做法或理解，一句话。

只输出 JSON 数组，不要其他文字，格式：
[{"n":1,"kind":"纠正|新要求|决定|其他","also_correction":false,"rule":"","scope":"这个项目|所有项目|","before":""}]`

type Classified = { n?: unknown; kind?: unknown; also_correction?: unknown; rule?: unknown; scope?: unknown; before?: unknown }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function currentIdea($: any): Promise<string> {
  // as the page picks it: the idea waiting on the user first, then the latest update, then the file written last
  const dir = `${S.root}/.ship/ideas`
  let best: { key: string; slug: string } | undefined
  for (const f of await $.fs.list(dir)) {
    if (f.kind !== 'file' || !String(f.name).endsWith('.md')) continue
    const meta = frontMatter(String(await $.fs.read(`${dir}/${f.name}`)))
    if (!['shaping', 'building', 'waiting', 'shipping'].includes(meta.status ?? '')) continue
    const key = `${meta.waiting ? 1 : 0}|${meta.updated ?? ''}|${String(f.mtimeMs).padStart(16, '0')}`
    if (!best || key > best.key) best = { key, slug: String(f.name).replace(/\.md$/, '') }
  }
  return best?.slug ?? ''
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function countSuggested($: any): Promise<number> {
  const text = String(await $.fs.read(`${S.root}/.ship/记录.jsonl`).catch(() => ''))
  return text.split('\n').filter((l) => { try { return JSON.parse(l).status === '建议' } catch { return false } }).length
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function classify($: any, said: string[], before: string): Promise<void> {
  if (!S.root || !said.length) return
  const lines = said.map((t, i) => `${i + 1}. ${t.slice(0, 800)}`).join('\n')
  const r = await $.model.complete({ model: 'sonnet', maxTokens: 2000, timeoutMs: 90_000,
    prompt: `${CLASSIFY}\n\nAgent 上一条（末尾）：${before.slice(-800) || '（无）'}\n\n他说：\n${lines}` })
  if (!r.isAnswered) return
  const found = r.text.match(/\[[\s\S]*\]/)
  let items: Classified[]
  try { items = JSON.parse(found ? found[0] : '[]') } catch { return }
  const at = new Date(await $.clock.now()).toISOString()
  const idea = await currentIdea($)
  let add = ''
  let quotes = ''
  items.forEach((x, i) => {
    const n = Number(x.n) || i + 1
    const text = said[n - 1]
    const corrects = x.kind === '纠正' || x.also_correction === true
    if (!text || (!corrects && x.kind !== '决定' && x.kind !== '新要求')) return
    const id = `${at.replace(/[-:.TZ]/g, '').slice(0, 14)}-${n}`
    add += JSON.stringify({ id, at, idea, kind: corrects ? '纠正' : String(x.kind), before: String(x.before ?? ''),
      rule: corrects ? String(x.rule ?? '') : '', scope: corrects ? (x.scope === '所有项目' ? '所有项目' : '这个项目') : '',
      status: corrects ? '建议' : '' }) + '\n'
    quotes += JSON.stringify({ id, said: text }) + '\n'
  })
  if (!add) return
  const file = `${S.root}/.ship/记录.jsonl`
  const words = `${S.root}/.ship/live/原话.jsonl`
  await $.fs.write(file, String(await $.fs.read(file).catch(() => '')) + add)
  await $.fs.write(words, String(await $.fs.read(words).catch(() => '')) + quotes)
  C.suggested = await countSuggested($)
  $.ui.invalidate('ui.render')
}

type Job = { at: string; said: string[]; before: string }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function jobs($: any): Promise<Job[]> {
  try { return JSON.parse(String(await $.fs.read(`${S.root}/.ship/live/待认出.json`))) as Job[] } catch { return [] }
}

// Reads one turn's words for corrections. The words wait on disk until they are read, so a session
// closed right after a correction leaves them for the next session in this project to read.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function readTurn($: any, job: Job, isNew: boolean): Promise<void> {
  const file = `${S.root}/.ship/live/待认出.json`
  if (isNew) await $.fs.write(file, JSON.stringify([...(await jobs($)), job]))
  await classify($, job.said, job.before)
  await $.fs.write(file, JSON.stringify((await jobs($)).filter((j) => j.at !== job.at)))
}

// The page beside the terminal can change the picks too (a click there): follow it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function syncPicks($: any): Promise<void> {
  if (!S.root) return
  const stat = await $.fs.stat(`${S.root}/.ship/记录.jsonl`).catch(() => undefined)
  if (stat && stat.mtimeMs !== C.rulesAt) {  // a rule confirmed or dropped on the page
    C.rulesAt = stat.mtimeMs
    C.suggested = await countSuggested($)
    $.ui.invalidate('prompt.context')
    $.ui.invalidate('ui.render')
  }
  if (P.pending?.kind !== 'choices') return
  const text = await $.fs.read(`${S.root}/.ship/live/focus.json`).catch(() => '')
  let picks: unknown
  try { picks = JSON.parse(String(text || '{}')).picks } catch { return }
  if (!Array.isArray(picks) || picks.join() === P.picks.join()) return
  P.picks = picks.map(String)
  void $.prompt.suggest({ text: `/yishuship ${P.picks.map((l, i) => `${i + 1}${l}`).join(' ')}` })
  $.ui.invalidate('ui.render')
}

// ---- the board: what the user asked for, how far it is, and whether the numbers are real ----
//
// One board per session, drawn above the prompt. Its spine is the behaviors the user confirmed.
// An optimization task adds a metric: before, target, and each measurement. A measurement counts as
// measured only when this module saw the command that produced it run in this session; otherwise
// it is shown as the agent's estimate. The rhythm strip and the outside-the-plan warning come from
// the tool calls this module sees, never from what the agent says.

const BOARD_TOOL = 'mcp__yishuship__board'
const BOARD_DESCRIPTION = `Show the user (a product person) a live board above their prompt: what they asked for, how far it is,
and for an optimization task how much the metric moved. Create it after the user confirmed the behaviors, before
changing code; update it as work moves.

Create: title, kind ("feature" or "optimize"), behaviors (what the user will see or be able to do, in their words,
max 14 characters each, no code names), optionally areas (product names of the places you plan to change, with their
files or folders) so edits elsewhere in the project are flagged, and for kind "optimize" a metric
{ name, unit, before, target } where before carries the command that measured it.
Update: doing { text, for } is the line "what you are doing now, for which behavior" (product words, no file names,
for is the behavior's 1-based number); states [{ n, state }] with state todo, doing, done (ready for the user to check)
or accepted (the user checked it); measure { value, command, note } after you measured the metric: command is the
shell command you ran to get the value (shown as measured only if a command containing it ran in this session), note says in a few
words what changed since the last measurement. When the time splits into steps, give steps (the same breakdown
each time) and focus { steps, why }: which steps to point out now and why, judged for this task (the ones whose
numbers change what to do next); the board draws before and now as aligned step bars against the target.
clear: true removes the board.`

type Behavior = { text: string; state: 'todo' | 'doing' | 'done' | 'accepted' }
type Step = { name: string; value: number }
type Reading = { value: number; isMeasured: boolean; note: string; steps: Step[] }
// What the agent chose to point out in the breakdown, and why; the plugin only draws it.
type Focus = { steps: string[]; why: string }
type Metric = { name: string; unit: string; before: Reading; target: number; readings: Reading[]; focus?: Focus }
type Beat = { at: number; kind: 'read' | 'edit' | 'command' }
const B: {
  title: string
  kind: 'feature' | 'optimize'
  behaviors: Behavior[]
  doing?: { text: string; for: number }
  metric?: Metric
  areas: { name: string; files: string[] }[]
  outside: Map<string, number>
  commands: string[] // shell commands seen this session, for telling measured numbers from estimates
  pictures: { file: string; label: string; ratio: number }[] // real screenshots; a press opens one full size
  beats: Beat[]
} = { title: '', kind: 'feature', behaviors: [], areas: [], outside: new Map(), commands: [], beats: [], pictures: [] }

// A file pattern names a file or a folder (ending in /), relative or absolute, `*` and `**` allowed.
// A relative one matches at any folder boundary, so it does not depend on where the session started.
function patternTest(pattern: string): RegExp {
  const p = pattern.trim().replace(/^\.\//, '')
  const body = p.split(/(\*\*\/?|\*)/).map((s) =>
    s.startsWith('**') ? '(?:.*/)?' : s === '*' ? '[^/]*' : s.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('')
  const tail = p.endsWith('/') ? '.*' : '(?:/.*)?'
  return new RegExp(`${p.startsWith('/') ? '^' : '(?:^|/)'}${body}${tail}$`)
}

const isNumber = (x: unknown): x is number => typeof x === 'number' && Number.isFinite(x)

function reading(x: unknown, what: string): Reading {
  const r = x as { value?: unknown; command?: unknown; note?: unknown; steps?: unknown } | undefined
  if (!r || !isNumber(r.value)) throw new Error(`${what}.value must be a number.`)
  const command = typeof r.command === 'string' ? r.command.trim() : ''
  const steps = Array.isArray(r.steps) ? r.steps.map((x, i) => {
    const st = x as { name?: unknown; value?: unknown }
    if (typeof st.name !== 'string' || !st.name || !isNumber(st.value)) throw new Error(`${what}.steps[${i}] needs a name and a number.`)
    return { name: st.name, value: st.value }
  }) : []
  // A measurement often runs inside a longer command (a script written and run in one go).
  return { value: r.value, isMeasured: command !== '' && B.commands.some((c) => c.includes(command)),
    note: typeof r.note === 'string' ? r.note : '', steps }
}

function focusOf(x: unknown): Focus {
  const f = x as { steps?: unknown; why?: unknown }
  if (!Array.isArray(f.steps) || f.steps.some((n) => typeof n !== 'string') || typeof f.why !== 'string' || !f.why) {
    throw new Error('focus needs steps (names from the breakdown) and why (one short sentence for the user).')
  }
  return { steps: f.steps as string[], why: f.why }
}

function setBoard(input: Record<string, unknown>): string {
  if (input.clear === true) {
    Object.assign(B, { title: '', kind: 'feature', behaviors: [], doing: undefined, metric: undefined, areas: [] })
    B.outside.clear()
    return 'The board is removed.'
  }
  if (input.title !== undefined) {
    const behaviors = input.behaviors
    if (typeof input.title !== 'string' || !input.title) throw new Error('title must be a non-empty string.')
    if (input.kind !== 'feature' && input.kind !== 'optimize') throw new Error('kind must be feature or optimize.')
    if (!Array.isArray(behaviors) || !behaviors.length || behaviors.some((b) => typeof b !== 'string' || !b)) {
      throw new Error('behaviors must be a non-empty list of short strings.')
    }
    let metric: Metric | undefined
    if (input.kind === 'optimize') {
      const m = input.metric as { name?: unknown; unit?: unknown; before?: unknown; target?: unknown } | undefined
      if (!m || typeof m.name !== 'string' || typeof m.unit !== 'string' || !isNumber(m.target)) {
        throw new Error('an optimize task needs metric { name, unit, before { value, command }, target }.')
      }
      metric = { name: m.name, unit: m.unit, before: reading(m.before, 'metric.before'), target: m.target, readings: [] }
      const f = (m as { focus?: unknown }).focus
      if (f !== undefined) metric.focus = focusOf(f)
    }
    const areas = Array.isArray(input.areas) ? input.areas.map((a, i) => {
      const x = a as { name?: unknown; files?: unknown }
      if (typeof x.name !== 'string' || !Array.isArray(x.files) || x.files.some((f) => typeof f !== 'string' || !f)) {
        throw new Error(`areas[${i}] needs a name and a list of files or folders.`)
      }
      return { name: x.name, files: x.files as string[] }
    }) : []
    Object.assign(B, { title: input.title, kind: input.kind, metric, areas, doing: undefined,
      behaviors: (behaviors as string[]).map((text) => ({ text, state: 'todo' })) })
    B.outside.clear()
  } else if (!B.title) {
    throw new Error('There is no board yet: create it with title, kind and behaviors.')
  }
  if (input.doing !== undefined) {
    const d = input.doing as { text?: unknown; for?: unknown }
    if (typeof d.text !== 'string' || !d.text) throw new Error('doing.text must be a non-empty string.')
    if (d.for !== undefined && (!isNumber(d.for) || !B.behaviors[d.for - 1])) throw new Error(`doing.for must be 1 to ${B.behaviors.length}.`)
    B.doing = { text: d.text, for: (d.for as number | undefined) ?? 0 }
    if (B.doing.for && B.behaviors[B.doing.for - 1]!.state === 'todo') B.behaviors[B.doing.for - 1]!.state = 'doing'
  }
  for (const s of Array.isArray(input.states) ? input.states : []) {
    const { n, state } = s as { n?: unknown; state?: unknown }
    if (!isNumber(n) || !B.behaviors[n - 1]) throw new Error(`states: n must be 1 to ${B.behaviors.length}.`)
    if (state !== 'todo' && state !== 'doing' && state !== 'done' && state !== 'accepted') throw new Error('states: state must be todo, doing, done or accepted.')
    B.behaviors[n - 1]!.state = state
  }
  if (Array.isArray(input.pictures)) {
    B.pictures = input.pictures.map((x, i) => {
      const pic = x as { file?: unknown; label?: unknown; ratio?: unknown }
      if (typeof pic.file !== 'string' || !pic.file.startsWith('/') || !pic.file.endsWith('.png')) {
        throw new Error(`pictures[${i}].file must be an absolute path to a PNG.`)
      }
      if (!isNumber(pic.ratio) || pic.ratio <= 0) throw new Error(`pictures[${i}].ratio must be the picture's height divided by its width.`)
      return { file: pic.file, label: typeof pic.label === 'string' ? pic.label : '', ratio: pic.ratio }
    })
  }
  let measured = ''
  if (input.measure !== undefined) {
    if (!B.metric) throw new Error('measure needs an optimize board with a metric.')
    const r = reading(input.measure, 'measure')
    B.metric.readings.push(r)
    if ((input.measure as { focus?: unknown }).focus !== undefined) B.metric.focus = focusOf((input.measure as { focus?: unknown }).focus)
    measured = r.isMeasured ? ' The value is shown as measured.' : ' The command was not seen in this session, so the value is shown as an estimate.'
  }
  return `Board "${B.title}" updated.${measured}`
}

const BOARD_SCHEMA = {
  type: 'object',
  properties: {
    title: { type: 'string', description: 'What the task does, in product words. Giving it creates a new board.' },
    kind: { type: 'string', enum: ['feature', 'optimize'] },
    behaviors: { type: 'array', items: { type: 'string' }, description: 'What the user will see or be able to do; max 14 characters each.' },
    areas: {
      type: 'array',
      items: { type: 'object', properties: { name: { type: 'string' }, files: { type: 'array', items: { type: 'string' } } }, required: ['name', 'files'] },
    },
    metric: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'What is measured, in the user\'s words, e.g. "说完话 → 手机开始动".' },
        unit: { type: 'string', description: 'e.g. "秒".' },
        before: { type: 'object', properties: { value: { type: 'number' }, command: { type: 'string' }, steps: { type: 'array', description: 'The same breakdown every time: each part of the measured time, in order, in the user\'s words.', items: { type: 'object', properties: { name: { type: 'string' }, value: { type: 'number' } }, required: ['name', 'value'] } } }, required: ['value'] },
        focus: { type: 'object', description: 'Which steps to point out to the user now and why: the ones whose numbers change what to do next. Your judgment for this task, not a fixed rule.', properties: { steps: { type: 'array', items: { type: 'string' } }, why: { type: 'string' } }, required: ['steps', 'why'] },
        target: { type: 'number' },
      },
      required: ['name', 'unit', 'before', 'target'],
    },
    doing: { type: 'object', properties: { text: { type: 'string' }, for: { type: 'integer' } }, required: ['text'] },
    states: {
      type: 'array',
      items: { type: 'object', properties: { n: { type: 'integer' }, state: { type: 'string', enum: ['todo', 'doing', 'done', 'accepted'] } }, required: ['n', 'state'] },
    },
    measure: { type: 'object', properties: { value: { type: 'number' }, command: { type: 'string' }, note: { type: 'string' }, steps: { type: 'array', description: 'The same breakdown every time: each part of the measured time, in order, in the user\'s words.', items: { type: 'object', properties: { name: { type: 'string' }, value: { type: 'number' } }, required: ['name', 'value'] } }, focus: { type: 'object', description: 'Which steps to point out to the user now and why: the ones whose numbers change what to do next. Your judgment for this task, not a fixed rule.', properties: { steps: { type: 'array', items: { type: 'string' } }, why: { type: 'string' } }, required: ['steps', 'why'] } }, required: ['value'] },
    pictures: {
      type: 'array',
      description: 'Real screenshots on the board, absolute PNG paths with a short label and ratio (height / width). A whole phone screen is unreadable at board size: crop to the part that changed (one card, one control) so the words can be read; the user can open each full size. Replaces the previous set; [] removes them.',
      items: { type: 'object', properties: { file: { type: 'string' }, label: { type: 'string' }, ratio: { type: 'number' } }, required: ['file', 'ratio'] },
    },
    clear: { type: 'boolean' },
  },
}

// What a tool call adds to the board: a beat on the rhythm strip, a seen command, an edit outside the plan.
function observe(tool: string, input: Record<string, unknown>): void {
  if (tool === 'Bash' && typeof input.command === 'string') {
    B.commands.push(input.command.trim())
    if (B.commands.length > 300) B.commands.shift()
  }
  if (!B.title) return
  const isEdit = ['Edit', 'MultiEdit', 'Write', 'NotebookEdit'].includes(tool)
  const kind = isEdit ? 'edit' : tool === 'Bash' ? 'command' : ['Read', 'Grep', 'Glob'].includes(tool) ? 'read' : undefined
  if (kind) {
    B.beats.push({ at: Date.now(), kind })
    if (B.beats.length > 200) B.beats.shift()
  }
  const path = String(input.file_path ?? input.notebook_path ?? '')
  // Only the project's own files count: scratch files elsewhere (/tmp) are not part of the work.
  if (isEdit && path && B.areas.length && S.cwd && path.startsWith(`${S.cwd}/`)
      && !B.areas.some((a) => a.files.some((f) => patternTest(f).test(path)))) {
    B.outside.set(path, (B.outside.get(path) ?? 0) + 1)
  }
}

function toBase64(bytes: Uint8Array): string {
  let s = ''
  for (const b of bytes) s += String.fromCharCode(b)
  return btoa(s)
}

// One row of cells: [codePoint, foreground, background] each, as a Raster takes them.
function cells(row: [number, number, number][]): string {
  const words = new Uint32Array(row.length * 3)
  row.forEach((c, i) => words.set(c, i * 3))
  return toBase64(new Uint8Array(words.buffer))
}

const DEFAULT = 0x01000000
const GREEN = 0x5fd38d
const BLUE = 0x7a9cf0
const GRAY = 0x8a8790
const DARK = 0x3a3a40

// The last two minutes, one cell per beat; thinking time between beats shows as dots, one per 5 seconds.
// Empty when nothing happened in that window: the row is then left out.
function rhythm(max: number, isWorking: boolean): { cells: string; columns: number } | undefined {
  const row: [number, number, number][] = []
  const now = Date.now()
  const beats = B.beats.filter((b) => now - b.at < 120_000)
  beats.forEach((b, i) => {
    const gap = Math.min(3, Math.floor(((beats[i + 1]?.at ?? (isWorking ? now : b.at)) - b.at) / 5000))
    row.push(b.kind === 'edit' ? [0x2588, GREEN, DEFAULT] : b.kind === 'command' ? [0x2584, GRAY, DEFAULT] : [0x2581, BLUE, DEFAULT])
    for (let k = 0; k < gap; k++) row.push([0xb7, DARK, DEFAULT])
  })
  if (!row.length) return undefined
  const shown = row.slice(-max)
  return { cells: cells(shown), columns: shown.length }
}

function meterCells(m: Metric, columns: number): string {
  const current = m.readings.at(-1)?.value ?? m.before.value
  const share = Math.max(0, Math.min(1, (m.before.value - current) / (m.before.value - m.target)))
  const fill = Math.round(share * columns)
  const row: [number, number, number][] = []
  for (let x = 0; x < columns; x++) row.push(x < fill ? [0x2588, GREEN, DEFAULT] : [0x2591, DARK, DEFAULT])
  return cells(row)
}

const FOCUS_COLORS = [0xa07ab8, 0xc09060, 0x6a8fd0, 0xd07a8a]
const SHORTER = 0x3f9d66
const QUIET = 0x3a3a40

function cellWidth(s: string): number {
  return [...s].reduce((w, ch) => w + (/[\u1100-\u115f\u2e80-\ua4cf\uac00-\ud7a3\uf900-\ufaff\ufe30-\ufe4f\uff00-\uff60]/.test(ch) ? 2 : 1), 0)
}

// One reading as a bar of its steps, on a shared scale: a focused step in its own colour, a step that got
// shorter than before in green, the rest quiet; past the target line the cells are hatched (still to cut).
function stepBar(r: Reading, m: Metric, perCell: number, isNow: boolean): { cells: string; columns: number; labels: string } {
  const row: [number, number, number][] = []
  const target = Math.round(m.target / perCell)
  let labels = ''
  let col = 0
  for (const st of r.steps) {
    const was = m.before.steps.find((b) => b.name === st.name)
    const isShorter = isNow && was !== undefined && was.value - st.value >= 0.05
    const fi = m.focus?.steps.indexOf(st.name) ?? -1
    const color = isShorter ? SHORTER : fi >= 0 ? FOCUS_COLORS[fi % FOCUS_COLORS.length]! : QUIET
    const n = Math.max(1, Math.round(st.value / perCell))
    const at = row.length
    for (let k = 0; k < n; k++) {
      const x = row.length
      row.push(x === target ? [0x2503, GREEN, color] : x > target ? [0x2592, color, DEFAULT] : [k === 0 && x > 0 ? 0x258f : 0x20, 0x18181a, color])
    }
    const text = isShorter ? `${st.name} −${fmt(was!.value - st.value)}` : !isNow && fi >= 0 ? `${st.name} ${fmt(st.value)}` : ''
    if (text) {
      const start = Math.max(at, col + (col ? 2 : 0))
      labels += ' '.repeat(start - col) + text
      col = start + cellWidth(text)
    }
  }
  while (row.length <= target) row.push(row.length === target ? [0x2503, GREEN, DEFAULT] : [0x20, DEFAULT, DEFAULT])
  return { cells: cells(row), columns: row.length, labels }
}

function fmt(n: number): string {
  return String(Math.round(n * 100) / 100)
}

const STATE_MARK: Record<Behavior['state'], [string, string]> = {
  todo: ['○', 'gray'], doing: ['●', 'green'], done: ['✓', '#9fb6f5'], accepted: ['✓✓', '#9fb6f5'],
}
const STATE_WORD: Record<Behavior['state'], string> = { todo: '', doing: '在做', done: '做好，待你验', accepted: '你验过' }

// The before and now step bars, aligned, with the agent's reason for what it points out.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function breakdown(el: any, m: Metric, last: Reading | undefined, width: number, source: (r: Reading) => string): unknown[] {
  const { Box, Text, Raster } = el
  const longest = Math.max(m.before.value, m.target, last?.value ?? 0)
  const perCell = longest / width
  const rows: unknown[] = []
  const add = (key: string, head: string, r: Reading, isNow: boolean) => {
    const bar = stepBar(r, m, perCell, isNow)
    rows.push(
      h(Text, { key: `${key}h`, dimColor: true }, `${head} ${fmt(r.value)} ${m.unit} · ${source(r)}`),
      h(Box, { key: `${key}b`, flexDirection: 'row' },
        h(Raster, { key: `${key}r`, columns: bar.columns, rows: 1, cells: bar.cells }),
        h(Text, { dimColor: true }, ` 目标 ${fmt(m.target)}`)),
      bar.labels ? h(Text, { key: `${key}l`, color: isNow ? 'green' : undefined, dimColor: !isNow }, bar.labels) : null)
  }
  add('before', '改前', m.before, false)
  if (last?.steps.length) add('now', '现在', last, true)
  if (m.focus) rows.push(h(Text, { key: 'focus', dimColor: true }, `突出：${m.focus.steps.join('、')}。${m.focus.why}`))
  return rows
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function drawBoard($: any, el: any, columns: number, isWorking: boolean): RenderElement {
  const { Box, Text, Raster } = el
  const done = B.behaviors.filter((b) => b.state === 'done' || b.state === 'accepted').length
  const { Button } = el
  const parts: unknown[] = [h(Box, { key: 'title', flexDirection: 'row' },
    h(Text, { bold: true, color: '#d6a8ff' }, B.title),
    h(Text, { dimColor: true }, `  ${done} / ${B.behaviors.length} 条做好  `),
    // The user closes the board themselves; it would otherwise stay until the agent clears it.
    h(Button, { key: 'close', plain: true, dimColor: true, onPress: () => { setBoard({ clear: true }); $.ui.invalidate('ui.render') } }, '×'))]

  const m = B.metric
  if (m) {
    const last = m.readings.at(-1)
    const current = last ?? m.before
    const gained = m.before.value - current.value
    const left = current.value - m.target
    const share = Math.round(Math.max(0, gained / (m.before.value - m.target)) * 100)
    const source = (r: Reading) => (r.isMeasured ? '实测' : 'AI 推测')
    const width = Math.max(10, Math.min(36, columns - 40))
    parts.push(
      h(Text, { key: 'mname', dimColor: true }, m.name),
      h(Box, { key: 'mnow', flexDirection: 'row' },
        h(Text, {}, '现在 '),
        h(Text, { bold: true, color: last ? (last.isMeasured ? 'green' : 'yellow') : undefined }, `${fmt(current.value)} ${m.unit}`),
        h(Text, { color: current.isMeasured ? 'green' : 'yellow' }, ` · ${source(current)}`),
        h(Text, { dimColor: true }, last
          ? `　${gained >= 0 ? '已快了' : '反而慢了'} ${fmt(Math.abs(gained))} ${m.unit}，${left > 0 ? `离目标还差 ${fmt(left)} ${m.unit}` : '已达到目标'}`
          : '　还没有改后的测量')),
      ...(m.before.steps.length
        ? breakdown(el, m, last, Math.max(20, Math.min(56, columns - 16)), source)
        : [h(Box, { key: 'meter', flexDirection: 'row' },
            h(Text, { dimColor: true }, `改前 ${fmt(m.before.value)} `),
            h(Raster, { key: 'meterbar', columns: width, rows: 1, cells: meterCells(m, width) }),
            h(Text, { dimColor: true }, ` 目标 ${fmt(m.target)} ${m.unit}`),
            h(Text, { color: 'green' }, `  完成 ${share}%`)),
          h(Text, { key: 'mlab', dimColor: true }, `改前的数字：${source(m.before)}`)]),
      last?.note ? h(Text, { key: 'mnote', dimColor: true }, `最近一次：${last.note}`) : null)
  }

  if (B.pictures.length) {
    const { Image, Button } = el
    // A terminal cell is about twice as tall as wide. Wide crops get the board's width so their words
    // can be read; tall pictures (a whole screen) stay small and are meant to be opened.
    const wide = Math.max(20, Math.min(64, Math.floor((columns - 4) / B.pictures.length) - 2))
    parts.push(h(Box, { key: 'pictures', flexDirection: 'row', gap: 2, marginTop: 1 },
      ...B.pictures.map((pic, i) => {
        const cols = pic.ratio < 1 ? wide : 14
        const rows = Math.max(3, Math.min(30, Math.round((cols * pic.ratio) / 2)))
        return h(Box, { key: `pic${i}`, flexDirection: 'column', width: cols },
          h(Box, { key: `cap${i}`, flexDirection: 'row' },
            h(Text, { dimColor: true, wrap: 'truncate-end' }, `${pic.label} `),
            h(Button, { key: `zoom${i}`, hotkey: String(i + 1), plain: true, dimColor: true,
              onPress: () => { void $.process.run(['open', '-a', 'Preview', pic.file]) } }, '放大')),
          h(Image, { key: `img${i}`, source: { file: pic.file, format: 'png' }, columns: cols, rows, alt: pic.label || '截图' }))
      })))
  }

  B.behaviors.forEach((b, i) => {
    const [mark, color] = STATE_MARK[b.state]
    const isCurrent = b.state === 'doing'
    parts.push(h(Box, { key: `b${i}`, flexDirection: 'row' },
      h(Box, { width: 3 }, h(Text, { color }, mark)),
      h(Text, { color: isCurrent ? 'green' : undefined, dimColor: b.state === 'todo' }, b.text),
      STATE_WORD[b.state] ? h(Text, { dimColor: !isCurrent, color: isCurrent ? 'green' : undefined }, `　${STATE_WORD[b.state]}`) : null))
  })

  if (isWorking && B.doing) {
    const target = B.doing.for ? B.behaviors[B.doing.for - 1]?.text : ''
    parts.push(h(Text, { key: 'doing', color: 'green' }, `→ ${B.doing.text}${target ? `，为了「${target}」` : ''}`))
  }
  const beats = rhythm(Math.max(10, Math.min(60, columns - 34)), isWorking)
  if (beats) {
    parts.push(h(Box, { key: 'rhythm', flexDirection: 'row' },
      h(Text, { dimColor: true }, '节奏 '),
      h(Raster, { key: 'beats', columns: beats.columns, rows: 1, cells: beats.cells }),
      h(Text, { dimColor: true }, '  ▁读 █改 ▄命令 ·想')))
  }

  const outside = [...B.outside.entries()]
  if (outside.length) {
    parts.push(h(Text, { key: 'outside', color: 'yellow' },
      `⚠ 动了计划外的地方：${outside.slice(0, 3).map(([p]) => base(p)).join('、')}${outside.length > 3 ? ` 等 ${outside.length} 个文件` : ''}`))
  }
  return h(Box, { flexDirection: 'column' }, ...parts) as RenderElement
}

// ---- page review: the user comments on a page the agent made, without leaving it ----
//
// `review` serves a folder of pages through scripts/review.py and opens one; each part of a page gets a
// 「说一句」 button. This module watches the folder's .review/inbox.jsonl and hands each new comment to the
// agent as a prompt; the agent answers with `reply`, which the page shows next to the same part.
// Which folder is under review survives a reload of this module in /tmp, keyed by the session.

const REVIEW_TOOL = 'mcp__yishuship__review'
const REPLY_TOOL = 'mcp__yishuship__reply'
const R: { dir: string; port: number; seen: number } = { dir: '', port: 0, seen: 0 }

function portFor(dir: string): number {
  let h = 0
  for (const ch of dir) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return 8770 + (h % 200)
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function reviewLines($: any, name: 'inbox' | 'replies'): Promise<Record<string, string>[]> {
  const text = String(await $.fs.read(`${R.dir}/.review/${name}.jsonl`).catch(() => ''))
  return text.split('\n').filter((l) => l.trim()).map((l) => JSON.parse(l) as Record<string, string>)
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function startReview($: any, page: string): Promise<string> {
  const dir = page.slice(0, page.lastIndexOf('/'))
  const port = portFor(dir)
  const alive = await $.http.fetch(`http://127.0.0.1:${port}/__thread?page=`).then((r: { status: number }) => r.status === 200, () => false)
  if (!alive) {
    await $.process.run(['bash', '-c', 'nohup python3 "$0" "$1" "$2" >/dev/null 2>&1 &', `${$.plugin.root}/scripts/review.py`, dir, String(port)])
    await $.clock.sleep(600)
  }
  const isNewDir = R.dir !== dir
  R.dir = dir
  R.port = port
  if (isNewDir) R.seen = (await reviewLines($, 'inbox')).length // comments from before are not new
  await $.fs.write(`/tmp/yishuship-review-${S.session}.json`, JSON.stringify(R))
  const url = `http://127.0.0.1:${port}/${encodeURI(page.slice(dir.length + 1))}`
  await $.process.run(['open', url])
  return url
}

// New comments become prompts. A comment written while the agent works waits in the queue for its turn.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function pollReview($: any): Promise<void> {
  if (!R.dir) return
  const inbox = await reviewLines($, 'inbox')
  const fresh = inbox.slice(R.seen)
  if (!fresh.length) return
  R.seen = inbox.length
  await $.fs.write(`/tmp/yishuship-review-${S.session}.json`, JSON.stringify(R))
  for (const c of fresh) {
    await $.prompt.submit({ text: `【页面意见】${c.page} 的「${c.label}」（编号 ${c.id}）：${c.text}\n` +
      `看完或改完后，用 reply 工具回复编号 ${c.id}，一两句话；改了页面就说改了哪里，用户刷新就能看到。` })
  }
}

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    try {
      await $.tool.register({ name: 'board', description: BOARD_DESCRIPTION, inputSchema: BOARD_SCHEMA })
      await $.tool.register({ name: 'review',
        description: 'Open a page you made (an HTML file) for the user to review in the browser beside the terminal. Each part of the page gets a 「说一句」 button; the user\'s comments come back to you as prompts marked 【页面意见】 with an id, and you answer each with the reply tool. Use it whenever the user should judge something visual (before/after, layouts, motion) instead of reading text. Mark the parts with data-review="name" on sections, or the page\'s section and .card elements are used.',
        inputSchema: { type: 'object', properties: { page: { type: 'string', description: 'Absolute path of the HTML file.' } }, required: ['page'] } })
      await $.tool.register({ name: 'reply',
        description: 'Answer a 【页面意见】 comment; the answer shows on the page next to the part the user pointed at. One or two sentences in the user\'s language; if you changed the page, say what changed.',
        inputSchema: { type: 'object', properties: { id: { type: 'string' }, text: { type: 'string' } }, required: ['id', 'text'] } })
      // While the agent works, the step's clock moves every second, so a long step still looks alive.
      $.clock.every(1000, () => { if (S.now?.state === 'working') $.ui.invalidate('ui.render') })
      let dir = String(e.cwd).replace(/\/+$/, '')
      S.cwd = dir
      while (dir && !(await $.fs.exists(`${dir}/.ship/ideas`))) dir = dir.slice(0, dir.lastIndexOf('/'))
      S.root = dir || undefined
      S.session = await $.session.id()
      try { Object.assign(R, JSON.parse(String(await $.fs.read(`/tmp/yishuship-review-${S.session}.json`)))) } catch { /* no review open */ }
      $.clock.every(700, () => void pollReview($).catch(() => undefined))
      const day = new Date(await $.clock.now()).toISOString().slice(0, 10)
      S.log = `${day}-${S.session.slice(0, 8)}`
      // what is in .ship/live/ stays on this machine, whatever the project's own .gitignore says
      if (S.root) await $.fs.write(`${S.root}/.ship/live/.gitignore`, '*\n')
      await save($, { state: 'stopped', reason: 'start', since: await $.clock.now() }, { who: 'engine', what: 'session.start' })
      P.pending = await readPending($)
      $.clock.every(500, () => void syncPicks($))
      if (S.root) for (const job of await jobs($)) C.work = C.work.then(() => readTurn($, job, false)).catch(() => undefined)
      $.ui.invalidate('ui.render')
    } catch { /* watching only */ }
    return result
  })

  on('turn.start', async ($, e, next) => {
    P.pending = undefined
    $.ui.invalidate('ui.render')
    await save($, { state: 'working', said: clip(e.text, 200), did: '' })
    return next(e)
  })

  // Every prompt the user sends, typed at the start of a turn or while the agent works.
  on('prompt.submit', async ($, e, next) => {
    const text = e.text.trim()
    if (S.root && e.origin.kind === 'composer' && text && !/^\/(?!yishuship\b)/.test(text)) {
      C.said.push(text)
      await save($, {}, { who: 'user', said: text, turn: e.turnId ?? '', mid: !!e.turnId })
      // on disk at once, so a session closed before this turn ends leaves it for the next one to read
      if (!C.open) C.open = new Date(await $.clock.now()).toISOString()
      const rest = (await jobs($)).filter((j) => j.at !== C.open)
      await $.fs.write(`${S.root}/.ship/live/待认出.json`, JSON.stringify([...rest, { at: C.open, said: C.said, before: C.lastAnswer }]))
    }
    return next(e)
  })

  // The rules the user confirmed, in every turn's context: this project's and their own.
  on('prompt.context', async ($, e, next) => {
    const result = await next(e)
    if (!S.root) return result
    const mine = String(await $.fs.read(`${S.root}/.ship/live/个人规则.md`).catch(() => '')).trim()
    const here = String(await $.fs.read(`${S.root}/.ship/规则.md`).catch(() => '')).trim()
    if (!mine && !here) return result
    const text = '这些是这位用户纠正过、并确认要一直遵守的做法。开工前先对照；要做的事和其中一条冲突时，停下来用一句话说清冲突，其余时候照做、不必提起。\n\n'
      + [mine && `对他所有的项目：\n${mine}`, here && `对这个项目：\n${here}`].filter(Boolean).join('\n\n')
    return { ...result, blocks: [...result.blocks, { name: 'yishuship 你确认过的规则', text }] }
  })

  on('tool.call', async ($, e, next) => {
    const input = e as unknown as Record<string, unknown>
    if ((e.tool as string) === REVIEW_TOOL) {
      const page = String(input.page ?? '')
      if (!page.startsWith('/') || !page.endsWith('.html')) return { deny: 'page must be an absolute path to an .html file.' }
      if (!(await $.fs.exists(page))) return { deny: `No file at ${page}.` }
      return { result: `Opened ${await startReview($, page)} for review.` }
    }
    if ((e.tool as string) === REPLY_TOOL) {
      if (!R.dir) return { deny: 'No page is under review: open one with the review tool first.' }
      const id = String(input.id ?? '')
      const text = String(input.text ?? '').trim()
      if (!text) return { deny: 'text must not be empty.' }
      if (!(await reviewLines($, 'inbox')).some((c) => c.id === id)) return { deny: `No comment with id ${id}.` }
      const file = `${R.dir}/.review/replies.jsonl`
      const before = String(await $.fs.read(file).catch(() => ''))
      await $.fs.write(file, before + JSON.stringify({ id, at: new Date().toISOString(), text }) + '\n')
      return { result: 'The answer is on the page.' }
    }
    if ((e.tool as string) === BOARD_TOOL) {
      try {
        const text = setBoard(input)
        $.ui.invalidate('ui.render')
        return { result: text }
      } catch (err) {
        return { deny: (err as Error).message }
      }
    }
    if (!S.root) {
      // No idea in progress here: only the board follows the work, when one is shown.
      observe(e.tool, input)
      if (B.title) $.ui.invalidate('ui.render')
      return next(e)
    }
    const sub = typeof e.agentId === 'string'
    if ((e.tool as string) === 'AskUserQuestion' && !sub) {
      const question = firstQuestion(input)
      $.ui.invalidate('ui.render')
      await save($, { state: 'asking', question }, { who: 'agent', asked: input.questions })
      const result = await next(e)
      await save($, { state: 'working', did: '你回答了问题' }, { who: 'user', answered: (result as { result?: unknown })?.result ?? null })
      return result
    }
    const did = (sub ? '子 Agent ' : '') + describe(e.tool, input)
    observe(e.tool, input)
    const saved = save($, { did }, { who: sub ? 'subagent' : 'agent', tool: e.tool, did, id: e.tool_use_id })
    $.ui.invalidate('ui.render')
    await saved
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (!e.agentId) {
      await save($, { state: 'stopped', reason: e.reason, said: clip(e.answer, 300) },
        { who: 'agent', stopped: e.reason, answer: e.answer, ms: e.durationMs, turn: e.turnId })
      const said = C.said
      const before = C.lastAnswer
      C.said = []
      C.lastAnswer = e.answer || before
      if (said.length) {
        const job = { at: C.open, said, before }  // already on disk since the words were sent
        C.work = C.work.then(() => readTurn($, job, false)).catch(() => undefined)
      }
      C.open = ''
      P.pending = await readPending($).catch(() => undefined)
      $.ui.invalidate('ui.render')
    }
    return result
  })

  // The band right above where the user types: what they need to do now, and a key to do it.
  // A pending choice: one box per option with a small picture (where the terminal draws
  // pictures; its words elsewhere), a digit picks it and the page beside the terminal shows it large.
  on('ui.render', { component: 'AbovePrompt' }, ($, e, next) => {
    if ((!S.root && !B.title) || e.props.hasSurvey || e.surface !== 'terminal') return next(e)
    const el = $.ui.resolve(e)
    const { Box, Text, Button, Image } = el
    const now = S.now
    // The board, when one is shown: while the agent works, and outside an idea's project at any time.
    if (B.title && (now?.state === 'working' || !S.root)) return drawBoard($, el, e.props.bodyColumns, now?.state === 'working')
    const line = (color: string, text: string, rest = '') => h(Box, { flexDirection: 'row' }, h(Text, { color, bold: true }, `● ${text}`), rest ? h(Text, { dimColor: true }, `  ${rest}`) : null) as RenderElement
    if (!now || now.state === 'closed') return next(e)
    const rules = C.suggested > 0 && now.state === 'stopped'
      ? h(Text, { color: 'yellow' }, `● Agent 认出了你的 ${C.suggested} 条纠正，想记下来以后照做，请在旁边页面点“确认”或“不要”`)
      : null
    const withRules = (el: unknown) => (rules ? h(Box, { flexDirection: 'column' }, el, rules) : el) as RenderElement
    if (now.state === 'asking') return line('magenta', 'Agent 在上面问你一个问题，请选一个答案')
    if (now.state === 'working') {
      const did = now.did ? (now.did.startsWith('在') ? `它正${now.did}` : now.did) : '它刚开始这一轮'
      return line('green', 'Agent 正在工作，你现在不用操作', did)
    }
    const pending = P.pending
    const offer = (text: string) => { void $.prompt.suggest({ text }) } // dim, Tab takes it
    if (pending?.kind === 'choices') {
      const count = '零一两三四五六七八九'[pending.questions.length] ?? String(pending.questions.length)
      const reply = () => P.picks.map((l, i) => `${i + 1}${l}`).join(' ')
      let key = 0
      const pick = (qi: number, letter: string) => () => {
        P.picks[qi] = letter
        // a dim suggestion, not text: the box stays empty, so the next digit still picks
        void $.prompt.suggest({ text: `/yishuship ${reply()}` })
        const opt = pending.questions[qi]!.opts.find((o) => o.letter === letter)
        void $.fs.write(`${S.root}/.ship/live/focus.json`,
          JSON.stringify({ q: qi + 1, letter, src: opt?.src ?? '', picks: P.picks }))
        $.ui.invalidate('ui.render')
      }
      const head = line('magenta', `Agent 停下来了，有${count}件事要你决定`,
        `按数字键选中，旁边的页面会放大它。现在的回复：/yishuship ${reply()}，按 Tab 采用，再按回车发出`)
      // side by side when two boxes fit with their words; one per line on a narrow terminal
      const wide = e.props.bodyColumns >= 84
      const cols = wide ? Math.min(40, Math.floor((e.props.bodyColumns - 8) / 2)) : Math.max(20, e.props.bodyColumns - 2)
      const rows = pending.questions.map((q, qi) => h(Box, { key: `q${qi}`, flexDirection: 'column', marginTop: 1 },
        h(Text, { bold: true }, `${'①②③④⑤⑥⑦⑧⑨'[qi] ?? qi + 1} ${q.q}`),
        h(Box, { flexDirection: wide ? 'row' : 'column', gap: wide ? 2 : 0 }, ...q.opts.map((o) => {
          key += 1
          const chosen = P.picks[qi] === o.letter
          const label = `${chosen ? '● ' : '○ '}${o.letter} ${o.text}${o.rec ? '（推荐）' : ''}`
          return h(Box, { key: `o${key}`, flexDirection: 'column', borderStyle: 'round', borderColor: chosen ? 'magenta' : 'gray', paddingX: 1, width: cols },
            o.png ? h(Image, { key: `i${key}`, source: { file: o.png, format: 'png' }, columns: cols - 4, rows: Math.round((cols - 4) / 6), alt: o.text }) : null,
            h(Button, { key: `k${key}`, hotkey: String(key), plain: true, onPress: pick(qi, o.letter) }, label))
        }))))
      return withRules(h(Box, { flexDirection: 'column' }, head, ...rows))
    }
    if (pending?.kind === 'satisfied') {
      return withRules(h(Box, { flexDirection: 'column' },
        line('magenta', 'Agent 做完了，请看旁边页面的改前改后，然后告诉它满不满意', '按数字键选，回复以灰字出现在输入框里，按 Tab 采用，再按回车发出'),
        h(Box, { flexDirection: 'row', gap: 2 },
          h(Button, { key: 'yes', hotkey: '1', plain: true, onPress: () => offer('/yishuship 满意') }, '满意'),
          h(Button, { key: 'no', hotkey: '2', plain: true, onPress: () => offer('/yishuship 不行') }, '不行'))))
    }
    const why: Record<string, string> = {
      answer: 'Agent 已经停下，请告诉它下一步做什么',
      aborted: '你打断了 Agent，请告诉它接下来做什么',
      error: 'Agent 出错停下了，请看上面的错误信息',
      refusal: 'Agent 拒绝了这个请求，请看上面它说了什么',
      start: 'Agent 已经打开，请告诉它要做什么',
    }
    return withRules(line('cyan', why[now.reason ?? 'answer'] ?? why.answer!))
  })

  on('session.end', async ($, e, next) => {
    await save($, { state: 'closed' }, { who: 'engine', what: 'session.end' })
    return next(e)
  })
}
