export type LogMessage = {
  level: string
  msg: string
  ts: number
}

export function createLogStream(
  wsBaseURL: string,
  taskId: string,
  onMessage: (msg: LogMessage) => void,
  onDone: () => void
): () => void {
  const ws = new WebSocket(`${wsBaseURL}/backtest/${taskId}/logs`)

  ws.onmessage = (event) => {
    const msg: LogMessage = JSON.parse(event.data)
    if (msg.msg === '__DONE__' || msg.msg === '__FAIL__') {
      onDone()
      ws.close()
    } else {
      onMessage(msg)
    }
  }

  ws.onerror = () => onDone()

  return () => {
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      ws.close()
    }
  }
}
