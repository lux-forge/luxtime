import { useState, useEffect, useCallback } from 'react'
import AppShell from './components/layout/AppShell'
import TimerView from './components/timer/TimerView'
import HistoryView from './components/history/HistoryView'
import InsightsView from './components/insights/InsightsView'
import ProjectsView from './components/projects/ProjectsView'
import SettingsView from './components/settings/SettingsView'
import ResumeDialog from './components/dialogs/ResumeDialog'
import IdleDialog from './components/dialogs/IdleDialog'
import RecoveryDialog from './components/dialogs/RecoveryDialog'
import AddProjectOverlay from './components/dialogs/AddProjectOverlay'

export type View = 'timer' | 'history' | 'projects' | 'insights' | 'settings'
export type WorkType = 'Development' | 'Design' | 'Research' | 'Operations' | 'Admin' | 'Business'
export type Dialog = 'none' | 'resume' | 'idle' | 'recovery' | 'addProject'

export type ActiveTimer = {
  id: string
  project: string
  projectColor: string
  workType: WorkType
  description: string
  startedAt: Date
  elapsed: number
  rate: number
}

export type HistoryEntry = {
  id: string
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
  concurrent?: boolean
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

export default function App() {
  const [view, setView] = useState<View>('timer')
  const [activeTimers, setActiveTimers] = useState<ActiveTimer[]>([])
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [dialog, setDialog] = useState<Dialog>('none')
  const [settings, setSettings] = useState<Settings>({
    defaultRate: 50,
    stopOnLock: true,
    stopOnSleep: true,
    resumePrompt: true,
    idleDetection: true,
    idleThreshold: 20,
    engineStartsWithWindows: true,
    startupBehaviour: 'tray',
  })

  useEffect(() => {
    if (activeTimers.length === 0) return
    const id = setInterval(() => {
      setActiveTimers(prev => prev.map(t => ({ ...t, elapsed: t.elapsed + 1 })))
    }, 1000)
    return () => clearInterval(id)
  }, [activeTimers.length])

  const startTimer = useCallback((project: string, workType: WorkType, description: string) => {
    const projectData = projects.find(p => p.name === project)
    const newTimer: ActiveTimer = {
      id: crypto.randomUUID(),
      project,
      projectColor: projectData?.color ?? '#5A5A72',
      workType,
      description,
      startedAt: new Date(),
      elapsed: 0,
      rate: settings.defaultRate,
    }
    setActiveTimers(prev => [...prev, newTimer])
  }, [projects, settings.defaultRate])

  const stopTimer = useCallback((id: string) => {
    setActiveTimers(prev => {
      const timer = prev.find(t => t.id === id)
      if (timer) {
        const entry: HistoryEntry = {
          id: crypto.randomUUID(),
          date: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
          start: timer.startedAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
          end: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
          durationSeconds: timer.elapsed,
          project: timer.project,
          projectColor: timer.projectColor,
          workType: timer.workType,
          description: timer.description,
          stopReason: 'Manual',
          rate: timer.rate,
          concurrent: prev.length > 1,
        }
        setHistory(h => [entry, ...h])
      }
      return prev.filter(t => t.id !== id)
    })
  }, [])

  const stopAllTimers = useCallback(() => {
    setActiveTimers(prev => {
      prev.forEach(timer => {
        const entry: HistoryEntry = {
          id: crypto.randomUUID(),
          date: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
          start: timer.startedAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
          end: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
          durationSeconds: timer.elapsed,
          project: timer.project,
          projectColor: timer.projectColor,
          workType: timer.workType,
          description: timer.description,
          stopReason: 'Manual',
          rate: timer.rate,
          concurrent: prev.length > 1,
        }
        setHistory(h => [entry, ...h])
      })
      return []
    })
  }, [])

  return (
    <div className="h-full flex overflow-hidden" style={{ background: 'var(--color-background)', color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
      <AppShell
        view={view}
        setView={setView}
        activeTimers={activeTimers}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-auto">
          {view === 'timer' && (
            <TimerView
              activeTimers={activeTimers}
              projects={projects}
              onStart={startTimer}
              onStop={stopTimer}
              onAddAnother={() => setDialog('addProject')}
            />
          )}
          {view === 'history' && (
            <HistoryView
              history={history}
              activeTimers={activeTimers}
              onNavigateTimer={() => setView('timer')}
            />
          )}
          {view === 'insights' && (
            <InsightsView
              history={history}
              activeTimers={activeTimers}
              onNavigateTimer={() => setView('timer')}
            />
          )}
          {view === 'projects' && (
            <ProjectsView
              projects={projects}
              setProjects={setProjects}
              activeTimers={activeTimers}
              onNavigateTimer={() => setView('timer')}
            />
          )}
          {view === 'settings' && (
            <SettingsView
              settings={settings}
              setSettings={setSettings}
              activeTimers={activeTimers}
              onNavigateTimer={() => setView('timer')}
            />
          )}
        </main>
      </div>

      {dialog === 'resume' && (
        <ResumeDialog
          sessions={[]}
          onClose={() => setDialog('none')}
          onResume={(items) => {
            items.forEach(p => startTimer(p.project, p.workType, p.description))
            setDialog('none')
          }}
        />
      )}
      {dialog === 'idle' && (
        <IdleDialog
          activeTimers={activeTimers}
          idleThreshold={settings.idleThreshold}
          onKeepAll={() => setDialog('none')}
          onStopAll={() => { stopAllTimers(); setDialog('none') }}
          onClose={() => setDialog('none')}
        />
      )}
      {dialog === 'recovery' && (
        <RecoveryDialog
          sessions={[]}
          onClose={() => setDialog('none')}
          onContinue={(project, workType, description) => {
            startTimer(project, workType, description)
            setDialog('none')
          }}
        />
      )}
      {dialog === 'addProject' && (
        <AddProjectOverlay
          projects={projects}
          onStart={startTimer}
          onClose={() => setDialog('none')}
        />
      )}
    </div>
  )
}
