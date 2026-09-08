import { useState } from 'react'
import type { Project } from '../../App'
import { formatDuration } from '../../App'

type Props = {
  projects: Project[]
  onCreate: (name: string, code: string, color: string) => void
  onUpdate: (id: string, values: Partial<Pick<Project, 'name' | 'code' | 'color' | 'active'>>) => void
}

export default function ProjectsView({ projects, onCreate, onUpdate }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState('')
  const [newCode, setNewCode] = useState('')

  const COLORS = ['#34D399', '#22D3EE', '#818CF8', '#F472B6', '#FBBF24', '#60A5FA', '#C084FC', '#FB923C']

  function startEdit(p: Project) {
    setEditingId(p.id)
    setEditName(p.name)
  }

  function saveEdit(id: string) {
    const name = editName.trim()
    const existing = projects.find(project => project.id === id)
    if (name && existing && name !== existing.name) onUpdate(id, { name })
    setEditingId(null)
  }

  function toggleActive(id: string) {
    const project = projects.find(item => item.id === id)
    if (project) onUpdate(id, { active: !project.active })
  }

  function addProject() {
    if (!newName.trim()) return
    onCreate(
      newName.trim(),
      newCode.trim().toUpperCase() || newName.slice(0, 3).toUpperCase(),
      COLORS[projects.length % COLORS.length],
    )
    setNewName('')
    setNewCode('')
    setShowAdd(false)
  }

  const active = projects.filter(p => p.active)
  const archived = projects.filter(p => !p.active)

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-auto px-8 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-base font-semibold" style={{ color: 'var(--color-text)' }}>Projects</h1>
          <button
            onClick={() => setShowAdd(v => !v)}
            className="px-3 py-1.5 rounded text-xs"
            style={{
              background: 'var(--color-primary-soft)',
              color: 'var(--color-primary)',
              border: '1px solid var(--color-primary-emphasis)',
            }}
          >
            + Add Project
          </button>
        </div>

        {/* Add form */}
        {showAdd && (
          <div
            className="mb-5 p-4 rounded"
            style={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
          >
            <div className="flex gap-3 mb-3">
              <input
                type="text"
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="Project name"
                className="flex-1 px-3 py-2 rounded text-sm bg-transparent outline-none"
                style={{
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text)',
                  fontFamily: 'var(--font-sans)',
                }}
                onFocus={e => (e.target.style.borderColor = 'var(--color-primary)')}
                onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
                onKeyDown={e => { if (e.key === 'Enter') addProject() }}
              />
              <input
                type="text"
                value={newCode}
                onChange={e => setNewCode(e.target.value)}
                placeholder="Project code (optional)"
                className="px-3 py-2 rounded text-sm bg-transparent outline-none"
                style={{
                  width: 120,
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text)',
                  fontFamily: 'var(--font-mono)',
                }}
                onFocus={e => (e.target.style.borderColor = 'var(--color-primary)')}
                onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={addProject}
                className="px-4 py-1.5 rounded text-xs font-semibold"
                style={{ background: 'var(--color-primary)', color: '#0C0C10', border: 'none' }}
              >
                Add
              </button>
              <button
                onClick={() => setShowAdd(false)}
                className="px-4 py-1.5 rounded text-xs"
                style={{ background: 'transparent', color: 'var(--color-muted)', border: '1px solid var(--color-border)' }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Active projects */}
        <div className="mb-6">
          <div className="text-xs font-semibold tracking-widest uppercase mb-3" style={{ color: 'var(--color-muted)', letterSpacing: '0.1em' }}>
            Active — {active.length}
          </div>
          <div className="rounded overflow-hidden" style={{ border: '1px solid var(--color-border)' }}>
            {active.map((p, i) => (
              <ProjectRow
                key={p.id}
                project={p}
                isLast={i === active.length - 1}
                isEditing={editingId === p.id}
                editName={editName}
                onEditName={setEditName}
                onStartEdit={() => startEdit(p)}
                onSaveEdit={() => saveEdit(p.id)}
                onCancelEdit={() => setEditingId(null)}
                onToggleActive={() => toggleActive(p.id)}
              />
            ))}
            {active.length === 0 && (
              <div className="px-4 py-12 text-center text-sm" style={{ color: 'var(--color-muted)' }}>
                {projects.length === 0 ? 'No projects yet.' : 'No active projects.'}
              </div>
            )}
          </div>
        </div>

        {/* Archived */}
        {archived.length > 0 && (
          <div>
            <div className="text-xs font-semibold tracking-widest uppercase mb-3" style={{ color: 'var(--color-muted)', letterSpacing: '0.1em' }}>
              Archived — {archived.length}
            </div>
            <div className="rounded overflow-hidden" style={{ border: '1px solid var(--color-border)' }}>
              {archived.map((p, i) => (
                <ProjectRow
                  key={p.id}
                  project={p}
                  isLast={i === archived.length - 1}
                  isEditing={editingId === p.id}
                  editName={editName}
                  onEditName={setEditName}
                  onStartEdit={() => startEdit(p)}
                  onSaveEdit={() => saveEdit(p.id)}
                  onCancelEdit={() => setEditingId(null)}
                  onToggleActive={() => toggleActive(p.id)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ProjectRow({
  project,
  isLast,
  isEditing,
  editName,
  onEditName,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onToggleActive,
}: {
  project: Project
  isLast: boolean
  isEditing: boolean
  editName: string
  onEditName: (n: string) => void
  onStartEdit: () => void
  onSaveEdit: () => void
  onCancelEdit: () => void
  onToggleActive: () => void
}) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      className="flex items-center gap-4 px-4 py-3 transition-colors"
      style={{
        background: hovered ? 'var(--color-surface-raised)' : 'transparent',
        borderBottom: isLast ? 'none' : '1px solid var(--color-border-subtle)',
        opacity: project.active ? 1 : 0.5,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Color dot */}
      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: project.color }} />

      {/* Name */}
      <div className="flex-1 min-w-0">
        {isEditing ? (
          <input
            autoFocus
            className="bg-transparent outline-none text-sm w-full"
            style={{
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
              borderBottom: '1px solid var(--color-primary)',
            }}
            value={editName}
            onChange={e => onEditName(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') onSaveEdit()
              if (e.key === 'Escape') onCancelEdit()
            }}
            onBlur={onSaveEdit}
          />
        ) : (
          <span className="text-sm" style={{ color: 'var(--color-text)' }}>{project.name}</span>
        )}
      </div>

      {/* Code */}
      <span className="text-xs" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-muted)', width: 36 }}>
        {project.code}
      </span>

      {/* Total hours */}
      <span className="text-xs" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-muted-bright)', width: 56, textAlign: 'right' }}>
        {formatDuration(project.totalSeconds)}
      </span>

      {/* Actions */}
      <div
        className="flex items-center gap-2"
        style={{ opacity: hovered ? 1 : 0, transition: 'opacity 0.15s' }}
      >
        {!isEditing && (
          <button
            onClick={onStartEdit}
            className="text-xs px-2 py-1 rounded"
            style={{ color: 'var(--color-muted-bright)', background: 'none', border: '1px solid var(--color-border)', cursor: 'pointer' }}
          >
            Rename
          </button>
        )}
        <button
          onClick={onToggleActive}
          className="text-xs px-2 py-1 rounded"
          style={{
            color: project.active ? 'var(--color-muted)' : 'var(--color-active)',
            background: 'none',
            border: '1px solid var(--color-border)',
            cursor: 'pointer',
          }}
        >
          {project.active ? 'Archive' : 'Restore'}
        </button>
      </div>
    </div>
  )
}
