import type { Mark, Snapshot, TodoItem, Worktree } from '../types'

type Line = { indent: number; mark: Mark; text: string; section: string; bold?: string }

const BULLET = /^(\s*)- \[( |x|X|~)\] (.*)$/
/** Whose sign-off the pane tracks: unticked items naming this person as the blocker show under "Waiting on". */
export const OWNER = 'Joshua'
const WAITING = new RegExp(`awaiting ${OWNER}|waiting on ${OWNER}|${OWNER}'?s (approval|decision|OK)\\b|→ ${OWNER}\\b`, 'i')

const clean = (s: string) => s.replace(/\*\*/g, '').replace(/`/g, '').replace(/\s+/g, ' ').trim()

const markOf = (c: string): Mark => (c === ' ' ? 'open' : c === '~' ? 'doing' : 'done')

/** Every checkbox line of the todo, with its wrapped continuation lines joined on. */
export function checkboxLines(md: string): Line[] {
  const out: Line[] = []
  let section = ''
  let cur: Line | undefined
  for (const raw of md.split(/\r?\n/)) {
    if (raw.startsWith('#')) {
      section = raw.replace(/^#+\s*/, '')
      cur = undefined
      continue
    }
    const m = BULLET.exec(raw)
    if (m) {
      const line: Line = { indent: (m[1] ?? '').length, mark: markOf(m[2] ?? ' '), text: m[3] ?? '', section }
      cur = line
      out.push(line)
    } else if (cur && raw.trim() !== '' && /^\s/.test(raw) && !/^\s*- /.test(raw)) {
      cur.text += ' ' + raw.trim()
    } else {
      cur = undefined
    }
  }
  return out.map(l => ({ ...l, bold: /\*\*(.+?)\*\*/.exec(l.text)?.[1], text: clean(l.text) }))
}

/** The "- **Label:** text" bullets of the Resume block, continuations joined. */
function resumeBullets(md: string): { updated: string; bullets: Record<string, string> } {
  const lines = md.split(/\r?\n/)
  const start = lines.findIndex(l => /^## .*Resume here/.test(l))
  if (start < 0) return { updated: '', bullets: {} }
  const updated = /updated ([^)]+)\)/.exec(lines[start] ?? '')?.[1] ?? ''
  const bullets: Record<string, string> = {}
  let key = ''
  for (const raw of lines.slice(start + 1)) {
    if (raw.startsWith('#')) break
    const m = /^- \*\*(.+?):\*\*\s*(.*)$/.exec(raw)
    if (m) {
      key = m[1] ?? ''
      bullets[key] = m[2] ?? ''
    } else if (key && /^\s+\S/.test(raw)) {
      bullets[key] += ' ' + raw.trim()
    } else {
      key = ''
    }
  }
  for (const k of Object.keys(bullets)) bullets[k] = clean(bullets[k] ?? '')
  return { updated, bullets }
}

const stageName = (l: Line) => {
  const name = clean(l.bold ?? /^(.*?) — /.exec(l.text)?.[1] ?? l.text)
  return name.length > 60 ? name.slice(0, 57) + '…' : name
}

export function parseTodo(md: string): Omit<Snapshot, 'worktrees' | 'readAt'> {
  const all = checkboxLines(md)
  const roadmap = all.filter(l => l.section === 'Roadmap')
  const stages = roadmap.filter(l => l.indent === 0)
  const current = stages.find(s => s.mark === 'doing') ?? stages.find(s => s.mark === 'open')

  let items: TodoItem[] = []
  if (current) {
    const from = roadmap.indexOf(current) + 1
    const nextStage = roadmap.findIndex((l, i) => i >= from && l.indent === 0)
    items = roadmap
      .slice(from, nextStage < 0 ? undefined : nextStage)
      .map(({ mark, text }) => ({ mark, text }))
  }

  const { updated, bullets } = resumeBullets(md)
  return {
    resumeUpdated: updated,
    resumeNext: bullets['Next'] ?? '',
    beforeStarting: bullets['Before starting'] ?? '',
    phase: current ? stageName(current) : 'All stages ticked',
    items,
    done: items.filter(i => i.mark === 'done').length,
    total: items.length,
    nextStep: items.find(i => i.mark !== 'done')?.text ?? '',
    waiting: all.filter(l => l.mark !== 'done' && WAITING.test(l.text)).map(l => l.text),
    error: '',
  }
}

/** `git worktree list --porcelain` → the worktrees under .worktrees/ (main excluded). */
export function parseWorktrees(porcelain: string): Worktree[] {
  return porcelain
    .split(/\r?\n\r?\n/)
    .map(block => {
      const path = /^worktree (.+)$/m.exec(block)?.[1]?.replace(/\\/g, '/') ?? ''
      const branch = /^branch refs\/heads\/(.+)$/m.exec(block)?.[1] ?? (/^detached$/m.test(block) ? '(detached)' : '')
      return { path, branch }
    })
    .filter(w => w.path.includes('/.worktrees/'))
    .map(w => ({ name: w.path.split('/.worktrees/')[1] ?? w.path, branch: w.branch }))
}
