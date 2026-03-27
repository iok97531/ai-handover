import { useProjectStore } from '../../stores/projectStore'
import { FolderPlus, Folder, Trash2, Settings, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import IndexProgress from '../Projects/IndexProgress'

interface SidebarProps {
  onOpenSettings: () => void
}

export default function Sidebar({ onOpenSettings }: SidebarProps) {
  const { projects, selectedProjectId, selectProject, addProject, removeProject, triggerIndex } =
    useProjectStore()
  const [adding, setAdding] = useState(false)

  const handleAddProject = async () => {
    const folderPath = await window.api.selectFolder()
    if (!folderPath) return

    setAdding(true)
    const folderName = folderPath.split(/[/\\]/).pop() || 'Untitled'
    await addProject(folderName, folderPath)
    setAdding(false)
  }

  return (
    <div className="flex h-full w-64 flex-col border-r border-slate-700 bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-700 p-4">
        <h1 className="text-lg font-bold text-white">Scope</h1>
        <button
          onClick={onOpenSettings}
          className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
        >
          <Settings size={18} />
        </button>
      </div>

      <div className="p-3">
        <button
          onClick={handleAddProject}
          disabled={adding}
          className="flex w-full items-center gap-2 rounded-lg border border-dashed border-slate-600 px-3 py-2 text-sm text-slate-400 transition hover:border-blue-500 hover:text-blue-400 disabled:opacity-50"
        >
          <FolderPlus size={16} />
          {adding ? '추가 중...' : '프로젝트 추가'}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3">
        {projects.map((project) => (
          <div
            key={project.id}
            onClick={() => selectProject(project.id)}
            className={`group mb-1 cursor-pointer rounded-lg px-3 py-2 transition ${
              selectedProjectId === project.id
                ? 'bg-blue-600/20 text-blue-400'
                : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 overflow-hidden">
                <Folder size={16} className="shrink-0" />
                <span className="truncate text-sm font-medium">{project.name}</span>
              </div>
              <div className="flex items-center gap-0.5">
                {project.status === 'ready' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      triggerIndex(project.id)
                    }}
                    title="다시 인덱싱"
                    className="hidden rounded p-1 text-slate-500 hover:text-blue-400 group-hover:block"
                  >
                    <RefreshCw size={13} />
                  </button>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    removeProject(project.id)
                  }}
                  className="hidden rounded p-1 text-slate-500 hover:text-red-400 group-hover:block"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
            <div className="mt-1 pl-6">
              <IndexProgress project={project} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
