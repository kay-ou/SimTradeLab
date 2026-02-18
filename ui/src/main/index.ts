import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { spawn, ChildProcess } from 'child_process'
import * as net from 'net'
import * as http from 'http'

let serverProcess: ChildProcess | null = null
let serverPort = 8000

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
      const req = http.get(`http://127.0.0.1:${port}/strategies`, (res) => {
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

async function startServer(port: number): Promise<void> {
  const isDev = is.dev

  if (isDev) {
    serverProcess = spawn('poetry', ['run', 'simtradelab', 'serve', '--port', String(port)], {
      cwd: join(__dirname, '../../..'),
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env }
    })
  } else {
    const serverBin = join(
      process.resourcesPath,
      'server',
      process.platform === 'win32' ? 'simtradelab-server.exe' : 'simtradelab-server'
    )
    serverProcess = spawn(serverBin, ['serve', '--port', String(port)], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env }
    })
  }

  serverProcess.stdout?.on('data', (d: Buffer) => console.log('[server]', d.toString().trim()))
  serverProcess.stderr?.on('data', (d: Buffer) => console.error('[server]', d.toString().trim()))
  serverProcess.on('error', (err: Error) => console.error('[server error]', err))

  await waitForServer(port)
}

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

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.simtradelab')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  ipcMain.handle('get-server-port', () => serverPort)

  try {
    serverPort = await findFreePort()
    await startServer(serverPort)
    console.log(`[main] Server started on port ${serverPort}`)
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
