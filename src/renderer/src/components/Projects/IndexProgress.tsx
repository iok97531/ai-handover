import { useEffect, useState } from 'react'
import { Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import type { IndexStatus, Project } from '../../types'
import * as api from '../../api/client'

interface IndexProgressProps {
  project: Project
}

export default function IndexProgress({ project }: IndexProgressProps) {
  const [status, setStatus] = useState<IndexStatus | null>(null)

  useEffect(() => {
    if (project.status !== 'indexing') {
      setStatus(null)
      return
    }

    const poll = async () => {
      try {
        const s = await api.getIndexStatus(project.id)
        setStatus(s)
      } catch {
        // ignore polling errors
      }
    }

    poll()
    const interval = setInterval(poll, 1500)
    return () => clearInterval(interval)
  }, [project.id, project.status])

  if (project.status === 'pending') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-slate-500">
        <Clock size={12} />
        <span>대기 중</span>
      </div>
    )
  }

  if (project.status === 'error') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-red-400">
        <AlertCircle size={12} />
        <span>오류 발생</span>
      </div>
    )
  }

  if (project.status === 'ready') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-green-400">
        <CheckCircle size={12} />
        <span>
          {project.file_count}개 파일 · {project.chunk_count}개 청크
        </span>
      </div>
    )
  }

  // indexing
  const percent = status?.progress_percent ?? 0
  const filesInfo = status ? `${status.files_indexed}/${status.files_total}` : '...'

  return (
    <div className="w-full space-y-1">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-yellow-400">
          <Loader2 size={12} className="animate-spin" />
          <span>인덱싱 중</span>
        </div>
        <span className="text-slate-500">{filesInfo} 파일</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-700">
        <div
          className="h-full rounded-full bg-yellow-400 transition-all duration-300"
          style={{ width: `${Math.max(percent, 2)}%` }}
        />
      </div>
    </div>
  )
}
