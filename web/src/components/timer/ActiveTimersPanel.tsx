import type { ActiveTimer } from '../../App'
import { formatElapsed, calcValue } from '../../App'

type Props = {
  timers: ActiveTimer[]
  onStop: (id: string) => void
  onAddAnother: () => void
}

function TimerRow({
  timer,
  onStop,
  isLast,
  showConnector,
  index,
  total,
}: {
  timer: ActiveTimer
  onStop: (id: string) => void
  isLast: boolean
  showConnector: boolean
  index: number
  total: number
}) {
  const isFirst = index === 0
  const multi = total > 1

  return (
    <div className="flex">
      {/* Tree connector column */}
      {multi && (
        <div className="flex flex-col items-center shrink-0" style={{ width: 28, paddingTop: 2 }}>
          {isFirst ? (
            <span style={{ color: 'var(--color-active)', fontSize: 9 }} className="pulse-dot">●</span>
          ) : (
            <span style={{ color: 'var(--color-muted)', fontSize: 12 }}>└─</span>
          )}
          {!isLast && isFirst && (
            <div className="flex-1 mt-1" style={{ borderLeft: '1px solid var(--color-border)', marginLeft: 0 }} />
          )}
        </div>
      )}

      {/* Timer card */}
      <div
        className="flex-1 rounded mb-3 p-4"
        style={{
          background: isFirst && multi ? 'rgba(52,211,153,0.06)' : 'var(--color-surface-raised)',
          border: `1px solid ${isFirst && !multi ? 'rgba(52,211,153,0.25)' : multi && isFirst ? 'rgba(52,211,153,0.2)' : 'var(--color-border)'}`,
        }}
      >
        {/* Header row */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            {!multi && (
              <span style={{ color: 'var(--color-active)', fontSize: 8 }} className="pulse-dot">●</span>
            )}
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: timer.projectColor }}
            />
            <span className="font-semibold text-sm" style={{ color: 'var(--color-text)' }}>
              {timer.project}
            </span>
          </div>

          {/* Elapsed */}
          <span
            className="text-2xl font-semibold timer-glow-green"
            style={{
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-active)',
              letterSpacing: '0.05em',
              lineHeight: 1,
            }}
          >
            {formatElapsed(timer.elapsed)}
          </span>
        </div>

        {/* Meta */}
        <div className="flex items-center gap-2 mb-1" style={{ color: 'var(--color-muted-bright)', fontSize: 12 }}>
          <span>{timer.workType}</span>
          {timer.description && (
            <>
              <span style={{ color: 'var(--color-muted)' }}>·</span>
              <span className="truncate">{timer.description}</span>
            </>
          )}
        </div>

        {/* Sub-meta */}
        <div className="flex items-center gap-3 mb-3" style={{ color: 'var(--color-muted)', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
          <span>
            Started {timer.startedAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
          </span>
          <span>·</span>
          <span>Notional value {calcValue(timer.elapsed, timer.rate)}</span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onStop(timer.id)}
            className="px-3 py-1 rounded text-xs font-medium transition-all"
            style={{
              background: 'rgba(248,113,113,0.12)',
              color: 'var(--color-danger)',
              border: '1px solid rgba(248,113,113,0.2)',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(248,113,113,0.2)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'rgba(248,113,113,0.12)')}
          >
            Stop
          </button>
          <button
            className="px-3 py-1 rounded text-xs transition-all"
            style={{
              background: 'transparent',
              color: 'var(--color-muted-bright)',
              border: '1px solid var(--color-border)',
            }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-text)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-muted-bright)')}
          >
            Edit
          </button>
          <button
            className="px-3 py-1 rounded text-xs transition-all"
            style={{
              background: 'transparent',
              color: 'var(--color-muted-bright)',
              border: '1px solid var(--color-border)',
            }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-text)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-muted-bright)')}
          >
            Add Note
          </button>
        </div>
      </div>
    </div>
  )
}

export default function ActiveTimersPanel({ timers, onStop, onAddAnother }: Props) {
  const multi = timers.length > 1

  return (
    <div className="flex flex-col h-full px-8 py-8" style={{ maxWidth: 600, margin: '0 auto' }}>
      {/* Section label */}
      <div className="flex items-center gap-3 mb-5">
        <span className="text-xs tracking-widest uppercase font-semibold" style={{ color: 'var(--color-muted)', letterSpacing: '0.12em' }}>
          Active Work
        </span>
        {multi && (
          <span
            className="text-xs px-2 py-0.5 rounded font-semibold"
            style={{
              background: 'rgba(52,211,153,0.15)',
              color: 'var(--color-active)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {timers.length} concurrent
          </span>
        )}
      </div>

      {/* Timer rows */}
      {timers.map((timer, i) => (
        <TimerRow
          key={timer.id}
          timer={timer}
          onStop={onStop}
          isLast={i === timers.length - 1}
          showConnector={multi}
          index={i}
          total={timers.length}
        />
      ))}

      {/* Add another */}
      <button
        onClick={onAddAnother}
        className="flex items-center gap-2 text-sm transition-colors mt-2"
        style={{ color: 'var(--color-muted-bright)', background: 'none', border: 'none', cursor: 'pointer' }}
        onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-primary)')}
        onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-muted-bright)')}
      >
        <span style={{ fontSize: 18, lineHeight: 1 }}>+</span>
        <span>Track Another Project</span>
      </button>
    </div>
  )
}
