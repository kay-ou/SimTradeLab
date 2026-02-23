import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const api = {
  getServerPort: (): Promise<number> => ipcRenderer.invoke('get-server-port'),
  getConfig: (): Promise<{ dataPath?: string; strategiesPath?: string }> =>
    ipcRenderer.invoke('get-config'),
  saveConfig: (config: { dataPath?: string; strategiesPath?: string }): Promise<void> =>
    ipcRenderer.invoke('save-config', config),
  openFolderDialog: (): Promise<string | null> => ipcRenderer.invoke('open-folder-dialog'),
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('electronAPI', api)
  } catch (error) {
    console.error(error)
  }
} else {
  window.electron = electronAPI
  ;(window as any).electronAPI = api
}
