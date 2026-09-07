import { useState } from 'react'
import type { HistoryEntry, ActiveTimer } from '../../App'
import { formatDuration, calcValue } from '../../App'
import ActiveBar from '../layout/ActiveBar'

type Period = 'today' | 'week' | 'month' | 'custom'

type Props = {
  history: HistoryEntry[]
  activeTimers: ActiveTimer[]
  onNavigateTimer: () => void
}

export default function HistoryView({ history, activeTimers, onNavigateTimer }: Props) {
  const [period, setPeriod] = useState<Period>('week')
  const [hoveredRow, setHoveredRow] = useState<string | null>(null)

  const periods: { id: Period; label: string }[] = [
    { id: 'today', label: 'Today' },
    { id: 'week', label: 'This Week' },
    { id: 'month', label: 'This Month' },
    { id: 'custom', label: 'Custom' },
  ]

  const totalValue = history.reduce((sum, e) => sum + (e.durationSeconds / 3600) * e.rate, 0)
  const totalTime = history.reduce((sum, e) => sum + e.durationSeconds, 0)

  return (
    <div className="h-full flex flex-col">
      <ActiveBar activeTimers={activeTimers} onNavigateTimer={onNavigateTimer} />

      <div className="flex-1 overflow-auto px-8 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-base font-semibold" style={{ color: 'var(--color-text)' }}>History</h1>
          <div className="flex items-center gap-3">
            <button
              className="px-3 py-1.5 rounded text-xs transition-all"
              style={{
                background: 'var(--color-surface-raised)',
                color: 'var(--color-muted-bright)',
                border: '1px solid var(--color-border)',
              }}
            >
              Export CSV
            </button>
            <button
              className="px-3 py-1.5 rounded text-xs transition-all"
              style={{
                background: 'rgba(34,211,238,0.12)',
                color: 'var(--color-primary)',
                border: '1px solid rgba(34,211,238,0.25)',
              }}
            >
              + Add Manual Entry
            </button>
          </div>
        </div>

        {/* Period filter */}
        <div className="flex items-center gap-1 mb-6 p-1 rounded inline-flex" style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)', display: 'inline-flex' }}>
          {periods.map(p => (
            <button
              key={p.id}
              onClick={() => setPeriod(p.id)}
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

        {/* Summary row */}
        <div className="flex items-center gap-6 mb-5 px-1">
          <div>
            <div className="text-xs mb-0.5" style={{ color: 'var(--color-muted)' }}>Sessions</div>
            <div className="text-sm font-semibold" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}>{history.length}</div>
          </div>
          <div>
            <div className="text-xs mb-0.5" style={{ color: 'var(--color-muted)' }}>Total time</div>
            <div className="text-sm font-semibold" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}>{formatDuration(totalTime)}</div>
          </div>
          <div>
            <div className="text-xs mb-0.5" style={{ color: 'var(--color-muted)' }}>Notional labour value</div>
            <div className="text-sm font-semibold" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}>£{totalValue.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>
          <div className="ml-auto">
            {history.some(e => e.concurrent) && (
              <span className="text-xs px-2 py-1 rounded" style={{ background: 'rgba(251,191,36,0.1)', color: 'var(--color-amber)', border: '1px solid rgba(251,191,36,0.2)' }}>
                Contains concurrent sessions
              </span>
            )}
          </div>
        </div>

        {/* Table */}
        <div className="rounded overflow-hidden" style={{ border: '1px solid var(--color-border)' }}>
          {/* Table header */}
          <div
            className="grid text-xs font-medium px-4 py-2"
            style={{
              gridTemplateColumns: '70px 52px 52px 60px 1fr 90px 1fr 70px 60px 70px 40px',
              background: 'var(--color-surface)',
              borderBottom: '1px solid var(--color-border)',
              color: 'var(--color-muted)',
              gap: '0 8px',
            }}
          >
            <span>Date</span>
            <span>Start</span>
            <span>End</span>
            <span>Duration</span>
            <span>Project</span>
            <span>Type</span>
            <span>Description</span>
            <span>Stop</span>
            <span>Rate</span>
            <span>Value</span>
            <span />
          </div>

          {/* Rows */}
          {history.map(entry => (
            <div
              key={entry.id}
              className="grid px-4 py-2.5 text-xs transition-colors cursor-default relative"
              style={{
                gridTemplateColumns: '70px 52px 52px 60px 1fr 90px 1fr 70px 60px 70px 40px',
                background: hoveredRow === entry.id ? 'var(--color-surface-raised)' : 'transparent',
                borderBottom: '1px solid var(--color-border-subtle)',
                gap: '0 8px',
                alignItems: 'center',
              }}
              onMouseEnter={() => setHoveredRow(entry.id)}
              onMouseLeave={() => setHoveredRow(null)}
            >
              <span style={{ color: 'var(--color-muted-bright)', fontFamily: 'var(--font-mono)' }}>{entry.date}</span>
              <span style={{ color: 'var(--color-muted-bright)', fontFamily: 'var(--font-mono)' }}>
                {entry.start}
                {entry.concurrent && (
                  <span title="Concurrent session" style={{ color: 'var(--color-amber)', marginLeft: 3 }}>↕</span>
                )}
              </span>
              <span style={{ color: 'var(--color-muted-bright)', fontFamily: 'var(--font-mono)' }}>{entry.end}</span>
              <span style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
                {formatDuration(entry.durationSeconds)}
              </span>
              <span className="flex items-center gap-1.5 truncate">
                <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: entry.projectColor }} />
                <span style={{ color: 'var(--color-text)' }}>{entry.project}</span>
              </span>
              <span style={{ color: 'var(--color-muted-bright)' }}>{entry.workType}</span>
              <span className="truncate" style={{ color: 'var(--color-muted-bright)' }}>{entry.description}</span>
              <span style={{ color: 'var(--color-muted)' }}>{entry.stopReason}</span>
              <span style={{ color: 'var(--color-muted)', fontFamily: 'var(--font-mono)' }}>£{entry.rate}/hr</span>
              <span style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}>{calcValue(entry.durationSeconds, entry.rate)}</span>
              <span
                className="flex items-center gap-1"
                style={{ opacity: hoveredRow === entry.id ? 1 : 0, transition: 'opacity 0.15s' }}
              >
                <button
                  className="p-0.5 rounded"
                  style={{ color: 'var(--color-muted)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 12 }}
                  title="Edit"
                >
                  ✎
                </button>
                <button
                  className="p-0.5 rounded"
                  style={{ color: 'var(--color-danger)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 12 }}
                  title="Delete"
                >
                  ×
                </button>
              </span>
            </div>
          ))}
          {history.length === 0 && (
            <div className="px-4 py-12 text-center text-sm" style={{ color: 'var(--color-muted)' }}>
              No tracked sessions yet.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
