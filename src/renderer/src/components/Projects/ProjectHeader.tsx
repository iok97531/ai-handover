import { useState, useEffect } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Folder, RefreshCw, Eye } from 'lucide-react'
import { getWatcherEvents } from '../../api/client'
import type { WatcherStatus } from '../../types'
import IndexProgress from './IndexProgress'

export default function ProjectHeader() {
  const { projects, selectedProjectId, triggerIndex } = useProjectStore()
  const project = projects.find((p) => p.id === selectedProjectId)
  const [watcherStatus, setWatcherStatus] = useState<WatcherStatus | null>(null)
  const [showEvents, setShowEvents] = useState(false)

  useEffect(() => {
    if (!project || project.status !== 'ready') {
      setWatcherStatus(null)
      return
    }

    const poll = async () => {
      try {
        const status = await getWatcherEvents(project.id)
        setWatcherStatus(status)
      } catch {
        // ignore
      }
    }

    poll()
    const interval = setInterval(poll, 5000)
    return () => clearInterval(interval)
  }, [project?.id, project?.status])

  if (!project) return null

  return (
    <div className="relative border-b border-slate-700">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <Folder size={18} className="text-slate-400" />
          <div>
            <div className="text-sm font-medium text-white">{project.name}</div>
            <div className="max-w-md truncate text-xs text-slate-500">{project.folder_path}</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {watcherStatus?.is_watching && (
            <button
              onClick={() => setShowEvents(!showEvents)}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-emerald-400 transition hover:bg-slate-800"
              title="파일 감시 중 — 클릭하여 최근 변경 보기"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
              </span>
              <Eye size={14} />
              감시 중
            </button>
          )}
          <div className="w-48">
            <IndexProgress project={project} />
          </div>
          {project.status === 'ready' && (
            <button
              onClick={() => triggerIndex(project.id)}
              title="다시 인덱싱"
              className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-white"
            >
              <RefreshCw size={16} />
            </button>
          )}
        </div>
      </div>

      {showEvents && watcherStatus && watcherStatus.events.length > 0 && (
        <div className="border-t border-slate-700/50 bg-slate-800/50 px-4 py-2">
          <div className="mb-1 text-xs font-medium text-slate-400">최근 파일 변경</div>
          <div className="max-h-32 space-y-0.5 overflow-y-auto">
            {watcherStatus.events
              .slice()
              .reverse()
              .slice(0, 10)
              .map((evt, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span
                    className={
                      evt.event_type === 'created'
                        ? 'text-green-400'
                        : evt.event_type === 'deleted'
                          ? 'text-red-400'
                          : 'text-yellow-400'
                    }
                  >
                    {evt.event_type === 'created' ? '+' : evt.event_type === 'deleted' ? '-' : '~'}
                  </span>
                  <span className="truncate text-slate-300">{evt.file_path}</span>
                  <span className="ml-auto whitespace-nowrap text-slate-500">
                    {new Date(evt.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
