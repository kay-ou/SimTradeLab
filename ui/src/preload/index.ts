import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('electronAPI', {
      getServerPort: (): Promise<number> => ipcRenderer.invoke('get-server-port')
    })
  } catch (error) {
    console.error(error)
  }
} else {
  window.electron = electronAPI
  ;(window as any).electronAPI = {
    getServerPort: (): Promise<number> => ipcRenderer.invoke('get-server-port')
  }
}
