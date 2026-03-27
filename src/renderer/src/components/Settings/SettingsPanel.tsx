import { useState, useEffect, useRef } from 'react'
import { X, AlertTriangle } from 'lucide-react'
import * as api from '../../api/client'
import type { AppSettings } from '../../types'

interface SettingsPanelProps {
  open: boolean
  onClose: () => void
}

type ModelOption = { id: string; label: string; recommended?: string }

const MODEL_OPTIONS: Record<'openai' | 'claude', ModelOption[]> = {
  openai: [
    { id: 'gpt-4o',      label: 'GPT-4o',      recommended: '추천 · 성능/비용 균형' },
    { id: 'gpt-4o-mini', label: 'GPT-4o mini', recommended: '추천 · 저비용' },
    { id: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { id: 'o1-mini',     label: 'o1-mini' },
  ],
  claude: [
    { id: 'claude-opus-4-6',          label: 'Claude Opus 4' },
    { id: 'claude-sonnet-4-6',        label: 'Claude Sonnet 4',  recommended: '추천 · 성능/비용 균형' },
    { id: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5', recommended: '추천 · 저비용·빠름' },
  ],
}

export default function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const [settings, setSettings] = useState<AppSettings>({
    ai_provider: 'openai',
    api_key: '',
    chat_model: '',
    embedding_model: ''
  })
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [showReindexWarning, setShowReindexWarning] = useState(false)
  const originalProvider = useRef('')

  useEffect(() => {
    if (open) {
      api.getSettings().then((s) => {
        setSettings(s)
        originalProvider.current = s.ai_provider
        setShowReindexWarning(false)
      }).catch(console.error)
    }
  }, [open])

  const handleProviderChange = (provider: 'openai' | 'claude') => {
    const defaultModel = MODEL_OPTIONS[provider].find((m) => m.recommended)?.id ?? ''
    setSettings({ ...settings, ai_provider: provider, chat_model: defaultModel })
    setShowReindexWarning(provider !== originalProvider.current)
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      const result = await api.updateSettings(settings)
      setSettings(result)
      if (showReindexWarning) {
        setMessage('저장되었습니다! 임베딩 차원이 달라졌으므로 프로젝트를 다시 인덱싱해주세요.')
        originalProvider.current = settings.ai_provider
        setShowReindexWarning(false)
      } else {
        setMessage('저장되었습니다!')
        setTimeout(() => setMessage(''), 2000)
      }
    } catch (err) {
      setMessage(`오류: ${(err as Error).message}`)
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  const modelOptions = MODEL_OPTIONS[settings.ai_provider as 'openai' | 'claude'] ?? []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-slate-800 p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">설정</h2>
          <button onClick={onClose} className="rounded p-1 text-slate-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-slate-300">AI 프로바이더</label>
            <select
              value={settings.ai_provider}
              onChange={(e) => handleProviderChange(e.target.value as 'openai' | 'claude')}
              className="w-full rounded-lg bg-slate-700 px-3 py-2 text-sm text-white outline-none"
            >
              <option value="openai">OpenAI</option>
              <option value="claude">Claude (Anthropic)</option>
            </select>
            {showReindexWarning && (
              <div className="mt-2 flex items-start gap-2 rounded-lg bg-amber-900/30 px-3 py-2 text-xs text-amber-300">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                <span>프로바이더를 변경하면 임베딩 차원이 달라져 기존 인덱스를 사용할 수 없습니다. 저장 후 모든 프로젝트를 다시 인덱싱해야 합니다.</span>
              </div>
            )}
          </div>

          <div>
            <label className="mb-1 block text-sm text-slate-300">API Key</label>
            <input
              type="password"
              value={settings.api_key}
              onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
              placeholder={settings.ai_provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
              className="w-full rounded-lg bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-500 outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm text-slate-300">채팅 모델</label>
            <select
              value={settings.chat_model || ''}
              onChange={(e) => setSettings({ ...settings, chat_model: e.target.value })}
              className="w-full rounded-lg bg-slate-700 px-3 py-2 text-sm text-white outline-none"
            >
              {modelOptions.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}{m.recommended ? `  ✦ ${m.recommended}` : ''}
                </option>
              ))}
            </select>
            {modelOptions.find((m) => m.id === settings.chat_model)?.recommended && (
              <p className="mt-1 text-xs text-blue-400">
                ✦ {modelOptions.find((m) => m.id === settings.chat_model)!.recommended}
              </p>
            )}
          </div>

          {message && (
            <p className={`text-sm ${message.startsWith('오류') ? 'text-red-400' : 'text-green-400'}`}>
              {message}
            </p>
          )}

          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full rounded-lg bg-blue-600 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? '저장 중...' : '저장'}
          </button>
        </div>
      </div>
    </div>
  )
}
