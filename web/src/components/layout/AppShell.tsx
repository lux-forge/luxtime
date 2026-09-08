import type { View, ActiveTimer } from '../../App'
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
  applicationName: string
  onPause: (id: string) => void
  onResume: (id: string) => void
}

type IconProps = { size?: number }

function PauseIcon({ size = 12 }: IconProps) {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" width={size} height={size} fill="currentColor">
      <rect x="3" y="2.5" width="3.5" height="11" rx="0.75" />
      <rect x="9.5" y="2.5" width="3.5" height="11" rx="0.75" />
    </svg>
  )
}

function PlayIcon({ size = 12 }: IconProps) {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" width={size} height={size} fill="currentColor">
      <path d="M4 2.75a1 1 0 0 1 1.52-.85l8 5.25a1 1 0 0 1 0 1.7l-8 5.25A1 1 0 0 1 4 13.25V2.75Z" />
    </svg>
  )
}

function SleepIcon({ size = 12 }: IconProps) {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" width={size} height={size} fill="currentColor">
      <path d="M11.7 11.55A5.6 5.6 0 0 1 5.16 4.2a5.6 5.6 0 1 0 6.54 7.35Z" />
      <path d="M9.5 2h4v1.2l-2.25 2.6h2.35V7h-4.2V5.8l2.25-2.6H9.5V2Z" />
    </svg>
  )
}

function AwayIcon({ size = 12 }: IconProps) {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="4" r="2" />
      <path d="M2.75 13c.35-2.5 1.45-4 3.25-4s2.9 1.5 3.25 4M11 8h3M12.5 6.5 14 8l-1.5 1.5" />
    </svg>
  )
}

export default function AppShell({ view, setView, activeTimers, applicationName, onPause, onResume }: Props) {
  const isTracking = activeTimers.length > 0

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
          {applicationName}
        </div>
      </div>

      {/* Active task cards */}
      {isTracking && (
        <div
          className="px-3 py-3"
          style={{ borderBottom: '1px solid var(--color-border)' }}
        >
          <div
            className="px-1 mb-2 uppercase"
            style={{ color: 'var(--color-muted)', fontSize: 9, letterSpacing: '0.12em', fontWeight: 600 }}
          >
            {activeTimers.length === 1 ? 'Active task' : `${activeTimers.length} active tasks`}
          </div>
          <div className="flex flex-col gap-2">
            {activeTimers.map(timer => {
              const isPaused = timer.status === 'paused'
              const mode = isPaused ? timer.pauseMode ?? 'manual' : 'running'
              const presentation = {
                running: { label: 'Running', accent: 'var(--color-active)', background: <PlayIcon size={48} /> },
                manual: { label: 'Paused', accent: 'var(--color-amber)', background: <PauseIcon size={48} /> },
                sleep: { label: 'Sleeping', accent: '#60A5FA', background: <SleepIcon size={48} /> },
                away: { label: 'Away', accent: '#F59E0B', background: <AwayIcon size={48} /> },
              }[mode]
              return (
                <div
                  key={timer.id}
                  className="relative overflow-hidden rounded px-2.5 py-2 cursor-pointer transition-colors"
                  style={{
                    background: `color-mix(in srgb, ${presentation.accent} 7%, var(--color-surface-raised))`,
                    border: `1px solid color-mix(in srgb, ${presentation.accent} 22%, var(--color-border))`,
                  }}
                  onClick={() => setView('timer')}
                  title={`Open Timer — ${presentation.label}`}
                >
                  <span
                    className="absolute pointer-events-none"
                    style={{
                      color: presentation.accent,
                      opacity: 0.1,
                      right: 28,
                      top: 3,
                      transform: 'rotate(-7deg)',
                    }}
                  >
                    {presentation.background}
                  </span>
                  <div className="relative flex items-center gap-2 min-w-0" style={{ zIndex: 1 }}>
                    <span
                      className={`w-1.5 h-1.5 rounded-full shrink-0 ${mode === 'running' ? 'pulse-dot' : ''}`}
                      style={{ background: timer.projectColor }}
                    />
                    <span className="text-xs font-medium truncate flex-1" style={{ color: 'var(--color-text)' }}>
                      {timer.project}
                    </span>
                    <button
                      type="button"
                      className="w-6 h-6 rounded flex items-center justify-center shrink-0 transition-colors"
                      style={{
                        color: isPaused ? 'var(--color-active)' : 'var(--color-amber)',
                        background: isPaused ? 'rgba(52,211,153,0.12)' : 'rgba(251,191,36,0.12)',
                        border: `1px solid ${isPaused ? 'rgba(52,211,153,0.2)' : 'rgba(251,191,36,0.2)'}`,
                      }}
                      aria-label={`${isPaused ? 'Resume' : 'Pause'} ${timer.project}`}
                      title={isPaused ? 'Resume task' : 'Pause task'}
                      onClick={event => {
                        event.stopPropagation()
                        if (isPaused) onResume(timer.id)
                        else onPause(timer.id)
                      }}
                    >
                      {isPaused ? <PlayIcon /> : <PauseIcon />}
                    </button>
                  </div>
                  <div
                    className="relative mt-1.5 pl-3.5 text-xs flex items-center gap-1.5"
                    style={{ fontFamily: 'var(--font-mono)', color: presentation.accent, zIndex: 1 }}
                  >
                    <span>{formatElapsed(timer.elapsed)}</span>
                    <span style={{ fontFamily: 'var(--font-sans)', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      {presentation.label}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
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
                background: active ? 'var(--color-primary-subtle)' : 'transparent',
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

    </aside>
  )
}
