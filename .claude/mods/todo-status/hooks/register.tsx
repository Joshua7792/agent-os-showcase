import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Snapshot } from '../types'
import { OWNER, parseTodo, parseWorktrees } from './parse'

// Read-only by design: this module only reads the todo and asks git for its worktree list.
// The todo is resolved against the session's project root; change TODO_REL to point at another project's todo.
const TODO_REL = 'tasks/todo.md'
const PANE = 'todo-status'
const REFRESH_MS = 30_000

const snap = atom({ plugin: 'todo-status', key: 'snap' } as const, null as Snapshot | null)

const MARK = { done: '✓', doing: '~', open: '☐' } as const

async function readSnapshot($: EngineInterface): Promise<Snapshot> {
  const readAt = new Date().toISOString().slice(11, 16)
  const REPO = await $.session.root()
  const TODO = `${REPO}/${TODO_REL}`
  let worktrees: Snapshot['worktrees'] = []
  try {
    const git = await $.process.run(['git', '-C', REPO, 'worktree', 'list', '--porcelain'], { timeoutMs: 10_000 })
    if (git.exitCode === 0) worktrees = parseWorktrees(git.stdout)
  } catch {
    // git missing or slow: the pane still shows the todo, with no worktrees listed
  }
  try {
    const md = await $.fs.read(TODO)
    return { ...parseTodo(md), worktrees, readAt }
  } catch (err) {
    return {
      resumeUpdated: '', resumeNext: '', beforeStarting: '', phase: '', items: [], done: 0, total: 0,
      nextStep: '', waiting: [], worktrees, readAt,
      error: `Could not read ${TODO}: ${err instanceof Error ? err.message : String(err)}`,
    }
  }
}

async function refresh($: EngineInterface): Promise<void> {
  const next = await readSnapshot($)
  const { readAt: _a, ...nextBody } = next
  await update($, snap, prev => {
    if (prev) {
      const { readAt: _b, ...prevBody } = prev
      if (JSON.stringify(prevBody) === JSON.stringify(nextBody)) return prev
    }
    return next
  })
  $.ui.status(next.error ? 'todo unreadable' : `${next.phase} · ${next.done}/${next.total}`)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'todo-status',
      description: `Open the project status pane (phase, next step, waiting on ${OWNER}, worktrees)`,
    })
    await refresh($)
    $.clock.every(REFRESH_MS, () => void refresh($))
    return next(e)
  })

  on('command.run', { command: 'todo-status' }, async $ => {
    await refresh($)
    await $.ui.open({ id: PANE, title: 'Project status' })
    return { text: 'Project status pane opened.' }
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    void refresh($)
    return result
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const s = await read($, snap)

    if (!s) return <Text dimColor>Reading {TODO_REL}…</Text>
    if (s.error) return <Text color="error">{s.error}</Text>

    return (
      <Box flexDirection="column">
        <Text bold>{s.phase}  <Text dimColor>{s.done}/{s.total} done</Text></Text>
        {s.items.map(i => (
          <Text dimColor={i.mark === 'done'} wrap="truncate-end">
            <Text color={i.mark === 'done' ? 'success' : i.mark === 'doing' ? 'warning' : 'text'}>{MARK[i.mark]}</Text> {i.text}
          </Text>
        ))}

        <Text> </Text>
        <Text bold>Next step</Text>
        <Text>{s.nextStep || '—'}</Text>

        <Text> </Text>
        <Text bold>Waiting on {OWNER}</Text>
        {s.waiting.length === 0
          ? <Text dimColor>Nothing.</Text>
          : s.waiting.map(w => <Text color="warning">• {w}</Text>)}

        <Text> </Text>
        <Text bold>Worktrees (.worktrees/)</Text>
        {s.worktrees.length === 0
          ? <Text dimColor>None open. Only main.</Text>
          : s.worktrees.map(w => <Text>• {w.name} <Text dimColor>{w.branch}</Text></Text>)}

        <Text> </Text>
        <Text bold>Resume block <Text dimColor>(updated {s.resumeUpdated || '—'})</Text></Text>
        <Text dimColor>Next: {s.resumeNext || '—'}</Text>
        {s.beforeStarting && <Text dimColor>Before starting: {s.beforeStarting}</Text>}

        <Text> </Text>
        <Box flexDirection="row">
          <Button label="Refresh" hotkey="r" onPress={() => refresh($)} />
          <Text dimColor>  read {s.readAt} UTC · auto every 30 s · read-only</Text>
        </Box>
      </Box>
    )
  })
}
