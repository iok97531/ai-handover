import { create } from 'zustand'
import type { ChatMessage } from '../types'
import { streamChat } from '../api/client'

interface ChatState {
  messages: Record<string, ChatMessage[]> // projectId -> messages
  streaming: boolean

  sendMessage: (projectId: string, question: string, hiddenInstruction?: string) => Promise<void>
  clearMessages: (projectId: string) => void
}

function createMessageId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2)
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: {},
  streaming: false,

  sendMessage: async (projectId, question, hiddenInstruction) => {
    const userMsg: ChatMessage = {
      id: createMessageId(),
      role: 'user',
      content: question,
      timestamp: new Date().toISOString()
    }

    const assistantMsg: ChatMessage = {
      id: createMessageId(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    }

    set((state) => ({
      messages: {
        ...state.messages,
        [projectId]: [...(state.messages[projectId] || []), userMsg, assistantMsg]
      },
      streaming: true
    }))

    try {
      const history = get().messages[projectId]?.slice(0, -1) || []
      const apiQuestion = hiddenInstruction ? `${question}\n\n${hiddenInstruction}` : question
      for await (const token of streamChat(projectId, apiQuestion, history)) {
        set((state) => {
          const msgs = [...(state.messages[projectId] || [])]
          const lastMsg = msgs[msgs.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            msgs[msgs.length - 1] = { ...lastMsg, content: lastMsg.content + token }
          }
          return { messages: { ...state.messages, [projectId]: msgs } }
        })
      }
    } catch (err) {
      set((state) => {
        const msgs = [...(state.messages[projectId] || [])]
        const lastMsg = msgs[msgs.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          msgs[msgs.length - 1] = {
            ...lastMsg,
            content: `오류가 발생했습니다: ${(err as Error).message}`
          }
        }
        return { messages: { ...state.messages, [projectId]: msgs } }
      })
    } finally {
      set({ streaming: false })
    }
  },

  clearMessages: (projectId) => {
    set((state) => ({
      messages: { ...state.messages, [projectId]: [] }
    }))
  }
}))
