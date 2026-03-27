export interface Project {
  id: string
  name: string
  folder_path: string
  file_count: number
  chunk_count: number
  last_indexed: string | null
  status: 'indexing' | 'ready' | 'error' | 'pending'
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: SourceReference[]
}

export interface SourceReference {
  file_path: string
  line_start: number
  line_end: number
  snippet: string
}

export interface IndexStatus {
  project_id: string
  status: string
  files_total: number
  files_indexed: number
  progress_percent: number
}

export interface WatcherEvent {
  event_type: 'created' | 'modified' | 'deleted'
  file_path: string
  timestamp: number
}

export interface WatcherStatus {
  is_watching: boolean
  events: WatcherEvent[]
}

export interface AppSettings {
  ai_provider: 'openai' | 'claude'
  api_key: string
  chat_model?: string
  embedding_model?: string
}
