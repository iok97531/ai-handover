/// <reference types="vite/client" />

interface Window {
  electron: import('@electron-toolkit/preload').ElectronAPI
  api: {
    selectFolder: () => Promise<string | null>
    getBackendPort: () => Promise<number>
  }
}
