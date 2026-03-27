import type { ChatMessage } from '../../types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { User, Bot, Copy, Check } from 'lucide-react'
import { useState } from 'react'

interface MessageBubbleProps {
  message: ChatMessage
}

function CodeBlock({ className, children }: { className?: string; children?: React.ReactNode }) {
  const [copied, setCopied] = useState(false)
  const match = /language-(\w+)/.exec(className || '')
  const code = String(children).replace(/\n$/, '')

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!match) {
    return (
      <code className="rounded bg-slate-900 px-1.5 py-0.5 text-xs text-emerald-400">
        {children}
      </code>
    )
  }

  return (
    <div className="group relative my-2">
      <div className="flex items-center justify-between rounded-t-lg bg-slate-900 px-3 py-1">
        <span className="text-xs text-slate-500">{match[1]}</span>
        <button
          onClick={handleCopy}
          className="text-slate-500 transition hover:text-white"
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={match[1]}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderTopLeftRadius: 0,
          borderTopRightRadius: 0,
          fontSize: '0.8rem'
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`mb-4 flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600">
          <Bot size={16} />
        </div>
      )}
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
          isUser ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-200'
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none [&_pre]:bg-transparent [&_pre]:p-0">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code: ({ className, children }) => (
                  <CodeBlock className={className}>{children}</CodeBlock>
                )
              }}
            >
              {message.content || '...'}
            </ReactMarkdown>
          </div>
        )}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 border-t border-slate-700 pt-2">
            <p className="mb-1 text-xs text-slate-400">참조 파일:</p>
            {message.sources.map((src, i) => (
              <span key={i} className="mr-2 text-xs text-blue-400">
                {src.file_path}:{src.line_start}
              </span>
            ))}
          </div>
        )}
      </div>
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700">
          <User size={16} />
        </div>
      )}
    </div>
  )
}
