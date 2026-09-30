// Watches the agent inside Claude Code and writes what it sees into the project,
// so the page beside the terminal follows the agent without the agent writing anything.
//
//   .ship/live/now.json            the state right now: working / asking / stopped / closed
//   .ship/live/<date>-<id>.jsonl   what happened, one step per line (kept out of git)
//   .ship/live/focus.json          the option the user picked (a digit here, or a click on the page)
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

// The page beside the terminal can change the picks too (a click there): follow it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function syncPicks($: any): Promise<void> {
  if (!S.root || P.pending?.kind !== 'choices') return
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
      await save($, { state: 'stopped', reason: 'start', since: await $.clock.now() }, { who: 'engine', what: 'session.start' })
      P.pending = await readPending($)
      $.clock.every(500, () => void syncPicks($))
      $.ui.invalidate('ui.render')
    } catch { /* watching only */ }
    return result
  })

  on('turn.start', async ($, e, next) => {
    P.pending = undefined
    $.ui.invalidate('ui.render')
    await save($, { state: 'working', said: clip(e.text, 200), did: '' }, { who: 'user', said: e.text, turn: e.turnId })
    return next(e)
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
      return h(Box, { flexDirection: 'column' }, head, ...rows) as RenderElement
    }
    if (pending?.kind === 'satisfied') {
      return <RenderElement>h(Box, { flexDirection: 'column' },
        line('magenta', 'Agent 做完了，请看旁边页面的改前改后，然后告诉它满不满意', '按数字键选，回复以灰字出现在输入框里，按 Tab 采用，再按回车发出'),
        h(Box, { flexDirection: 'row', gap: 2 },
          h(Button, { key: 'yes', hotkey: '1', plain: true, onPress: () => offer('/yishuship 满意') }, '满意'),
          h(Button, { key: 'no', hotkey: '2', plain: true, onPress: () => offer('/yishuship 不行') }, '不行')))
    }
    const why: Record<string, string> = {
      answer: 'Agent 已经停下，请告诉它下一步做什么',
      aborted: '你打断了 Agent，请告诉它接下来做什么',
      error: 'Agent 出错停下了，请看上面的错误信息',
      refusal: 'Agent 拒绝了这个请求，请看上面它说了什么',
      start: 'Agent 已经打开，请告诉它要做什么',
    }
    return line('cyan', why[now.reason ?? 'answer'] ?? why.answer!)
  })

  on('session.end', async ($, e, next) => {
    await save($, { state: 'closed' }, { who: 'engine', what: 'session.end' })
    return next(e)
  })
}
