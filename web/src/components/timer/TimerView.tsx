import type { ActiveTimer, Project, WorkType } from '../../App'
import NoTimerState from './NoTimerState'
import ActiveTimersPanel from './ActiveTimersPanel'

type Props = {
  activeTimers: ActiveTimer[]
  projects: Project[]
  onStart: (project: string, workType: WorkType, description: string) => void
  onStop: (id: string) => void
  onPause: (id: string) => void
  onResume: (id: string) => void
  onUpdate: (id: string, values: { project_id?: string; description?: string }) => void
  onDelete: (id: string) => void
  onAddAnother: () => void
}

export default function TimerView({ activeTimers, projects, onStart, onStop, onPause, onResume, onUpdate, onDelete, onAddAnother }: Props) {
  const isActive = activeTimers.length > 0

  return (
    <div className="h-full">
      {isActive ? (
        <ActiveTimersPanel
          timers={activeTimers}
          projects={projects}
          onStop={onStop}
          onPause={onPause}
          onResume={onResume}
          onUpdate={onUpdate}
          onDelete={onDelete}
          onAddAnother={onAddAnother}
        />
      ) : (
        <NoTimerState
          projects={projects}
          onStart={onStart}
        />
      )}
    </div>
  )
}
