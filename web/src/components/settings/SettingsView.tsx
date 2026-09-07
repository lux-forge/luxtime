import type { ReactNode } from 'react'
import type { Settings, ActiveTimer } from '../../App'
import ActiveBar from '../layout/ActiveBar'

type Props = {
  settings: Settings
  setSettings: (s: Settings) => void
  activeTimers: ActiveTimer[]
  onNavigateTimer: () => void
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="relative shrink-0"
      style={{
        width: 36,
        height: 20,
        borderRadius: 10,
        background: checked ? 'var(--color-active)' : 'var(--color-surface-raised)',
        border: `1px solid ${checked ? 'var(--color-active)' : 'var(--color-border)'}`,
        cursor: 'pointer',
        transition: 'background 0.2s',
      }}
    >
      <span
        style={{
          position: 'absolute',
          top: 2,
          left: checked ? 16 : 2,
          width: 14,
          height: 14,
          borderRadius: 7,
          background: checked ? '#0C0C10' : 'var(--color-muted)',
          transition: 'left 0.2s',
        }}
      />
    </button>
  )
}

function SettingRow({ label, sub, children }: { label: string; sub?: string; children: React.ReactNode }) {
  return (
    <div
      className="flex items-center justify-between py-3"
      style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
    >
      <div>
        <div className="text-sm" style={{ color: 'var(--color-text)' }}>{label}</div>
        {sub && <div className="text-xs mt-0.5" style={{ color: 'var(--color-muted)' }}>{sub}</div>}
      </div>
      <div className="ml-8 shrink-0">{children}</div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mb-8">
      <div
        className="text-xs font-semibold tracking-widest uppercase mb-3 pb-2"
        style={{
          color: 'var(--color-muted)',
          letterSpacing: '0.12em',
          borderBottom: '1px solid var(--color-border)',
        }}
      >
        {title}
      </div>
      {children}
    </div>
  )
}

export default function SettingsView({ settings, setSettings, activeTimers, onNavigateTimer }: Props) {
  function update<K extends keyof Settings>(key: K, value: Settings[K]) {
    setSettings({ ...settings, [key]: value })
  }

  return (
    <div className="h-full flex flex-col">
      <ActiveBar activeTimers={activeTimers} onNavigateTimer={onNavigateTimer} />

      <div className="flex-1 overflow-auto px-8 py-6" style={{ maxWidth: 640 }}>
        <h1 className="text-base font-semibold mb-8" style={{ color: 'var(--color-text)' }}>Settings</h1>

        {/* Time Valuation */}
        <Section title="Time Valuation">
          <div className="py-3">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-sm" style={{ color: 'var(--color-text)' }}>Default internal hourly rate</span>
              <div
                className="flex items-center gap-1 px-3 py-1.5 rounded"
                style={{
                  background: 'var(--color-surface-raised)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <span className="text-sm" style={{ color: 'var(--color-muted)' }}>£</span>
                <input
                  type="number"
                  value={settings.defaultRate}
                  onChange={e => update('defaultRate', Number(e.target.value))}
                  className="bg-transparent outline-none text-sm w-16"
                  style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}
                />
                <span className="text-xs" style={{ color: 'var(--color-muted)' }}>/ hour</span>
              </div>
            </div>
            <p className="text-xs" style={{ color: 'var(--color-muted)', lineHeight: '1.6', maxWidth: 480 }}>
              This is an internal valuation of founder labour. It does not represent payroll, salary or money owed by LuxForge.
              Historic sessions retain their recorded rate.
            </p>
          </div>
        </Section>

        {/* Automatic Tracking */}
        <Section title="Automatic Tracking">
          <SettingRow
            label="Stop active timers when Windows locks"
            sub="All active sessions stop using the lock timestamp"
          >
            <Toggle checked={settings.stopOnLock} onChange={v => update('stopOnLock', v)} />
          </SettingRow>
          <SettingRow
            label="Stop active timers when the computer sleeps"
            sub="Also applies on hibernate"
          >
            <Toggle checked={settings.stopOnSleep} onChange={v => update('stopOnSleep', v)} />
          </SettingRow>
          <SettingRow
            label="Ask which previous projects to resume on unlock"
            sub="Works with multiple concurrent projects"
          >
            <Toggle checked={settings.resumePrompt} onChange={v => update('resumePrompt', v)} />
          </SettingRow>
        </Section>

        {/* Idle Detection */}
        <Section title="Idle Detection">
          <SettingRow label="Detect when I appear inactive">
            <Toggle checked={settings.idleDetection} onChange={v => update('idleDetection', v)} />
          </SettingRow>
          <div className="py-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
            <div className="flex items-center gap-3">
              <span className="text-sm" style={{ color: settings.idleDetection ? 'var(--color-text)' : 'var(--color-muted)' }}>
                Idle threshold
              </span>
              <div
                className="flex items-center gap-2 px-3 py-1.5 rounded"
                style={{
                  background: 'var(--color-surface-raised)',
                  border: '1px solid var(--color-border)',
                  opacity: settings.idleDetection ? 1 : 0.4,
                }}
              >
                <input
                  type="number"
                  value={settings.idleThreshold}
                  onChange={e => update('idleThreshold', Number(e.target.value))}
                  disabled={!settings.idleDetection}
                  className="bg-transparent outline-none text-sm w-12"
                  style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}
                />
                <span className="text-xs" style={{ color: 'var(--color-muted)' }}>minutes</span>
              </div>
              <span className="text-xs" style={{ color: 'var(--color-muted)' }}>then: ask what to do</span>
            </div>
          </div>
        </Section>

        {/* Startup & Background */}
        <Section title="Startup & Background">
          <SettingRow
            label="LuxTime Engine starts with Windows"
            sub="Recommended — tracking continues even when the UI is closed"
          >
            <Toggle checked={settings.engineStartsWithWindows} onChange={v => update('engineStartsWithWindows', v)} />
          </SettingRow>
          <div className="py-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
            <div className="text-sm mb-3" style={{ color: 'var(--color-text)' }}>Open LuxTime when I sign in</div>
            <div className="flex flex-col gap-2">
              {(['tray', 'compact', 'window'] as const).map(opt => (
                <label key={opt} className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="radio"
                    name="startupBehaviour"
                    checked={settings.startupBehaviour === opt}
                    onChange={() => update('startupBehaviour', opt)}
                    style={{ accentColor: 'var(--color-primary)' }}
                  />
                  <span className="text-sm" style={{ color: 'var(--color-muted-bright)' }}>
                    {opt === 'tray' && 'Start in tray and show "What are you working on?" prompt'}
                    {opt === 'compact' && 'Start minimised to tray only'}
                    {opt === 'window' && 'Open main LuxTime window'}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </Section>

        {/* Engine Health */}
        <Section title="Engine Health">
          <div className="py-3">
            <div className="flex items-center gap-2 mb-2">
              <span style={{ color: 'var(--color-muted)', fontSize: 8 }}>●</span>
              <span className="text-sm font-medium" style={{ color: 'var(--color-muted-bright)' }}>
                LuxTime Engine not connected
              </span>
            </div>
            <p className="text-xs mb-3" style={{ color: 'var(--color-muted)' }}>
              Background engine integration is not configured in this frontend baseline.
            </p>
            <div className="flex gap-2">
              <button
                disabled
                className="px-3 py-1.5 rounded text-xs"
                style={{
                  background: 'var(--color-surface-raised)',
                  color: 'var(--color-muted)',
                  border: '1px solid var(--color-border)',
                  cursor: 'not-allowed',
                }}
              >
                View Engine Log
              </button>
              <button
                disabled
                className="px-3 py-1.5 rounded text-xs"
                style={{
                  background: 'transparent',
                  color: 'var(--color-muted)',
                  border: '1px solid var(--color-border)',
                  cursor: 'not-allowed',
                }}
              >
                Restart Engine
              </button>
            </div>
          </div>
        </Section>
      </div>
    </div>
  )
}
