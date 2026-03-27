import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '../../stores/chatStore'
import { useProjectStore } from '../../stores/projectStore'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import ProjectHeader from '../Projects/ProjectHeader'
import HandoverWelcome from './HandoverWelcome'
import { MessageSquare } from 'lucide-react'

export default function ChatPanel() {
  const { projects, selectedProjectId } = useProjectStore()
  const { messages, streaming, sendMessage } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showWelcome, setShowWelcome] = useState(true)

  const projectMessages = selectedProjectId ? messages[selectedProjectId] || [] : []
  const selectedProject = projects.find((p) => p.id === selectedProjectId)
  const isReady = selectedProject?.status === 'ready'

  // 프로젝트가 바뀌거나 메시지가 없으면 웰컴 화면 초기화
  useEffect(() => {
    setShowWelcome(true)
  }, [selectedProjectId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [projectMessages])

  if (!selectedProjectId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-slate-500">
        <MessageSquare size={48} className="mb-4" />
        <p className="text-lg">프로젝트를 선택해주세요</p>
        <p className="text-sm">왼쪽에서 프로젝트를 추가하거나 선택하세요</p>
      </div>
    )
  }

  const handleSend = (question: string) => {
    if (!streaming && isReady) {
      sendMessage(selectedProjectId, question)
    }
  }

  const handleHandover = (display: string, instruction: string) => {
    setShowWelcome(false)
    if (!streaming && isReady) {
      sendMessage(selectedProjectId, display, instruction)
    }
  }

  const handleDirectQuestion = () => {
    setShowWelcome(false)
  }

  return (
    <div className="flex flex-1 flex-col min-h-0">
      <ProjectHeader />
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {projectMessages.length === 0 && isReady && showWelcome ? (
          <HandoverWelcome onHandover={handleHandover} onDirectQuestion={handleDirectQuestion} />
        ) : projectMessages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-slate-500">
            <MessageSquare size={48} className="mb-4" />
            <p className="text-lg">프로젝트에 대해 질문해보세요</p>
            <p className="text-sm text-slate-600">
              코드 구조, 기능, 사용 방법 등 무엇이든 물어보세요
            </p>
          </div>
        ) : (
          projectMessages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSend={handleSend} disabled={streaming || !isReady} />
    </div>
  )
}
