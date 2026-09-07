import type { ActiveTimer, Project, WorkType } from '../../App'
import NoTimerState from './NoTimerState'
import ActiveTimersPanel from './ActiveTimersPanel'

type Props = {
  activeTimers: ActiveTimer[]
  projects: Project[]
  onStart: (project: string, workType: WorkType, description: string) => void
  onStop: (id: string) => void
  onAddAnother: () => void
}

export default function TimerView({ activeTimers, projects, onStart, onStop, onAddAnother }: Props) {
  const isActive = activeTimers.length > 0

  return (
    <div className="h-full">
      {isActive ? (
        <ActiveTimersPanel
          timers={activeTimers}
          onStop={onStop}
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
