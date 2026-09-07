import { useState } from 'react'
import type { WorkType } from '../../App'
import { formatDuration } from '../../App'

export type PreviousSession = {
  id: string
  project: string
  projectColor: string
  workType: WorkType
  description: string
  durationSeconds: number
}

type Props = {
  sessions?: PreviousSession[]
  lockedAt?: string
  onClose: () => void
  onResume: (items: { project: string; workType: WorkType; description: string }[]) => void
}

export default function ResumeDialog({ sessions = [], lockedAt, onClose, onResume }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set(sessions.map(s => s.id)))

  function toggleSession(id: string) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function handleResume() {
    const items = sessions
      .filter(s => selected.has(s.id))
      .map(s => ({ project: s.project, workType: s.workType, description: s.description }))
    onResume(items)
  }

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(3px)' }}
    >
      <div
        className="rounded-lg p-6 w-full"
        style={{
          maxWidth: 420,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          boxShadow: '0 24px 64px rgba(0,0,0,0.7)',
        }}
      >
        {/* Header */}
        <div className="mb-1">
          <div className="text-xs font-semibold tracking-widest uppercase mb-2" style={{ color: 'var(--color-primary)', letterSpacing: '0.12em' }}>
            Welcome back
          </div>
          <h3 className="text-base font-semibold" style={{ color: 'var(--color-text)' }}>
            {lockedAt ? `Your computer locked at ${lockedAt}.` : 'No resumable sessions were found.'}
          </h3>
          <p className="text-xs mt-1" style={{ color: 'var(--color-muted)' }}>
            {sessions.length > 0 ? 'Previously tracking:' : 'There is no previous work to resume.'}
          </p>
        </div>

        {/* Sessions */}
        <div className="mt-4 mb-5 flex flex-col gap-2">
          {sessions.map(session => (
            <label
              key={session.id}
              className="flex items-start gap-3 p-3 rounded cursor-pointer transition-colors"
              style={{
                background: selected.has(session.id) ? 'rgba(52,211,153,0.07)' : 'var(--color-surface-raised)',
                border: `1px solid ${selected.has(session.id) ? 'rgba(52,211,153,0.2)' : 'var(--color-border)'}`,
              }}
            >
              <input
                type="checkbox"
                checked={selected.has(session.id)}
                onChange={() => toggleSession(session.id)}
                className="mt-0.5"
                style={{ accentColor: 'var(--color-active)' }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: session.projectColor }} />
                  <span className="text-sm font-medium" style={{ color: 'var(--color-text)' }}>
                    {session.project}
                  </span>
                </div>
                <div className="text-xs truncate" style={{ color: 'var(--color-muted-bright)' }}>
                  {session.workType}{session.description ? ` · ${session.description}` : ''}
                </div>
              </div>
              <span
                className="text-sm shrink-0"
                style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-active)' }}
              >
                {formatDuration(session.durationSeconds)}
              </span>
            </label>
          ))}
          {sessions.length === 0 && (
            <div
              className="p-3 rounded text-sm text-center"
              style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}
            >
              No previous sessions to resume.
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2">
          <button
            onClick={handleResume}
            disabled={selected.size === 0}
            className="w-full py-2.5 rounded text-sm font-semibold transition-all"
            style={{
              background: selected.size > 0 ? 'var(--color-active)' : 'var(--color-surface-raised)',
              color: selected.size > 0 ? '#0C0C10' : 'var(--color-muted)',
              border: 'none',
              cursor: selected.size > 0 ? 'pointer' : 'not-allowed',
            }}
          >
            Resume Selected
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 py-2 rounded text-sm transition-all"
              style={{
                background: 'var(--color-surface-raised)',
                color: 'var(--color-muted-bright)',
                border: '1px solid var(--color-border)',
              }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-text)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-muted-bright)')}
            >
              Start Something Else
            </button>
            <button
              onClick={onClose}
              className="flex-1 py-2 rounded text-sm transition-all"
              style={{
                background: 'transparent',
                color: 'var(--color-muted)',
                border: '1px solid var(--color-border)',
              }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-muted-bright)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-muted)')}
            >
              Not Working
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
