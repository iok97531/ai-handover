import { Tray, Menu, BrowserWindow, nativeImage } from 'electron'

let tray: Tray | null = null

export function setupTray(mainWindow: BrowserWindow): void {
  const icon = nativeImage.createEmpty()
  tray = new Tray(icon)

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '열기',
      click: () => {
        mainWindow.show()
        mainWindow.focus()
      }
    },
    { type: 'separator' },
    {
      label: '종료',
      click: () => {
        mainWindow.destroy()
      }
    }
  ])

  tray.setToolTip('Scope')
  tray.setContextMenu(contextMenu)

  tray.on('click', () => {
    mainWindow.show()
    mainWindow.focus()
  })
}
