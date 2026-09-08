import { useState } from 'react'
import type { Project, WorkType } from '../../App'
import { WORK_TYPES } from '../../App'

type Props = {
  projects: Project[]
  onStart: (project: string, workType: WorkType, description: string) => void
}

export default function NoTimerState({ projects, onStart }: Props) {
  const [selectedProject, setSelectedProject] = useState('')
  const [workType, setWorkType] = useState<WorkType>('Development')
  const [description, setDescription] = useState('')
  const [search, setSearch] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)

  const activeProjects = projects.filter(p => p.active)
  const filtered = search
    ? activeProjects.filter(p => p.name.toLowerCase().includes(search.toLowerCase()))
    : activeProjects

  const selectedData = projects.find(p => p.name === selectedProject)

  function handleStart() {
    if (!selectedProject) return
    onStart(selectedProject, workType, description)
    setSelectedProject('')
    setDescription('')
    setSearch('')
  }

  return (
    <div className="flex flex-col items-center justify-center h-full px-8" style={{ maxWidth: 440, margin: '0 auto' }}>
      <div className="w-full">
        <h2
          className="text-2xl font-light mb-8 text-center"
          style={{ color: 'var(--color-muted-bright)', letterSpacing: '-0.01em' }}
        >
          What are you working on?
        </h2>

        {/* Project selector */}
        <div className="relative mb-4">
          <div
            className="flex items-center gap-2 px-3 py-2.5 rounded cursor-pointer transition-colors"
            style={{
              background: 'var(--color-surface-raised)',
              border: `1px solid ${showDropdown ? 'var(--color-primary)' : 'var(--color-border)'}`,
            }}
            onClick={() => setShowDropdown(v => !v)}
          >
            {selectedData && (
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ background: selectedData.color }}
              />
            )}
            <input
              className="flex-1 bg-transparent outline-none text-sm"
              style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
              placeholder="Select project…"
              value={showDropdown ? search : selectedProject}
              onChange={e => { setSearch(e.target.value); setShowDropdown(true) }}
              onFocus={() => { setShowDropdown(true); setSearch('') }}
              readOnly={!showDropdown}
            />
            <span style={{ color: 'var(--color-muted)', fontSize: 10 }}>▾</span>
          </div>

          {showDropdown && (
            <div
              className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-10"
              style={{
                background: 'var(--color-surface-raised)',
                border: '1px solid var(--color-border)',
                boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                maxHeight: 220,
                overflowY: 'auto',
              }}
            >
              {filtered.map(p => (
                <div
                  key={p.id}
                  className="flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors"
                  style={{ fontSize: 13 }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-surface-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  onClick={() => {
                    setSelectedProject(p.name)
                    setSearch('')
                    setShowDropdown(false)
                  }}
                >
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: p.color }} />
                  <span style={{ color: 'var(--color-text)' }}>{p.name}</span>
                  <span className="ml-auto text-xs" style={{ color: 'var(--color-muted)', fontFamily: 'var(--font-mono)' }}>
                    {p.code}
                  </span>
                </div>
              ))}
              {filtered.length === 0 && (
                <div className="px-3 py-3 text-sm" style={{ color: 'var(--color-muted)' }}>
                  No projects found
                </div>
              )}
            </div>
          )}
        </div>

        {/* Work type chips */}
        <div className="flex flex-wrap gap-2 mb-4">
          {WORK_TYPES.map(wt => (
            <button
              key={wt}
              onClick={() => setWorkType(wt)}
              className="px-3 py-1 rounded text-xs font-medium transition-all"
              style={{
                background: workType === wt ? 'var(--color-primary-soft)' : 'var(--color-surface-raised)',
                color: workType === wt ? 'var(--color-primary)' : 'var(--color-muted-bright)',
                border: `1px solid ${workType === wt ? 'var(--color-primary-border)' : 'var(--color-border)'}`,
              }}
            >
              {wt}
            </button>
          ))}
        </div>

        {/* Description */}
        <div className="mb-6">
          <input
            type="text"
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="What are you doing? (optional)"
            className="w-full px-3 py-2.5 rounded text-sm bg-transparent outline-none transition-colors"
            style={{
              background: 'var(--color-surface-raised)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
            }}
            onFocus={e => (e.target.style.borderColor = 'var(--color-primary)')}
            onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
            onKeyDown={e => { if (e.key === 'Enter') handleStart() }}
          />
        </div>

        {/* Start */}
        <button
          onClick={handleStart}
          disabled={!selectedProject}
          className="w-full py-3 rounded text-sm font-semibold transition-all"
          style={{
            background: selectedProject ? 'var(--color-primary)' : 'var(--color-surface-raised)',
            color: selectedProject ? '#0C0C10' : 'var(--color-muted)',
            border: 'none',
            cursor: selectedProject ? 'pointer' : 'not-allowed',
            letterSpacing: '0.02em',
          }}
        >
          Start Tracking
        </button>

        {/* Recent projects hint */}
        {activeProjects.length > 0 && (
          <div className="mt-8">
            <div className="text-xs mb-2" style={{ color: 'var(--color-muted)' }}>Recent</div>
            <div className="flex flex-col gap-1">
              {activeProjects.slice(0, 3).map(p => (
                <button
                  key={p.id}
                  className="flex items-center gap-2.5 px-2 py-1.5 rounded text-left text-sm transition-colors"
                  style={{ color: 'var(--color-muted-bright)', background: 'transparent' }}
                  onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-surface-raised)'; e.currentTarget.style.color = 'var(--color-text)' }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--color-muted-bright)' }}
                  onClick={() => setSelectedProject(p.name)}
                >
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: p.color }} />
                  {p.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
