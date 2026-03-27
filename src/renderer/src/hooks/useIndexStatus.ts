import { useEffect, useRef } from 'react'
import { useProjectStore } from '../stores/projectStore'
import * as api from '../api/client'

const POLL_INTERVAL = 2000 // 2초마다 폴링

export function useIndexPolling() {
  const { projects, fetchProjects } = useProjectStore()
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const indexingProjects = projects.filter((p) => p.status === 'indexing')

    if (indexingProjects.length === 0) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    // 인덱싱 중인 프로젝트가 있으면 폴링 시작
    if (!intervalRef.current) {
      intervalRef.current = setInterval(async () => {
        // 프로젝트 목록 새로고침으로 상태 동기화
        await fetchProjects()
      }, POLL_INTERVAL)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [projects, fetchProjects])
}
