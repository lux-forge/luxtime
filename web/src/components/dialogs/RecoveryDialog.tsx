import type { WorkType } from '../../App'

export type RecoveredSession = {
  id: string
  project: string
  projectColor: string
  workType: WorkType
  description: string
  lastSeen: string
}

type Props = {
  sessions?: RecoveredSession[]
  onClose: () => void
  onContinue: (project: string, workType: WorkType, description: string) => void
}

export default function RecoveryDialog({ sessions = [], onClose, onContinue }: Props) {
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
          border: '1px solid rgba(251,191,36,0.3)',
          boxShadow: '0 24px 64px rgba(0,0,0,0.7)',
        }}
      >
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span style={{ color: 'var(--color-amber)', fontSize: 14 }}>⚠</span>
            <span className="text-xs font-semibold tracking-widest uppercase" style={{ color: 'var(--color-amber)', letterSpacing: '0.12em' }}>
              Session Recovery
            </span>
          </div>
          <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--color-text)' }}>
            {sessions.length === 1
              ? 'LuxTime recovered an unfinished session'
              : sessions.length > 1
                ? 'LuxTime recovered unfinished sessions'
                : 'No unfinished sessions were recovered'}
          </h3>
          <p className="text-xs" style={{ color: 'var(--color-muted)' }}>
            {sessions.length > 0
              ? 'LuxTime shut down unexpectedly. What happened to these sessions?'
              : 'There is no recovered work to review.'}
          </p>
        </div>

        {/* Recovered sessions */}
        <div className="flex flex-col gap-3 mb-5">
          {sessions.map(session => (
            <div
              key={session.id}
              className="rounded p-3"
              style={{
                background: 'var(--color-surface-raised)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full" style={{ background: session.projectColor }} />
                <span className="text-sm font-medium" style={{ color: 'var(--color-text)' }}>
                  {session.project}
                </span>
              </div>
              <div className="text-xs mb-2" style={{ color: 'var(--color-muted-bright)' }}>
                {session.workType}{session.description ? ` · ${session.description}` : ''}
              </div>
              <div className="text-xs mb-3" style={{ color: 'var(--color-muted)', fontFamily: 'var(--font-mono)' }}>
                Last confirmed active: {session.lastSeen}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={onClose}
                  className="flex-1 py-1.5 rounded text-xs transition-all"
                  style={{
                    background: 'var(--color-surface)',
                    color: 'var(--color-muted-bright)',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  Accept {session.lastSeen}
                </button>
                <button
                  onClick={() => onContinue(session.project, session.workType, session.description)}
                  className="flex-1 py-1.5 rounded text-xs"
                  style={{
                    background: 'rgba(34,211,238,0.12)',
                    color: 'var(--color-primary)',
                    border: '1px solid rgba(34,211,238,0.25)',
                  }}
                >
                  Continue Timer
                </button>
                <button
                  onClick={onClose}
                  className="px-2.5 py-1.5 rounded text-xs"
                  style={{
                    background: 'transparent',
                    color: 'var(--color-muted)',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  Edit
                </button>
              </div>
            </div>
          ))}
          {sessions.length === 0 && (
            <div
              className="p-3 rounded text-sm text-center"
              style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}
            >
              No recovered sessions.
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 rounded text-sm"
          style={{
            background: 'transparent',
            color: 'var(--color-muted)',
            border: '1px solid var(--color-border)',
          }}
        >
          Dismiss All
        </button>
      </div>
    </div>
  )
}
