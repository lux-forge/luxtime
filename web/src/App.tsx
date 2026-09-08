import { useCallback, useEffect, useState } from 'react'
import { api } from './api/client'
import type { ApiInsights, ApiProject, ApiSession, ApiSettings, ApiStatus, InsightPeriod } from './api/types'
import AppShell from './components/layout/AppShell'
import TimerView from './components/timer/TimerView'
import HistoryView from './components/history/HistoryView'
import InsightsView from './components/insights/InsightsView'
import ProjectsView from './components/projects/ProjectsView'
import SettingsView from './components/settings/SettingsView'
import AddProjectOverlay from './components/dialogs/AddProjectOverlay'

export type View = 'timer' | 'history' | 'projects' | 'insights' | 'settings'
export type WorkType = 'Development' | 'Design' | 'Research' | 'Operations' | 'Admin' | 'Business'
export type Dialog = 'none' | 'addProject'
export type ApplicationStatus = ApiStatus['app_status'] | 'connecting' | 'unavailable'

export type ActiveTimer = {
  id: string
  projectId: string
  project: string
  projectColor: string
  workType: WorkType
  description: string
  startedAt: Date
  elapsed: number
  rate: number
  status: 'running' | 'paused'
  pauseMode: 'manual' | 'away' | 'sleep' | 'lock' | null
}

export type HistoryEntry = {
  id: string
  startedAt: Date
  date: string
  start: string
  end: string
  durationSeconds: number
  project: string
  projectColor: string
  workType: WorkType
  description: string
  stopReason: string
  rate: number
  concurrent: boolean
}

export type Project = {
  id: string
  name: string
  code: string
  color: string
  totalSeconds: number
  active: boolean
}

export type Settings = {
  applicationName: string
  accentColor: string
  defaultRate: number
  stopOnLock: boolean
  stopOnSleep: boolean
  resumePrompt: boolean
  idleDetection: boolean
  idleThreshold: number
  engineStartsWithWindows: boolean
  startupBehaviour: 'tray' | 'compact' | 'window'
}

export const WORK_TYPES: WorkType[] = ['Development', 'Design', 'Research', 'Operations', 'Admin', 'Business']

export function formatElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

export function calcValue(seconds: number, rate: number): string {
  return `£${((seconds / 3600) * rate).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const toProject = (project: ApiProject): Project => ({
  id: project.id,
  name: project.name,
  code: project.code ?? '',
  color: project.color,
  totalSeconds: project.total_seconds,
  active: project.active,
})

const toActiveTimer = (session: ApiSession): ActiveTimer => ({
  id: session.id,
  projectId: session.project_id,
  project: session.project,
  projectColor: session.project_color,
  workType: session.work_type,
  description: session.description,
  startedAt: new Date(session.started_at),
  elapsed: session.total_seconds,
  rate: Number(session.hourly_rate),
  status: session.status === 'paused' ? 'paused' : 'running',
  pauseMode: session.pause_mode,
})

const toHistoryEntry = (session: ApiSession): HistoryEntry => {
  const startedAt = new Date(session.started_at)
  const stoppedAt = session.stopped_at ? new Date(session.stopped_at) : null
  return {
    id: session.id,
    startedAt,
    date: startedAt.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
    start: startedAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    end: stoppedAt?.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) ?? '—',
    durationSeconds: session.total_seconds,
    project: session.project,
    projectColor: session.project_color,
    workType: session.work_type,
    description: session.description,
    stopReason: session.stop_reason
      ? session.stop_reason.charAt(0).toUpperCase() + session.stop_reason.slice(1)
      : '—',
    rate: Number(session.hourly_rate),
    concurrent: session.concurrent,
  }
}

const toSettings = (settings: ApiSettings): Settings => ({
  applicationName: settings.application_name,
  accentColor: settings.accent_color,
  defaultRate: Number(settings.default_rate),
  stopOnLock: settings.stop_on_lock,
  stopOnSleep: settings.stop_on_sleep,
  resumePrompt: settings.resume_prompt,
  idleDetection: settings.idle_detection,
  idleThreshold: settings.idle_threshold,
  engineStartsWithWindows: settings.engine_starts_with_windows,
  startupBehaviour: settings.startup_behaviour,
})

const settingNames: Record<keyof Settings, string> = {
  applicationName: 'application_name',
  accentColor: 'accent_color',
  defaultRate: 'default_rate',
  stopOnLock: 'stop_on_lock',
  stopOnSleep: 'stop_on_sleep',
  resumePrompt: 'resume_prompt',
  idleDetection: 'idle_detection',
  idleThreshold: 'idle_threshold',
  engineStartsWithWindows: 'engine_starts_with_windows',
  startupBehaviour: 'startup_behaviour',
}

export default function App() {
  const [view, setView] = useState<View>('timer')
  const [activeTimers, setActiveTimers] = useState<ActiveTimer[]>([])
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [settings, setSettings] = useState<Settings | null>(null)
  const [insights, setInsights] = useState<ApiInsights | null>(null)
  const [insightPeriod, setInsightPeriod] = useState<Exclude<InsightPeriod, 'all'>>('week')
  const [appStatus, setAppStatus] = useState<ApplicationStatus>('connecting')
  const [error, setError] = useState<string | null>(null)
  const [dialog, setDialog] = useState<Dialog>('none')

  useEffect(() => {
    if (!settings) return
    document.documentElement.style.setProperty('--color-primary', settings.accentColor)
    document.title = settings.applicationName
  }, [settings])

  const loadAll = useCallback(async () => {
    try {
      const [status, projectRows, activeRows, stoppedRows, settingRows, insightRows] = await Promise.all([
        api.status(), api.projects(), api.active(), api.sessions('stopped'), api.settings(), api.insights(insightPeriod),
      ])
      setAppStatus(status.app_status)
      setProjects(projectRows.map(toProject))
      setActiveTimers(activeRows.map(toActiveTimer))
      setHistory(stoppedRows.map(toHistoryEntry))
      setSettings(toSettings(settingRows))
      setInsights(insightRows)
      setError(null)
    } catch (caught) {
      setAppStatus('unavailable')
      setActiveTimers([])
      setError(caught instanceof Error ? caught.message : 'LuxTime is unavailable')
    }
  }, [insightPeriod])

  const refreshWork = useCallback(async () => {
    const [status, projectRows, activeRows, stoppedRows, insightRows] = await Promise.all([
      api.status(), api.projects(), api.active(), api.sessions('stopped'), api.insights(insightPeriod),
    ])
    setAppStatus(status.app_status)
    setProjects(projectRows.map(toProject))
    setActiveTimers(activeRows.map(toActiveTimer))
    setHistory(stoppedRows.map(toHistoryEntry))
    setInsights(insightRows)
    setError(null)
  }, [insightPeriod])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAll(), 0)
    return () => window.clearTimeout(timer)
  }, [loadAll])

  useEffect(() => {
    let disposed = false
    const timer = window.setInterval(async () => {
      try {
        const [status, activeRows] = await Promise.all([api.status(), api.active()])
        if (disposed) return
        setAppStatus(status.app_status)
        setActiveTimers(activeRows.map(toActiveTimer))
        setError(null)
      } catch (caught) {
        if (disposed) return
        setAppStatus('unavailable')
        setActiveTimers([])
        setError(caught instanceof Error ? caught.message : 'LuxTime is unavailable')
      }
    }, 1000)
    return () => { disposed = true; window.clearInterval(timer) }
  }, [])

  useEffect(() => {
    let disposed = false
    const refreshVisibleView = async () => {
      try {
        if (view === 'insights') {
          const rows = await api.insights(insightPeriod)
          if (!disposed) setInsights(rows)
        } else if (view === 'projects') {
          const rows = await api.projects()
          if (!disposed) setProjects(rows.map(toProject))
        } else if (view === 'history') {
          const rows = await api.sessions('stopped')
          if (!disposed) setHistory(rows.map(toHistoryEntry))
        }
      } catch (caught) {
        if (!disposed) setError(caught instanceof Error ? caught.message : 'LuxTime is unavailable')
      }
    }
    const initial = window.setTimeout(() => void refreshVisibleView(), 0)
    const timer = window.setInterval(() => void refreshVisibleView(), 5000)
    return () => {
      disposed = true
      window.clearTimeout(initial)
      window.clearInterval(timer)
    }
  }, [insightPeriod, view])

  const runMutation = useCallback(async (action: () => Promise<unknown>) => {
    try {
      await action()
      await refreshWork()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The action could not be completed')
    }
  }, [refreshWork])

  const startTimer = useCallback((projectName: string, workType: WorkType, description: string) => {
    const project = projects.find(item => item.name === projectName && item.active)
    if (!project) {
      setError('Select an active project before starting a timer')
      return
    }
    void runMutation(() => api.start({ project_id: project.id, work_type: workType, description }))
  }, [projects, runMutation])

  const updateSetting = useCallback(<K extends keyof Settings>(key: K, value: Settings[K]) => {
    void (async () => {
      try {
        const updated = await api.updateSettings({ [settingNames[key]]: value })
        setSettings(toSettings(updated))
        setError(null)
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : 'The setting could not be saved')
      }
    })()
  }, [])

  if (!settings) {
    return (
      <div className="h-full flex items-center justify-center" style={{ background: 'var(--color-background)', color: 'var(--color-text)' }}>
        <div className="text-center">
          <div className="text-sm font-semibold mb-2">{appStatus === 'connecting' ? 'Connecting to LuxTime…' : 'LuxTime is unavailable'}</div>
          {error && <div className="text-xs mb-4" style={{ color: 'var(--color-muted)' }}>{error}</div>}
          {appStatus !== 'connecting' && (
            <button className="px-4 py-2 rounded text-xs" style={{ background: 'var(--color-primary)', color: '#0C0C10' }} onClick={() => void loadAll()}>Retry</button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex overflow-hidden" style={{ background: 'var(--color-background)', color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
      <AppShell
        view={view}
        setView={setView}
        activeTimers={activeTimers}
        applicationName={settings.applicationName}
        onPause={id => void runMutation(() => api.pause(id))}
        onResume={id => void runMutation(() => api.resume(id))}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        {error && (
          <div className="px-4 py-2 text-xs flex items-center" role="alert" style={{ background: 'rgba(248,113,113,0.12)', color: 'var(--color-danger)', borderBottom: '1px solid rgba(248,113,113,0.2)' }}>
            {error}
            <button className="ml-auto" style={{ background: 'none', border: 'none', color: 'inherit' }} onClick={() => setError(null)}>×</button>
          </div>
        )}
        <main className="flex-1 overflow-auto">
          {view === 'timer' && (
            <TimerView activeTimers={activeTimers} projects={projects} onStart={startTimer}
              onStop={id => void runMutation(() => api.stop(id))}
              onPause={id => void runMutation(() => api.pause(id))}
              onResume={id => void runMutation(() => api.resume(id))}
              onUpdate={(id, values) => void runMutation(() => api.updateSession(id, values))}
              onDelete={id => void runMutation(() => api.deleteSession(id))}
              onAddAnother={() => setDialog('addProject')} />
          )}
          {view === 'history' && (
            <HistoryView history={history}
              onDelete={id => void runMutation(() => api.deleteSession(id))} />
          )}
          {view === 'insights' && insights && (
            <InsightsView insights={insights} period={insightPeriod} onPeriodChange={setInsightPeriod} />
          )}
          {view === 'projects' && (
            <ProjectsView projects={projects}
              onCreate={(name, code, color) => void runMutation(() => api.createProject({ name, code: code || undefined, color }))}
              onUpdate={(id, values) => void runMutation(() => api.updateProject(id, values))} />
          )}
          {view === 'settings' && (
            <SettingsView settings={settings} onUpdate={updateSetting} appStatus={appStatus} />
          )}
        </main>
      </div>

      {dialog === 'addProject' && (
        <AddProjectOverlay projects={projects} onStart={startTimer} onClose={() => setDialog('none')} />
      )}
    </div>
  )
}
