export type SessionStatus = 'running' | 'paused' | 'stopped'
export type PauseMode = 'manual' | 'away' | 'sleep' | 'lock'
export type WorkTypeName = 'Development' | 'Design' | 'Research' | 'Operations' | 'Admin' | 'Business'
export type InsightPeriod = 'week' | 'month' | 'quarter' | 'year' | 'all'

export type ApiStatus = {
  app_status: 'ready' | 'tracking' | 'paused' | 'degraded'
  database_connected: boolean
  active_sessions: number
  running_sessions: number
  paused_sessions: number
}

export type ApiProject = {
  id: string
  name: string
  code: string | null
  color: string
  total_seconds: number
  active: boolean
  created_at: string
  updated_at: string
}

export type ApiSegment = {
  id: string
  session_id: string
  started_at: string
  ended_at: string | null
}

export type ApiSession = {
  id: string
  project_id: string
  project: string
  project_color: string
  work_type: WorkTypeName
  description: string
  hourly_rate: string | number
  status: SessionStatus
  pause_mode: PauseMode | null
  started_at: string
  stopped_at: string | null
  stop_reason: string | null
  total_seconds: number
  concurrent: boolean
  created_at: string
  updated_at: string
  segments?: ApiSegment[] | null
}

export type ApiSettings = {
  application_name: string
  accent_color: string
  default_rate: string | number
  stop_on_lock: boolean
  stop_on_sleep: boolean
  resume_prompt: boolean
  idle_detection: boolean
  idle_threshold: number
  engine_starts_with_windows: boolean
  startup_behaviour: 'tray' | 'compact' | 'window'
  updated_at: string
}

export type ApiInsights = {
  period: InsightPeriod
  range_start: string | null
  range_end: string
  elapsed_seconds: number
  project_attributed_seconds: number
  concurrent_attribution_seconds: number
  notional_labour_value: number
  session_count: number
  average_session_seconds: number
  projects: Array<{
    project_id: string
    project: string
    color: string
    seconds: number
    value: number
  }>
  work_types: Array<{ name: string; seconds: number }>
  days: Array<{
    date: string
    total_seconds: number
    projects: Array<{
      project_id: string
      project: string
      color: string
      seconds: number
    }>
  }>
  session_lengths: Array<{ label: string; count: number }>
}
