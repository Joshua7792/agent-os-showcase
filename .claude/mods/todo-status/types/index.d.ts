export type Mark = 'done' | 'doing' | 'open'

export type TodoItem = { mark: Mark; text: string }

export type Worktree = { name: string; branch: string }

export type Snapshot = {
  /** Date in the "Resume here (updated …)" heading, as written. */
  resumeUpdated: string
  /** The Resume block's "Next:" bullet, as written. */
  resumeNext: string
  /** The Resume block's "Before starting:" bullet, as written. */
  beforeStarting: string
  /** Current roadmap stage: the first [~], else the first [ ]. */
  phase: string
  items: TodoItem[]
  done: number
  total: number
  /** First unticked item of the current stage. */
  nextStep: string
  /** Unticked items anywhere that wait on Joshua. */
  waiting: string[]
  worktrees: Worktree[]
  /** Set when a read failed; the other fields are then empty. */
  error: string
  readAt: string
}

declare module 'claude-code' {
  interface PluginState {
    'todo-status': { snap: Snapshot | null }
  }
}
