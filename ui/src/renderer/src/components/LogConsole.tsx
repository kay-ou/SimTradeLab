import { useEffect, useRef } from 'react'

export type LogMessage = { level: string; msg: string; ts: number }

const LEVEL_COLOR: Record<string, string> = {
  INFO: '#4fc3f7',
  WARNING: '#ffb74d',
  ERROR: '#ef9a9a',
  DEBUG: '#90a4ae',
  SYSTEM: '#81c784',
}

interface Props {
  logs: LogMessage[]
}

export function LogConsole({ logs }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  return (
    <div style={{
      height: '100%',
      overflowY: 'auto',
      background: '#1e1e1e',
      padding: '8px 12px',
      fontFamily: 'monospace',
      fontSize: 12,
    }}>
      {logs.length === 0 && (
        <span style={{ color: '#555' }}>等待日志输出...</span>
      )}
      {logs.map((log, i) => (
        <div key={i} style={{ color: LEVEL_COLOR[log.level] || '#d4d4d4', lineHeight: 1.8 }}>
          <span style={{ color: '#6a9955', marginRight: 8 }}>
            {new Date(log.ts * 1000).toLocaleTimeString()}
          </span>
          {log.msg}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
