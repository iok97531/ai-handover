import { useEffect, useState } from 'react'
import MainLayout from './components/Layout/MainLayout'
import Sidebar from './components/Layout/Sidebar'
import ChatPanel from './components/Chat/ChatPanel'
import SettingsPanel from './components/Settings/SettingsPanel'
import { useProjectStore } from './stores/projectStore'
import { initApiClient } from './api/client'
import { useIndexPolling } from './hooks/useIndexStatus'

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const { fetchProjects } = useProjectStore()

  useIndexPolling()

  useEffect(() => {
    initApiClient().then(() => {
      fetchProjects()
    })
  }, [])

  return (
    <MainLayout sidebar={<Sidebar onOpenSettings={() => setSettingsOpen(true)} />}>
      <ChatPanel />
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </MainLayout>
  )
}
