import type { ActiveTimer } from '../../App'
import { formatElapsed } from '../../App'

type Props = {
  activeTimers: ActiveTimer[]
  idleThreshold: number
  onKeepAll: () => void
  onStopAll: () => void
  onClose: () => void
}

export default function IdleDialog({ activeTimers, idleThreshold, onKeepAll, onStopAll, onClose }: Props) {
  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(3px)' }}
    >
      <div
        className="rounded-lg p-6 w-full"
        style={{
          maxWidth: 400,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          boxShadow: '0 24px 64px rgba(0,0,0,0.7)',
        }}
      >
        <div className="mb-4">
          <div className="text-xs font-semibold tracking-widest uppercase mb-2" style={{ color: 'var(--color-amber)', letterSpacing: '0.12em' }}>
            Idle Detected
          </div>
          <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--color-text)' }}>
            Still working?
          </h3>
          <p className="text-xs" style={{ color: 'var(--color-muted)' }}>
            No input has been detected for {idleThreshold} minutes. Currently tracking:
          </p>
        </div>

        {/* Active timers */}
        <div className="mb-5 flex flex-col gap-2">
          {activeTimers.length > 0 ? activeTimers.map(timer => (
            <div
              key={timer.id}
              className="flex items-center justify-between px-3 py-2 rounded"
              style={{
                background: 'var(--color-surface-raised)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: timer.projectColor }} />
                <span className="text-sm" style={{ color: 'var(--color-text)' }}>{timer.project}</span>
              </div>
              <span className="text-sm" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-muted-bright)' }}>
                {formatElapsed(timer.elapsed)}
              </span>
            </div>
          )) : (
            <div
              className="px-3 py-2 rounded"
              style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
            >
              <div className="text-sm text-center" style={{ color: 'var(--color-muted)' }}>
                No active sessions to review.
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2">
          <button
            onClick={onKeepAll}
            disabled={activeTimers.length === 0}
            className="w-full py-2.5 rounded text-sm font-semibold"
            style={{
              background: activeTimers.length > 0 ? 'var(--color-primary)' : 'var(--color-surface-raised)',
              color: activeTimers.length > 0 ? '#0C0C10' : 'var(--color-muted)',
              border: 'none',
              cursor: activeTimers.length > 0 ? 'pointer' : 'not-allowed',
            }}
          >
            Keep All Tracking
          </button>
          <div className="flex gap-2">
            <button
              onClick={onStopAll}
              disabled={activeTimers.length === 0}
              className="flex-1 py-2 rounded text-sm transition-all"
              style={{
                background: 'rgba(248,113,113,0.12)',
                color: activeTimers.length > 0 ? 'var(--color-danger)' : 'var(--color-muted)',
                border: `1px solid ${activeTimers.length > 0 ? 'rgba(248,113,113,0.2)' : 'var(--color-border)'}`,
                cursor: activeTimers.length > 0 ? 'pointer' : 'not-allowed',
              }}
            >
              Stop All Now
            </button>
            <button
              onClick={onClose}
              className="flex-1 py-2 rounded text-sm transition-all"
              style={{
                background: 'var(--color-surface-raised)',
                color: 'var(--color-muted-bright)',
                border: '1px solid var(--color-border)',
              }}
            >
              Stop at Last Activity
            </button>
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
            Review Individually
          </button>
        </div>
      </div>
    </div>
  )
}
