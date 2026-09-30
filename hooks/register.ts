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
  session: string
  log: string
  lines: string[]
  part: number
  now?: Now
  writing: Promise<void>
} = { session: '', log: '', lines: [], part: 0, writing: Promise.resolve() }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function save($: any, patch: Partial<Now>, step?: Record<string, unknown>): Promise<void> {
  if (!S.root) return S.writing
  const r = S.root
  S.writing = S.writing.then(async () => {
    const at = await $.clock.now()
    const changed = patch.state !== undefined && patch.state !== S.now?.state
    const now: Now = { ...(S.now ?? { session: S.session, state: 'stopped', since: at }), ...patch, session: S.session, at }
    if (changed) now.since = at
    if (patch.state && patch.state !== 'asking') delete now.question
    if (patch.state && patch.state !== 'stopped') delete now.reason
    S.now = now
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

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    try {
      let dir = String(e.cwd).replace(/\/+$/, '')
      while (dir && !(await $.fs.exists(`${dir}/.ship/ideas`))) dir = dir.slice(0, dir.lastIndexOf('/'))
      S.root = dir || undefined
      S.session = await $.session.id()
      const day = new Date(await $.clock.now()).toISOString().slice(0, 10)
      S.log = `${day}-${S.session.slice(0, 8)}`
      // what is in .ship/live/ stays on this machine, whatever the project's own .gitignore says
      if (S.root) await $.fs.write(`${S.root}/.ship/live/.gitignore`, '*\n')
      await save($, { state: 'stopped', reason: 'start', since: await $.clock.now() }, { who: 'engine', what: 'session.start' })
      P.pending = await readPending($)
      $.clock.every(500, () => void syncPicks($))
      for (const job of await jobs($)) C.work = C.work.then(() => readTurn($, job, false)).catch(() => undefined)
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
    if (!S.root) return next(e)
    const input = e as unknown as Record<string, unknown>
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
    $.ui.invalidate('ui.render')
    await save($, { did }, { who: sub ? 'subagent' : 'agent', tool: e.tool, did, id: e.tool_use_id })
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
    if (!S.root || e.props.hasSurvey || e.surface !== 'terminal') return next(e)
    const { Box, Text, Button, Image } = $.ui.resolve(e)
    const now = S.now
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
