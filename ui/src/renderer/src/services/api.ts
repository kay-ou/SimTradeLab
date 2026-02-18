import axios from 'axios'

declare global {
  interface Window {
    electronAPI?: {
      getServerPort: () => Promise<number>
    }
  }
}

let _baseURL: string | null = null

async function getBaseURL(): Promise<string> {
  if (_baseURL) return _baseURL
  if (window.electronAPI) {
    const port = await window.electronAPI.getServerPort()
    _baseURL = `http://127.0.0.1:${port}`
  } else {
    _baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  }
  return _baseURL
}

async function getClient() {
  const baseURL = await getBaseURL()
  return axios.create({ baseURL })
}

export type StrategySource = { name: string; source: string }
export type TaskStatusResp = {
  task_id: string
  status: 'pending' | 'running' | 'finished' | 'failed'
  progress: number
  started_at?: string
  finished_at?: string
  error?: string
}

export const strategiesAPI = {
  list: async (): Promise<string[]> =>
    (await (await getClient()).get('/strategies')).data,

  get: async (name: string): Promise<StrategySource> =>
    (await (await getClient()).get(`/strategies/${name}`)).data,

  save: async (name: string, source: string) =>
    (await (await getClient()).put(`/strategies/${name}`, { name, source })).data,

  create: async (name: string) =>
    (await (await getClient()).post(`/strategies/${name}`, { name })).data,

  delete: async (name: string) =>
    (await (await getClient()).delete(`/strategies/${name}`)).data,
}

export const backtestAPI = {
  run: async (params: {
    strategy_name: string
    start_date: string
    end_date: string
    initial_capital: number
    frequency: string
    enable_charts: boolean
    sandbox: boolean
  }): Promise<{ task_id: string }> =>
    (await (await getClient()).post('/backtest/run', params)).data,

  status: async (taskId: string): Promise<TaskStatusResp> =>
    (await (await getClient()).get(`/backtest/${taskId}/status`)).data,

  result: async (taskId: string) =>
    (await (await getClient()).get(`/backtest/${taskId}/result`)).data,

  cancel: async (taskId: string) =>
    (await (await getClient()).post(`/backtest/${taskId}/cancel`)).data,
}

export async function getWSBaseURL(): Promise<string> {
  const base = await getBaseURL()
  return base.replace(/^http/, 'ws')
}
