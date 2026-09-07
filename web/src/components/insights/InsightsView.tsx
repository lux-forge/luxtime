import { useState, type ReactNode } from 'react'
import type { ActiveTimer } from '../../App'
import type { ApiInsights, InsightPeriod } from '../../api/types'
import { formatDuration } from '../../App'
import ActiveBar from '../layout/ActiveBar'

type Period = Exclude<InsightPeriod, 'all'>

type Props = {
  insights: ApiInsights
  period: Period
  onPeriodChange: (period: Period) => void
  activeTimers: ActiveTimer[]
  onNavigateTimer: () => void
}

// ─── Data derivation ────────────────────────────────────────────────────────

type DayBucket = {
  date: string
  totalSeconds: number
  projects: { project: string; color: string; seconds: number }[]
}

type ProjectBucket = {
  project: string
  color: string
  seconds: number
  value: number
}

type WorkTypeBucket = {
  name: string
  color: string
  seconds: number
}

type LengthBucket = {
  label: string
  count: number
}

const WORK_TYPE_COLORS: Record<string, string> = {
  Development: '#34D399',
  Research: '#60A5FA',
  Design: '#F472B6',
  Operations: '#818CF8',
  Admin: '#FBBF24',
  Business: '#C084FC',
}

// ─── Chart components ────────────────────────────────────────────────────────

const BAR_HEIGHT = 120 // px

function DailyActivityChart({ days }: { days: DayBucket[] }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)

  if (days.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height: BAR_HEIGHT + 32, color: 'var(--color-muted)', fontSize: 13 }}>
        No sessions recorded
      </div>
    )
  }

  const maxSeconds = Math.max(...days.map(d => d.totalSeconds), 1)

  return (
    <div style={{ userSelect: 'none' }}>
      {/* Chart area */}
      <div className="relative flex items-end gap-1.5" style={{ height: BAR_HEIGHT }}>
        {/* Subtle gridlines */}
        {[0.25, 0.5, 0.75].map(pct => (
          <div
            key={pct}
            className="absolute inset-x-0 pointer-events-none"
            style={{
              bottom: `${pct * 100}%`,
              borderTop: '1px solid rgba(255,255,255,0.05)',
            }}
          />
        ))}

        {/* Bars */}
        {days.map((day, i) => {
          const barHeightPct = day.totalSeconds / maxSeconds
          const isHovered = hoveredIdx === i

          return (
            <div
              key={day.date}
              className="relative flex-1 flex flex-col justify-end"
              style={{ height: '100%' }}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              {/* Stacked bar */}
              <div
                className="w-full rounded-sm overflow-hidden flex flex-col-reverse transition-all"
                style={{
                  height: `${barHeightPct * 100}%`,
                  opacity: hoveredIdx !== null && !isHovered ? 0.4 : 1,
                  transition: 'opacity 0.15s',
                }}
              >
                {day.projects.map(proj => (
                  <div
                    key={proj.project}
                    style={{
                      flex: proj.seconds,
                      background: proj.color,
                      opacity: 0.8,
                    }}
                  />
                ))}
              </div>

              {/* Hover tooltip */}
              {isHovered && (
                <div
                  className="absolute bottom-full mb-2 left-1/2 z-10 rounded px-2.5 py-2 pointer-events-none"
                  style={{
                    transform: 'translateX(-50%)',
                    background: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
                    whiteSpace: 'nowrap',
                    minWidth: 140,
                  }}
                >
                  <div
                    className="font-semibold mb-1.5"
                    style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)', fontSize: 11 }}
                  >
                    {day.date} — {formatDuration(day.totalSeconds)}
                  </div>
                  {day.projects.map(p => (
                    <div key={p.project} className="flex items-center gap-2" style={{ fontSize: 11 }}>
                      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: p.color }} />
                      <span style={{ color: 'var(--color-muted-bright)' }}>{p.project}</span>
                      <span style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)', marginLeft: 'auto', paddingLeft: 8 }}>
                        {formatDuration(p.seconds)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Day labels */}
      <div className="flex gap-1.5 mt-2">
        {days.map(day => (
          <div key={day.date} className="flex-1 text-center">
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)' }}>{day.date.split(' ')[0]}</div>
            <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.2)' }}>{day.date.split(' ')[1]}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function LabourValueChart({ projects }: { projects: ProjectBucket[] }) {
  const maxValue = Math.max(...projects.map(p => p.value), 1)

  if (projects.length === 0) {
    return (
      <div className="flex items-center justify-center h-24" style={{ color: 'var(--color-muted)', fontSize: 13 }}>
        No data
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {projects.map(proj => {
        const pct = (proj.value / maxValue) * 100
        return (
          <div key={proj.project} className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 shrink-0" style={{ width: 120 }}>
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: proj.color }} />
              <span className="text-xs truncate" style={{ color: 'var(--color-muted-bright)' }}>{proj.project}</span>
            </div>
            <div className="flex-1 h-2 rounded overflow-hidden" style={{ background: 'var(--color-surface-raised)' }}>
              <div
                className="h-full rounded"
                style={{ width: `${pct}%`, background: proj.color, opacity: 0.75, transition: 'width 0.4s ease' }}
              />
            </div>
            <div className="shrink-0 text-right" style={{ width: 60 }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--color-text)' }}>
                £{proj.value.toLocaleString('en-GB', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-muted)' }}>
                {formatDuration(proj.seconds)}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function SessionLengthChart({ buckets }: { buckets: LengthBucket[] }) {
  const maxCount = Math.max(...buckets.map(b => b.count), 1)
  const HIST_HEIGHT = 80

  if (buckets.every(bin => bin.count === 0)) {
    return (
      <div className="flex items-center justify-center" style={{ height: HIST_HEIGHT + 24, color: 'var(--color-muted)', fontSize: 13 }}>
        No data
      </div>
    )
  }

  return (
    <div>
      {/* Bars */}
      <div className="flex items-end gap-2" style={{ height: HIST_HEIGHT, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        {buckets.map(bin => {
          const barPct = bin.count / maxCount
          return (
            <div
              key={bin.label}
              className="flex-1 flex flex-col justify-end items-center relative"
              style={{ height: '100%' }}
            >
              {bin.count > 0 && (
                <div
                  className="text-center mb-1"
                  style={{ fontSize: 10, color: 'var(--color-primary)', fontFamily: 'var(--font-mono)', opacity: 0.85 }}
                >
                  {bin.count}
                </div>
              )}
              <div
                className="w-full rounded-t-sm"
                style={{
                  height: `${barPct * 100}%`,
                  background: 'var(--color-primary)',
                  opacity: bin.count > 0 ? 0.55 : 0.1,
                  minHeight: bin.count > 0 ? 2 : 0,
                }}
              />
            </div>
          )
        })}
      </div>
      {/* Labels */}
      <div className="flex gap-2 mt-1.5">
        {buckets.map(bin => (
          <div
            key={bin.label}
            className="flex-1 text-center"
            style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)' }}
          >
            {bin.label}
          </div>
        ))}
      </div>
    </div>
  )
}

function HorizBar({ name, color, seconds, maxSeconds }: { name: string; color: string; seconds: number; maxSeconds: number }) {
  const pct = Math.round((seconds / maxSeconds) * 100)
  return (
    <div className="flex items-center gap-3 mb-2">
      <div className="flex items-center gap-1.5 shrink-0" style={{ width: 120 }}>
        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: color }} />
        <span className="text-xs truncate" style={{ color: 'var(--color-muted-bright)' }}>{name}</span>
      </div>
      <div className="flex-1 h-2 rounded overflow-hidden" style={{ background: 'var(--color-surface-raised)' }}>
        <div
          className="h-full rounded transition-all"
          style={{ width: `${pct}%`, background: color, opacity: 0.75 }}
        />
      </div>
      <div className="text-xs shrink-0" style={{ width: 48, textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--color-muted-bright)' }}>
        {formatDuration(seconds)}
      </div>
    </div>
  )
}

function StatTile({ label, value, sub, highlight }: { label: string; value: string; sub?: string; highlight?: boolean }) {
  return (
    <div
      className="p-4 rounded"
      style={{
        background: 'var(--color-surface-raised)',
        border: `1px solid ${highlight ? 'rgba(34,211,238,0.2)' : 'var(--color-border)'}`,
      }}
    >
      <div className="text-xs mb-1" style={{ color: 'var(--color-muted)' }}>{label}</div>
      <div
        className="text-xl font-semibold"
        style={{ fontFamily: 'var(--font-mono)', color: highlight ? 'var(--color-primary)' : 'var(--color-text)' }}
      >
        {value}
      </div>
      {sub && <div className="text-xs mt-0.5" style={{ color: 'var(--color-muted)' }}>{sub}</div>}
    </div>
  )
}

function formatInsightDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${String(minutes).padStart(2, '0')}m`
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div
      className="text-xs font-semibold tracking-widest uppercase mb-4"
      style={{ color: 'var(--color-muted)', letterSpacing: '0.1em' }}
    >
      {children}
    </div>
  )
}

// ─── Main view ────────────────────────────────────────────────────────────────

export default function InsightsView({ insights, period, onPeriodChange, activeTimers, onNavigateTimer }: Props) {
  const periods: { id: Period; label: string }[] = [
    { id: 'week', label: 'Week' },
    { id: 'month', label: 'Month' },
    { id: 'quarter', label: 'Quarter' },
    { id: 'year', label: 'Year' },
  ]

  const attributed = insights.project_attributed_seconds
  const elapsed = insights.elapsed_seconds
  const concurrentSecs = insights.concurrent_attribution_seconds
  const value = insights.notional_labour_value
  const sessions = insights.session_count
  const avg = insights.average_session_seconds
  const days: DayBucket[] = insights.days.map(day => ({
    date: new Date(`${day.date}T00:00:00`).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
    totalSeconds: day.total_seconds,
    projects: day.projects,
  }))
  const byProject: ProjectBucket[] = insights.projects
  const byWorkType: WorkTypeBucket[] = insights.work_types.map(item => ({
    ...item,
    color: WORK_TYPE_COLORS[item.name] ?? '#5A5A72',
  }))
  const lengthBuckets: LengthBucket[] = insights.session_lengths

  const maxProjectSeconds = Math.max(...byProject.map(p => p.seconds), 1)
  const maxTypeSeconds = Math.max(...byWorkType.map(t => t.seconds), 1)

  return (
    <div className="h-full flex flex-col">
      <ActiveBar activeTimers={activeTimers} onNavigateTimer={onNavigateTimer} />

      <div className="flex-1 overflow-auto px-8 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-base font-semibold" style={{ color: 'var(--color-text)' }}>Insights</h1>
          <div
            className="flex items-center gap-1 p-1 rounded"
            style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
          >
            {periods.map(p => (
              <button
                key={p.id}
                onClick={() => onPeriodChange(p.id)}
                className="px-3 py-1.5 rounded text-xs transition-all"
                style={{
                  background: period === p.id ? 'var(--color-surface-hover)' : 'transparent',
                  color: period === p.id ? 'var(--color-text)' : 'var(--color-muted)',
                  fontWeight: period === p.id ? 500 : 400,
                  border: 'none',
                }}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Stat tiles */}
        <div className="grid gap-3 mb-8" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <StatTile label="Elapsed work" value={formatInsightDuration(elapsed)} sub="Unique real-world time" />
          <StatTile label="Project-attributed work" value={formatInsightDuration(attributed)} sub="Includes concurrent overlap" />
          <StatTile label="Concurrent attribution" value={formatInsightDuration(concurrentSecs)} sub="Time attributed to 2+ projects" />
          <StatTile label="Notional labour value" value={`£${value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} highlight />
          <StatTile label="Sessions" value={String(sessions)} />
          <StatTile label="Avg session" value={formatInsightDuration(avg)} />
        </div>

        {/* Concurrent note — only when there is overlap */}
        {concurrentSecs > 0 && (
          <div
            className="flex items-start gap-2 px-4 py-3 rounded mb-8"
            style={{ background: 'rgba(251,191,36,0.07)', border: '1px solid rgba(251,191,36,0.15)' }}
          >
            <span style={{ color: 'var(--color-amber)', fontSize: 12, lineHeight: '20px' }}>ℹ</span>
            <p className="text-xs" style={{ color: 'var(--color-muted-bright)', lineHeight: '1.6' }}>
              Project-attributed work ({formatDuration(attributed)}) exceeds elapsed work ({formatDuration(elapsed)}) by{' '}
              <strong style={{ color: 'var(--color-amber)' }}>{formatDuration(concurrentSecs)}</strong> due to concurrent project tracking. This is expected.
            </p>
          </div>
        )}

        {/* Daily activity chart — full width */}
        <div
          className="mb-8 p-5 rounded"
          style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
        >
          <SectionLabel>
            {period === 'week' ? 'Daily Activity' : period === 'month' ? 'Daily Activity' : period === 'quarter' ? 'Activity by Week' : 'Activity by Month'}
          </SectionLabel>
          <DailyActivityChart days={days} />

          {/* Project legend */}
          {byProject.length > 0 && (
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-4">
              {byProject.map(p => (
                <div key={p.project} className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-sm" style={{ background: p.color, opacity: 0.8 }} />
                  <span className="text-xs" style={{ color: 'var(--color-muted)' }}>{p.project}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Lower 3-column grid */}
        <div className="grid gap-6" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          {/* Time by project (hours) */}
          <div
            className="p-5 rounded"
            style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
          >
            <SectionLabel>Time by Project</SectionLabel>
            {byProject.length > 0 ? byProject.map(p => (
              <HorizBar key={p.project} name={p.project} color={p.color} seconds={p.seconds} maxSeconds={maxProjectSeconds} />
            )) : <span className="text-xs" style={{ color: 'var(--color-muted)' }}>No data</span>}
          </div>

          {/* Labour value by project */}
          <div
            className="p-5 rounded"
            style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
          >
            <SectionLabel>Labour Value by Project</SectionLabel>
            <LabourValueChart projects={byProject} />
          </div>

          {/* Session length distribution */}
          <div
            className="p-5 rounded"
            style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
          >
            <SectionLabel>Session Length</SectionLabel>
            <SessionLengthChart buckets={lengthBuckets} />
            <div className="text-xs mt-2" style={{ color: 'var(--color-muted)' }}>
              {sessions} session{sessions !== 1 ? 's' : ''} · avg {formatDuration(avg)}
            </div>
          </div>
        </div>

        {/* Time by work type */}
        <div
          className="mt-6 p-5 rounded"
          style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
        >
          <SectionLabel>Time by Work Type</SectionLabel>
          <div className="grid gap-x-8" style={{ gridTemplateColumns: '1fr 1fr' }}>
            {byWorkType.map(t => (
              <HorizBar key={t.name} name={t.name} color={t.color} seconds={t.seconds} maxSeconds={maxTypeSeconds} />
            ))}
            {byWorkType.length === 0 && (
              <span className="text-xs" style={{ color: 'var(--color-muted)' }}>No data</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
