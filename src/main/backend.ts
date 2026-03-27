import { spawn, execSync, ChildProcess } from 'child_process'
import { join } from 'path'
import { existsSync } from 'fs'
import { app } from 'electron'
import { is } from '@electron-toolkit/utils'

let backendProcess: ChildProcess | null = null
const BACKEND_PORT = 8932
const HEALTH_CHECK_URL = `http://localhost:${BACKEND_PORT}/health`

export function getBackendPort(): number {
  return BACKEND_PORT
}

function getPythonCmd(): string {
  return process.platform === 'win32' ? 'python' : 'python3'
}

function ensureDependencies(backendDir: string): void {
  const reqFile = join(backendDir, 'requirements.txt')
  if (!existsSync(reqFile)) return

  // Check if FastAPI is importable as a quick dependency check
  try {
    execSync(`${getPythonCmd()} -c "import fastapi"`, {
      cwd: backendDir,
      stdio: 'ignore',
      timeout: 10000
    })
  } catch {
    console.log('[Backend] Installing Python dependencies...')
    try {
      execSync(`${getPythonCmd()} -m pip install -r requirements.txt --quiet`, {
        cwd: backendDir,
        stdio: 'inherit',
        timeout: 300000
      })
      console.log('[Backend] Dependencies installed')
    } catch (err) {
      console.error('[Backend] Failed to install dependencies:', err)
    }
  }
}

export async function startBackend(): Promise<void> {
  let cmd: string
  let args: string[]
  let cwd: string

  if (is.dev) {
    const backendDir = join(__dirname, '../../backend')
    ensureDependencies(backendDir)
    cmd = getPythonCmd()
    args = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)]
    cwd = backendDir
  } else {
    const backendDir = join(process.resourcesPath, 'backend')
    const exeName = process.platform === 'win32' ? 'backend.exe' : 'backend'
    cmd = join(backendDir, exeName)
    args = ['--host', '127.0.0.1', '--port', String(BACKEND_PORT)]
    cwd = backendDir
  }

  backendProcess = spawn(cmd, args, {
    cwd,
    env: {
      ...process.env,
      DATA_DIR: join(app.getPath('userData'), 'data'),
      PYTHONUNBUFFERED: '1',
      // Ensure DLLs next to the exe are found (onedir mode)
      PATH: `${cwd}${process.platform === 'win32' ? ';' : ':'}${process.env.PATH ?? ''}`
    },
    stdio: ['ignore', 'pipe', 'pipe']
  })

  backendProcess.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data}`)
  })

  backendProcess.stderr?.on('data', (data) => {
    console.error(`[Backend] ${data}`)
  })

  backendProcess.on('exit', (code) => {
    console.log(`[Backend] Process exited with code ${code}`)
    backendProcess = null
  })

  await waitForBackend()
}

async function waitForBackend(maxRetries = 30, intervalMs = 1000): Promise<void> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(HEALTH_CHECK_URL)
      if (response.ok) {
        console.log('[Backend] Ready')
        return
      }
    } catch {
      // Backend not ready yet
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
  console.error('[Backend] Failed to start within timeout')
}

export function stopBackend(): void {
  if (backendProcess) {
    console.log('[Backend] Stopping...')
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t'])
    } else {
      backendProcess.kill('SIGTERM')
    }
    backendProcess = null
  }
}
