import type { ActiveTimer } from '../../App'
import { formatElapsed } from '../../App'

type Props = {
  activeTimers: ActiveTimer[]
  onNavigateTimer: () => void
}

export default function ActiveBar({ activeTimers, onNavigateTimer }: Props) {
  if (activeTimers.length === 0) return null

  const isMulti = activeTimers.length > 1

  return (
    <div
      className="flex items-center gap-3 px-6 py-2.5 cursor-pointer transition-colors"
      style={{
        background: 'rgba(52,211,153,0.07)',
        borderBottom: '1px solid rgba(52,211,153,0.15)',
      }}
      onClick={onNavigateTimer}
      title="Return to Timer"
    >
      <span className="pulse-dot" style={{ color: 'var(--color-active)', fontSize: 8 }}>●</span>
      {isMulti ? (
        <>
          <span className="text-xs font-semibold" style={{ color: 'var(--color-active)' }}>
            {activeTimers.length} projects active
          </span>
          <span style={{ color: 'var(--color-border)', fontSize: 10 }}>·</span>
          {activeTimers.map((t, i) => (
            <span key={t.id} className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--color-muted-bright)' }}>
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: t.projectColor }} />
              <span>{t.project}</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-active)' }}>
                {formatElapsed(t.elapsed)}
              </span>
              {i < activeTimers.length - 1 && <span style={{ color: 'var(--color-border)', marginLeft: 4 }}>·</span>}
            </span>
          ))}
        </>
      ) : (
        <>
          <span className="flex items-center gap-1.5 text-xs">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: activeTimers[0].projectColor }} />
            <span style={{ color: 'var(--color-active)', fontWeight: 500 }}>{activeTimers[0].project}</span>
          </span>
          <span style={{ color: 'var(--color-border)', fontSize: 10 }}>·</span>
          <span className="text-xs" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-active)' }}>
            {formatElapsed(activeTimers[0].elapsed)}
          </span>
        </>
      )}
      <span className="ml-auto text-xs" style={{ color: 'var(--color-muted)', opacity: 0.7 }}>↩ Timer</span>
    </div>
  )
}
