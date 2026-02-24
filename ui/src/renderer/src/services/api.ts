import axios from "axios";

declare global {
  interface Window {
    electronAPI?: {
      getServerPort: () => Promise<number>;
    };
  }
}

let _baseURL: string | null = null;

async function getBaseURL(): Promise<string> {
  if (_baseURL) return _baseURL;
  if (window.electronAPI) {
    const port = await window.electronAPI.getServerPort();
    _baseURL = `http://127.0.0.1:${port}`;
  } else {
    _baseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  }
  return _baseURL;
}

async function getClient() {
  const baseURL = await getBaseURL();
  return axios.create({ baseURL });
}

export type StrategySource = { name: string; source: string };
export type TaskStatusResp = {
  task_id: string;
  status: "pending" | "running" | "finished" | "failed";
  progress: number;
  started_at?: string;
  finished_at?: string;
  error?: string;
};
export type LogMessage = { level: string; msg: string; ts: number };
export type HistoryEntry = {
  id: string;
  strategy: string;
  startDate: string;
  endDate: string;
  capital: number;
  frequency: string;
  runAt: number;
  duration: number;
  metrics: Record<string, any>;
  benchmarkName: string;
  jsonPath?: string;
  logPath?: string;
  logs?: LogMessage[]; // session-only
};

export const strategiesAPI = {
  list: async (): Promise<string[]> =>
    (await (await getClient()).get("/strategies")).data,

  get: async (name: string): Promise<StrategySource> =>
    (await (await getClient()).get(`/strategies/${name}`)).data,

  save: async (name: string, source: string) =>
    (await (await getClient()).put(`/strategies/${name}`, { name, source }))
      .data,

  create: async (name: string) =>
    (await (await getClient()).post(`/strategies/${name}`, { name })).data,

  delete: async (name: string) =>
    (await (await getClient()).delete(`/strategies/${name}`)).data,

  rename: async (name: string, newName: string) =>
    (
      await (
        await getClient()
      ).patch(`/strategies/${name}`, { new_name: newName })
    ).data,
};

export const backtestAPI = {
  run: async (params: {
    strategy_name: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    frequency: string;
    enable_charts: boolean;
    sandbox: boolean;
  }): Promise<{ task_id: string }> =>
    (await (await getClient()).post("/backtest/run", params)).data,

  status: async (taskId: string): Promise<TaskStatusResp> =>
    (await (await getClient()).get(`/backtest/${taskId}/status`)).data,

  result: async (taskId: string) =>
    (await (await getClient()).get(`/backtest/${taskId}/result`)).data,

  cancel: async (taskId: string) =>
    (await (await getClient()).post(`/backtest/${taskId}/cancel`)).data,
};

export const historyAPI = {
  list: async (): Promise<HistoryEntry[]> => {
    const data = (await (await getClient()).get("/history")).data as any[];
    return data.map((e) => ({
      id: e.task_id,
      strategy: e.strategy,
      startDate: e.start_date,
      endDate: e.end_date,
      capital: e.initial_capital,
      frequency: e.frequency,
      runAt: e.run_at * 1000,
      duration: e.duration,
      metrics: e.metrics,
      benchmarkName: e.benchmark_name,
      jsonPath: e.json_path,
      logPath: e.log_path ?? undefined,
    }));
  },

  detail: async (
    jsonPath: string,
  ): Promise<{ series: any; metrics: any; benchmark_name: string }> =>
    (
      await (
        await getClient()
      ).get("/history/detail", { params: { json_path: jsonPath } })
    ).data,

  getLog: async (logPath: string): Promise<LogMessage[]> => {
    const text: string = (
      await (
        await getClient()
      ).get("/history/log", { params: { path: logPath } })
    ).data;
    return text
      .split("\n")
      .filter(Boolean)
      .map((line) => {
        try {
          return JSON.parse(line) as LogMessage;
        } catch {
          return { level: "INFO", msg: line, ts: 0 };
        }
      });
  },

  delete: async (jsonPath: string) =>
    (
      await (
        await getClient()
      ).delete("/history", { params: { json_path: jsonPath } })
    ).data,
};

export const optimizerAPI = {
  getScript: async (
    strategyName: string,
  ): Promise<{ source: string; exists: boolean }> =>
    (await (await getClient()).get(`/optimizer/${strategyName}/script`)).data,

  saveScript: async (strategyName: string, source: string) =>
    (
      await (
        await getClient()
      ).put(`/optimizer/${strategyName}/script`, { source })
    ).data,

  run: async (strategyName: string): Promise<{ task_id: string }> =>
    (await (await getClient()).post(`/optimizer/${strategyName}/run`)).data,

  cancel: async (taskId: string) =>
    (await (await getClient()).post(`/backtest/${taskId}/cancel`)).data,
};

export async function getWSBaseURL(): Promise<string> {
  const base = await getBaseURL();
  return base.replace(/^http/, "ws");
}
