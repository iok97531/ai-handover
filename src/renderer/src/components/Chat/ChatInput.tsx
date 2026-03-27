import { useState, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled: boolean
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')

  const handleSend = () => {
    const trimmed = input.trim()
    if (trimmed && !disabled) {
      onSend(trimmed)
      setInput('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-slate-700 p-4">
      <div className="flex items-end gap-2 rounded-xl bg-slate-800 p-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="프로젝트에 대해 질문하세요..."
          rows={1}
          className="max-h-32 flex-1 resize-none bg-transparent px-2 py-1 text-sm text-white placeholder-slate-500 outline-none"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="rounded-lg bg-blue-600 p-2 text-white transition hover:bg-blue-700 disabled:opacity-40"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
