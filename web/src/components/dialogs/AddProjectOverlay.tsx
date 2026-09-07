import { useState } from 'react'
import type { Project, WorkType } from '../../App'
import { WORK_TYPES } from '../../App'

type Props = {
  projects: Project[]
  onStart: (project: string, workType: WorkType, description: string) => void
  onClose: () => void
}

export default function AddProjectOverlay({ projects, onStart, onClose }: Props) {
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
    onClose()
  }

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(2px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        className="rounded-lg p-6 w-full"
        style={{
          maxWidth: 400,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          boxShadow: '0 24px 64px rgba(0,0,0,0.6)',
        }}
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>
            Track Another Project
          </h3>
          <button
            onClick={onClose}
            style={{ color: 'var(--color-muted)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}
          >
            ×
          </button>
        </div>

        <p className="text-xs mb-4" style={{ color: 'var(--color-muted)' }}>
          Existing timers will continue running independently.
        </p>

        {/* Project selector */}
        <div className="relative mb-3">
          <div
            className="flex items-center gap-2 px-3 py-2.5 rounded cursor-pointer"
            style={{
              background: 'var(--color-surface-raised)',
              border: `1px solid ${showDropdown ? 'var(--color-primary)' : 'var(--color-border)'}`,
            }}
            onClick={() => setShowDropdown(v => !v)}
          >
            {selectedData && <span className="w-2 h-2 rounded-full shrink-0" style={{ background: selectedData.color }} />}
            <input
              className="flex-1 bg-transparent outline-none text-sm"
              style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
              placeholder="Select project…"
              value={showDropdown ? search : selectedProject}
              onChange={e => { setSearch(e.target.value); setShowDropdown(true) }}
              onFocus={() => { setShowDropdown(true); setSearch('') }}
              readOnly={!showDropdown}
            />
          </div>
          {showDropdown && (
            <div
              className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-20"
              style={{
                background: 'var(--color-surface-raised)',
                border: '1px solid var(--color-border)',
                boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                maxHeight: 180,
                overflowY: 'auto',
              }}
            >
              {filtered.map(p => (
                <div
                  key={p.id}
                  className="flex items-center gap-3 px-3 py-2 cursor-pointer"
                  style={{ fontSize: 13 }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-surface-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  onClick={() => { setSelectedProject(p.name); setSearch(''); setShowDropdown(false) }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
                  <span style={{ color: 'var(--color-text)' }}>{p.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Work type */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {WORK_TYPES.map(wt => (
            <button
              key={wt}
              onClick={() => setWorkType(wt)}
              className="px-2.5 py-1 rounded text-xs transition-all"
              style={{
                background: workType === wt ? 'rgba(34,211,238,0.15)' : 'var(--color-surface-raised)',
                color: workType === wt ? 'var(--color-primary)' : 'var(--color-muted-bright)',
                border: `1px solid ${workType === wt ? 'rgba(34,211,238,0.4)' : 'var(--color-border)'}`,
              }}
            >
              {wt}
            </button>
          ))}
        </div>

        {/* Description */}
        <input
          type="text"
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="What are you doing? (optional)"
          className="w-full px-3 py-2.5 rounded text-sm bg-transparent outline-none mb-4"
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

        <button
          onClick={handleStart}
          disabled={!selectedProject}
          className="w-full py-2.5 rounded text-sm font-semibold"
          style={{
            background: selectedProject ? 'var(--color-primary)' : 'var(--color-surface-raised)',
            color: selectedProject ? '#0C0C10' : 'var(--color-muted)',
            border: 'none',
            cursor: selectedProject ? 'pointer' : 'not-allowed',
          }}
        >
          Start Tracking
        </button>
      </div>
    </div>
  )
}
