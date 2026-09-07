import type { View, ActiveTimer, ApplicationStatus } from '../../App'
import { formatElapsed } from '../../App'

type NavItem = { id: View; label: string; icon: string }

const NAV: NavItem[] = [
  { id: 'timer', label: 'Timer', icon: '⏱' },
  { id: 'history', label: 'History', icon: '◷' },
  { id: 'projects', label: 'Projects', icon: '◈' },
  { id: 'insights', label: 'Insights', icon: '◻' },
  { id: 'settings', label: 'Settings', icon: '⚙' },
]

type Props = {
  view: View
  setView: (v: View) => void
  activeTimers: ActiveTimer[]
  appStatus: ApplicationStatus
}

export default function AppShell({ view, setView, activeTimers, appStatus }: Props) {
  const isTracking = activeTimers.length > 0
  const statusLabel = {
    connecting: 'Engine connecting',
    unavailable: 'Engine unavailable',
    degraded: 'Engine degraded',
    ready: 'Engine ready',
    tracking: 'Engine tracking',
    paused: 'Tracking paused',
  }[appStatus]
  const statusColor = appStatus === 'tracking'
    ? 'var(--color-active)'
    : appStatus === 'paused'
      ? 'var(--color-amber)'
      : appStatus === 'ready'
        ? 'var(--color-primary)'
        : 'var(--color-danger)'

  return (
    <aside
      className="flex flex-col shrink-0 select-none"
      style={{
        width: 176,
        background: 'var(--color-surface)',
        borderRight: '1px solid var(--color-border)',
      }}
    >
      {/* Logo */}
      <div className="px-4 pt-5 pb-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
        <div className="text-xs font-semibold tracking-widest uppercase" style={{ color: 'var(--color-muted)', letterSpacing: '0.15em' }}>
          LuxForge
        </div>
        <div className="text-sm font-semibold mt-0.5" style={{ color: 'var(--color-text)' }}>
          LuxTime
        </div>
      </div>

      {/* Active tracking compact info */}
      {isTracking && (
        <div
          className="px-4 py-3 cursor-pointer"
          style={{ borderBottom: '1px solid var(--color-border)', background: 'rgba(52,211,153,0.05)' }}
          onClick={() => setView('timer')}
        >
          <div className="flex items-center gap-1.5 mb-1">
            <span className={activeTimers.some(timer => timer.status === 'running') ? 'pulse-dot' : ''} style={{ color: statusColor, fontSize: 8 }}>●</span>
            <span className="text-xs font-medium" style={{ color: statusColor }}>
              {activeTimers.length === 1 ? activeTimers[0].project : `${activeTimers.length} sessions`}
            </span>
          </div>
          {activeTimers.map(t => (
            <div key={t.id} className="flex items-center justify-between">
              {activeTimers.length > 1 && (
                <span className="text-xs truncate" style={{ color: 'var(--color-muted-bright)', maxWidth: 80 }}>
                  {t.project}
                </span>
              )}
              <span className="text-xs" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-active)' }}>
                {t.status === 'paused' ? 'Paused · ' : ''}{formatElapsed(t.elapsed)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 py-3">
        {NAV.map(item => {
          const active = view === item.id
          return (
            <button
              key={item.id}
              onClick={() => setView(item.id)}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors"
              style={{
                color: active ? 'var(--color-primary)' : 'var(--color-muted-bright)',
                background: active ? 'rgba(34,211,238,0.07)' : 'transparent',
                borderLeft: active ? '2px solid var(--color-primary)' : '2px solid transparent',
                fontSize: 13,
                fontWeight: active ? 500 : 400,
              }}
            >
              <span style={{ fontSize: 14, opacity: active ? 1 : 0.7 }}>{item.icon}</span>
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* Engine status */}
      <div className="px-4 py-4" style={{ borderTop: '1px solid var(--color-border)' }}>
        <div className="flex items-center gap-2 mb-1">
          <span style={{ color: statusColor, fontSize: 8 }}>●</span>
          <span className="text-xs" style={{ color: 'var(--color-muted-bright)', fontSize: 11 }}>{statusLabel}</span>
        </div>
      </div>
    </aside>
  )
}
