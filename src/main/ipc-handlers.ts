import { ipcMain, dialog } from 'electron'
import { getBackendPort } from './backend'

export function setupIpcHandlers(): void {
  ipcMain.handle('select-folder', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory'],
      title: '프로젝트 폴더 선택'
    })
    if (result.canceled) return null
    return result.filePaths[0]
  })

  ipcMain.handle('get-backend-port', () => {
    return getBackendPort()
  })
}
