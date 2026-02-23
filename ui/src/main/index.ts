import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { spawn, ChildProcess } from 'child_process'
import * as net from 'net'
import * as http from 'http'

let serverProcess: ChildProcess | null = null
let serverPort = 8000

// ── 配置持久化 ──────────────────────────────────────────────
interface AppConfig {
  dataPath?: string
  strategiesPath?: string
}

const configPath = join(app.getPath('userData'), 'config.json')

function loadConfig(): AppConfig {
  try {
    if (existsSync(configPath)) {
      return JSON.parse(readFileSync(configPath, 'utf-8'))
    }
  } catch {}
  return {}
}

function saveConfig(config: AppConfig): void {
  mkdirSync(app.getPath('userData'), { recursive: true })
  writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8')
}

// ── 自动搜索 data 目录 ──────────────────────────────────────
function findProjectRoot(): string | null {
  const candidates = [
    app.getPath('documents'),
    app.getPath('home'),
    process.cwd(),
  ]
  for (const base of candidates) {
    if (existsSync(join(base, 'SimTradeLab', 'data'))) {
      return join(base, 'SimTradeLab')
    }
    if (existsSync(join(base, 'data'))) {
      return base
    }
  }
  return null
}

// ── Server 启动 ─────────────────────────────────────────────
async function findFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address() as net.AddressInfo
      server.close(() => resolve(addr.port))
    })
    server.on('error', reject)
  })
}

function waitForServer(port: number, timeoutMs = 15000): Promise<void> {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    function attempt() {
      const req = http.get(`http://127.0.0.1:${port}/settings`, (res) => {
        if (res.statusCode === 200) {
          resolve()
        } else {
          setTimeout(attempt, 500)
        }
      })
      req.on('error', () => {
        if (Date.now() - start >= timeoutMs) {
          reject(new Error('Server start timeout'))
        } else {
          setTimeout(attempt, 500)
        }
      })
      req.setTimeout(1000, () => {
        req.destroy()
        setTimeout(attempt, 500)
      })
    }
    attempt()
  })
}

async function startServer(port: number, config: AppConfig): Promise<void> {
  const extraArgs: string[] = []
  if (config.dataPath) extraArgs.push('--data-path', config.dataPath)
  if (config.strategiesPath) extraArgs.push('--strategies-path', config.strategiesPath)

  if (is.dev) {
    serverProcess = spawn(
      'poetry',
      ['run', 'simtradelab', 'serve', '--port', String(port), ...extraArgs],
      {
        cwd: join(__dirname, '../../..'),
        stdio: ['ignore', 'pipe', 'pipe'],
        env: { ...process.env }
      }
    )
  } else {
    const serverBin = join(
      process.resourcesPath,
      'server',
      process.platform === 'win32' ? 'simtradelab-server.exe' : 'simtradelab-server'
    )
    serverProcess = spawn(serverBin, ['serve', '--port', String(port), ...extraArgs], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env }
    })
  }

  serverProcess.stdout?.on('data', (d: Buffer) => console.log('[server]', d.toString().trim()))
  serverProcess.stderr?.on('data', (d: Buffer) => console.error('[server]', d.toString().trim()))
  serverProcess.on('error', (err: Error) => console.error('[server error]', err))

  await waitForServer(port)
}

// ── 窗口 ────────────────────────────────────────────────────
function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// ── 主流程 ──────────────────────────────────────────────────
app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.simtradelab')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // 加载配置，未配置时自动搜索
  const config = loadConfig()
  if (!config.dataPath) {
    const root = findProjectRoot()
    if (root) {
      config.dataPath = join(root, 'data')
      config.strategiesPath = join(root, 'strategies')
      saveConfig(config)
    }
  }

  ipcMain.handle('get-server-port', () => serverPort)
  ipcMain.handle('get-config', () => loadConfig())
  ipcMain.handle('save-config', (_e, newConfig: AppConfig) => {
    saveConfig(newConfig)
    return newConfig
  })
  ipcMain.handle('open-folder-dialog', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory'] })
    return result.canceled ? null : result.filePaths[0]
  })

  try {
    serverPort = await findFreePort()
    await startServer(serverPort, config)
    console.log('[main] Server started on port', serverPort)
  } catch (err) {
    console.error('[main] Failed to start server:', err)
  }

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  if (serverProcess) {
    serverProcess.kill()
    serverProcess = null
  }
})
