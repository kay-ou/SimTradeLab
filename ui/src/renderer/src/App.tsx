import { useState, useCallback } from 'react'
import { ConfigProvider, Layout, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { StrategyPanel } from './components/StrategyPanel'
import { EditorPanel } from './components/EditorPanel'
import { RunPanel } from './components/RunPanel'
import { LogConsole } from './components/LogConsole'
import { ResultPanel } from './components/ResultPanel'
import { createLogStream } from './services/backtest.ws'
import { backtestAPI, getWSBaseURL } from './services/api'
import type { LogMessage } from './components/LogConsole'

const { Header, Content } = Layout

export default function App() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null)
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null)
  const [logs, setLogs] = useState<LogMessage[]>([])
  const [result, setResult] = useState<any | null>(null)

  const handleTaskStarted = useCallback(async (taskId: string) => {
    setRunningTaskId(taskId)
    setLogs([])
    setResult(null)

    const base = await getWSBaseURL()

    createLogStream(
      base,
      taskId,
      (msg) => setLogs((prev) => [...prev, msg]),
      async () => {
        setRunningTaskId(null)
        try {
          const res = await backtestAPI.result(taskId)
          setResult(res)
        } catch {
          // task failed
        }
      }
    )
  }, [])

  return (
    <ConfigProvider locale={zhCN} theme={{ algorithm: theme.defaultAlgorithm }}>
      <Layout style={{ height: '100vh', overflow: 'hidden' }}>
        <Header style={{
          background: '#141414', color: '#fff', padding: '0 16px',
          height: 40, lineHeight: '40px', fontSize: 14, flexShrink: 0
        }}>
          SimTradeLab
        </Header>

        <RunPanel
          strategyName={selectedStrategy}
          onTaskStarted={handleTaskStarted}
          runningTaskId={runningTaskId}
        />

        <Content style={{ display: 'flex', overflow: 'hidden', flex: 1 }}>
          {/* 左栏：策略列表 */}
          <div style={{ width: 220, borderRight: '1px solid #f0f0f0', flexShrink: 0, overflow: 'hidden' }}>
            <StrategyPanel selected={selectedStrategy} onSelect={setSelectedStrategy} />
          </div>

          {/* 中栏：编辑器 + 日志 */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ flex: '0 0 60%', overflow: 'hidden' }}>
              <EditorPanel strategyName={selectedStrategy} />
            </div>
            <div style={{ flex: 1, borderTop: '1px solid #333', overflow: 'hidden' }}>
              <LogConsole logs={logs} />
            </div>
          </div>

          {/* 右栏：结果 */}
          <div style={{ width: 380, borderLeft: '1px solid #f0f0f0', flexShrink: 0, overflow: 'hidden' }}>
            <ResultPanel result={result} />
          </div>
        </Content>
      </Layout>
    </ConfigProvider>
  )
}
