import type { Project, ChatMessage, IndexStatus, AppSettings, WatcherStatus } from '../types'

let BASE_URL = 'http://localhost:8932'

export async function initApiClient(): Promise<void> {
  try {
    const port = await window.api.getBackendPort()
    BASE_URL = `http://localhost:${port}`
  } catch {
    // Use default port
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API Error ${response.status}: ${error}`)
  }
  return response.json()
}

// Projects
export async function getProjects(): Promise<Project[]> {
  return request('/api/projects')
}

export async function createProject(name: string, folderPath: string): Promise<Project> {
  return request('/api/projects', {
    method: 'POST',
    body: JSON.stringify({ name, folder_path: folderPath })
  })
}

export async function deleteProject(projectId: string): Promise<void> {
  await request(`/api/projects/${projectId}`, { method: 'DELETE' })
}

// Indexing
export async function triggerIndex(projectId: string): Promise<void> {
  await request(`/api/index/trigger/${projectId}`, { method: 'POST' })
}

export async function getIndexStatus(projectId: string): Promise<IndexStatus> {
  return request(`/api/index/status/${projectId}`)
}

// Chat (SSE streaming)
export async function* streamChat(
  projectId: string,
  question: string,
  chatHistory: ChatMessage[]
): AsyncGenerator<string> {
  const response = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_id: projectId,
      question,
      chat_history: chatHistory.map((m) => ({ role: m.role, content: m.content }))
    })
  })

  if (!response.ok) throw new Error(`Chat API Error: ${response.status}`)

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // Process complete lines, keep partial line in buffer
    const lines = buffer.split(/\r?\n/)
    buffer = lines.pop() || '' // Last element may be incomplete

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim()
        if (data === '[DONE]') return
        if (data.startsWith('{')) {
          try {
            const parsed = JSON.parse(data)
            if (parsed.token) yield parsed.token
            if (parsed.error) throw new Error(parsed.error)
          } catch (e) {
            if (e instanceof SyntaxError) continue // Malformed JSON, skip
            throw e
          }
        }
      }
    }
  }

  // Process any remaining buffer
  if (buffer.startsWith('data: ')) {
    const data = buffer.slice(6).trim()
    if (data.startsWith('{')) {
      try {
        const parsed = JSON.parse(data)
        if (parsed.token) yield parsed.token
      } catch {
        // ignore
      }
    }
  }
}

// Watcher
export async function getWatcherEvents(projectId: string): Promise<WatcherStatus> {
  return request(`/api/index/watcher/events/${projectId}`)
}

// Settings
export async function getSettings(): Promise<AppSettings> {
  return request('/api/settings')
}

export async function updateSettings(settings: Partial<AppSettings>): Promise<AppSettings> {
  return request('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(settings)
  })
}
