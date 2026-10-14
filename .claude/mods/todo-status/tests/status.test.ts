import { describe, expect, test } from 'claude-code/testing'

import { parseTodo, parseWorktrees } from '../hooks/parse'

// Shaped like a project tasks/todo.md: a Resume block, a Roadmap whose current stage is [~],
// an item wrapped over two lines that waits on Joshua, and a later section that must not leak in.
const TODO = [
  '# Example project — todo',
  '',
  '## ▶ Resume here (updated 2026-10-08)',
  '- **Where:** main.',
  '- **Next:** (1) **S1.1 fix pack** = gate M1, M3',
  '  and M5. (2) S2.',
  '- **Before starting:** local database `example-db` must be running.',
  '',
  '## Roadmap',
  '',
  '- [X] **S1 close-out** (spec) — gate PASSED',
  '  - [X] H2 done',
  '- [~] **S1.1 fix pack** (cards in spec) — cards written',
  '  - [ ] M1 no silent truncation',
  '  - [x] M4 control borders ≥ 3:1 — `8d4e852f`',
  '  - [~] S2 spec — planner expanded it → **awaiting',
  '    Joshua\'s approval**',
  '- [ ] **S2 — JHA + Quality logs** — platform first',
  '',
  '## Open follow-ups',
  '- [ ] something unrelated',
  '- [x] old item, 7 MEDIUM → Joshua',
].join('\n')

const PORCELAIN = [
  'worktree D:/work/repo',
  'HEAD abc',
  'branch refs/heads/main',
  '',
  'worktree D:/work/repo/.worktrees/m1',
  'HEAD def',
  'branch refs/heads/wt/m1',
  '',
  'worktree D:\\work\\repo\\.worktrees\\probe',
  'HEAD 123',
  'detached',
  '',
].join('\n')

describe('parseTodo', () => {
  test('finds the current stage, its progress and its next step', () => {
    const s = parseTodo(TODO)
    expect(s.phase).toBe('S1.1 fix pack')
    expect(s.total).toBe(3)
    expect(s.done).toBe(1)
    expect(s.nextStep).toBe('M1 no silent truncation')
    expect(s.items.map(i => i.mark)).toEqual(['open', 'done', 'doing'])
  })

  test('reads the Resume block, joining wrapped lines', () => {
    const s = parseTodo(TODO)
    expect(s.resumeUpdated).toBe('2026-10-08')
    expect(s.resumeNext).toBe('(1) S1.1 fix pack = gate M1, M3 and M5. (2) S2.')
    expect(s.beforeStarting).toBe('local database example-db must be running.')
  })

  test('lists only unticked items that wait on Joshua', () => {
    const s = parseTodo(TODO)
    expect(s.waiting).toEqual(["S2 spec — planner expanded it → awaiting Joshua's approval"])
  })

  test('says so when every stage is ticked', () => {
    const s = parseTodo('## Roadmap\n- [x] **S1** — done\n')
    expect(s.phase).toBe('All stages ticked')
    expect(s.total).toBe(0)
  })
})

describe('parseWorktrees', () => {
  test('keeps .worktrees/ entries only, Windows paths included', () => {
    expect(parseWorktrees(PORCELAIN)).toEqual([
      { name: 'm1', branch: 'wt/m1' },
      { name: 'probe', branch: '(detached)' },
    ])
  })
})

describe('the mod in the engine', () => {
  for (const surface of ['terminal', 'desktop'] as const) {
    test(`/todo-status opens a pane that draws the status (${surface}) and writes nothing`, async ($, on) => {
      const writes: string[] = []
      const statuses: (string | undefined)[] = []
      const opened: string[] = []
      on('ui.status', async (_$, e) => {
        statuses.push(e.text)
        return { value: undefined }
      })
      on('ui.open', async (_$, e) => {
        opened.push(e.id)
        return { value: { isPlaced: true } }
      })
      const reads: string[] = []
      on('session.root', async () => ({ value: 'D:/work/repo' }))
      on('fs.read', async (_$, e) => {
        reads.push(String(e.path))
        return { value: TODO }
      })
      on('fs.write', async (_$, e) => {
        writes.push(String(e.path))
        return { value: undefined }
      })
      on('process.run', async () => ({
        value: { exitCode: 0, stdout: PORCELAIN, stderr: '', isStdoutTruncated: false, isStderrTruncated: false },
      }))

      const ran = await $.command.run({
        command: 'todo-status',
        args: '',
        origin: { kind: 'composer' },
        presentation: { isFullscreen: true, columns: 160 },
      })
      expect(ran).toMatchObject({ text: 'Project status pane opened.' })
      expect(opened).toEqual(['todo-status'])
      expect(statuses.at(-1)).toBe('S1.1 fix pack · 1/3')

      const pane = await $.ui.mount({
        plugin: 'todo-status',
        surface,
        component: 'Pane',
        requestId: 'todo-status',
        props: {
          title: 'Project status',
          isFocused: false,
          bodyColumns: 60,
          placement: 'dock',
          scroll: { offset: 0, bodyRows: 40 },
          view: {},
        },
      })
      expect(await pane.find({ text: 'S1.1 fix pack' })).toBeDefined()
      expect(await pane.find({ text: /awaiting Joshua's approval/ })).toBeDefined()
      expect(await pane.find({ text: /m1/ })).toBeDefined()
      expect(writes).toEqual([])
      // the engine hands fs.read a native path, so compare with separators normalised
      expect(reads.map(p => p.replace(/\\/g, '/'))).toEqual(['D:/work/repo/tasks/todo.md'])
    })
  }
})
