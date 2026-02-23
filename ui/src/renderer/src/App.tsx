import { useEffect, useState, useCallback, useRef } from "react";
import { ConfigProvider, theme, Button, Tooltip } from "antd";
import {
  SettingOutlined,
  SunOutlined,
  MoonOutlined,
  LaptopOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BarChartOutlined,
  CodeOutlined,
} from "@ant-design/icons";
import { Allotment } from "allotment";
import "allotment/dist/style.css";
import zhCN from "antd/locale/zh_CN";
import { StrategyPanel } from "./components/StrategyPanel";
import { EditorPanel } from "./components/EditorPanel";
import { RunPanel } from "./components/RunPanel";
import { LogConsole } from "./components/LogConsole";
import { ResultPanel } from "./components/ResultPanel";
import { SettingsModal } from "./components/SettingsModal";
import { createLogStream } from "./services/backtest.ws";
import { backtestAPI, getWSBaseURL } from "./services/api";
import type { LogMessage } from "./components/LogConsole";

type ThemeMode = "light" | "dark" | "system";

export interface HistoryEntry {
  id: string;
  strategy: string;
  startDate: string;
  endDate: string;
  capital: number;
  frequency: string;
  runAt: number; // ms timestamp
  duration: number; // seconds
  metrics: Record<string, number>;
  benchmarkName: string;
}

const HISTORY_KEY = "simtradelab_history";
const MAX_HISTORY = 200;

function loadHistory(): HistoryEntry[] {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function saveHistory(entries: HistoryEntry[]) {
  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(entries.slice(0, MAX_HISTORY)),
  );
}

function getStoredTheme(): ThemeMode {
  return (localStorage.getItem("themeMode") as ThemeMode) ?? "light";
}

export default function App() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [result, setResult] = useState<any | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [strategyReloadKey, setStrategyReloadKey] = useState(0);
  const [history, setHistory] = useState<HistoryEntry[]>(loadHistory);
  const pendingRun = useRef<{ params: any; startedAt: number } | null>(null);

  const [themeMode, setThemeMode] = useState<ThemeMode>(getStoredTheme);
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches,
  );

  const [leftVisible, setLeftVisible] = useState(true);
  const [logVisible, setLogVisible] = useState(true);
  const [rightVisible, setRightVisible] = useState(true);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const isDark = themeMode === "dark" || (themeMode === "system" && systemDark);

  const cycleTheme = () => {
    const next: ThemeMode =
      themeMode === "light"
        ? "dark"
        : themeMode === "dark"
          ? "system"
          : "light";
    setThemeMode(next);
    localStorage.setItem("themeMode", next);
  };

  const themeIcon =
    themeMode === "light" ? (
      <SunOutlined />
    ) : themeMode === "dark" ? (
      <MoonOutlined />
    ) : (
      <LaptopOutlined />
    );
  const themeLabel =
    themeMode === "light" ? "浅色" : themeMode === "dark" ? "深色" : "跟随系统";

  const handleTaskStarted = useCallback(
    async (taskId: string, params: any, startedAt: number) => {
      setRunningTaskId(taskId);
      setLogs([]);
      setResult(null);
      pendingRun.current = { params, startedAt };
      const base = await getWSBaseURL();
      createLogStream(
        base,
        taskId,
        (msg) => setLogs((prev) => [...prev, msg]),
        async () => {
          setRunningTaskId(null);
          try {
            const res = await backtestAPI.result(taskId);
            setResult(res);
            const run = pendingRun.current;
            if (run && res.metrics) {
              const entry: HistoryEntry = {
                id: taskId,
                strategy: run.params.strategy_name,
                startDate: run.params.start_date,
                endDate: run.params.end_date,
                capital: run.params.initial_capital,
                frequency: run.params.frequency,
                runAt: run.startedAt,
                duration: (Date.now() - run.startedAt) / 1000,
                metrics: res.metrics,
                benchmarkName: res.metrics.benchmark_name ?? "",
              };
              setHistory((prev) => {
                const next = [entry, ...prev];
                saveHistory(next);
                return next;
              });
            }
          } catch {
            // task failed
          }
        },
      );
    },
    [],
  );

  const deleteHistory = useCallback((id: string) => {
    setHistory((prev) => {
      const next = prev.filter((e) => e.id !== id);
      saveHistory(next);
      return next;
    });
  }, []);

  const headerBg = isDark ? "#141414" : "#fff";
  const headerColor = isDark ? "#fff" : "#000";
  const headerBorder = isDark ? "none" : "0 0 0 1px #f0f0f0";

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
      }}
    >
      <div
        style={{
          height: "100vh",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            background: headerBg,
            color: headerColor,
            padding: "0 8px 0 16px",
            height: 40,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexShrink: 0,
            boxShadow: headerBorder,
            zIndex: 10,
          }}
        >
          <span style={{ fontWeight: 600, fontSize: 14 }}>SimTradeLab</span>
          <div style={{ display: "flex", gap: 2, alignItems: "center" }}>
            <Tooltip title={leftVisible ? "折叠策略面板" : "展开策略面板"}>
              <Button
                type="text"
                size="small"
                icon={
                  leftVisible ? <MenuFoldOutlined /> : <MenuUnfoldOutlined />
                }
                style={{ color: headerColor }}
                onClick={() => setLeftVisible((v) => !v)}
              />
            </Tooltip>
            <Tooltip title={logVisible ? "折叠日志面板" : "展开日志面板"}>
              <Button
                type="text"
                size="small"
                icon={<CodeOutlined />}
                style={{ color: logVisible ? "#1677ff" : headerColor }}
                onClick={() => setLogVisible((v) => !v)}
              />
            </Tooltip>
            <Tooltip title={rightVisible ? "折叠结果面板" : "展开结果面板"}>
              <Button
                type="text"
                size="small"
                icon={<BarChartOutlined />}
                style={{ color: rightVisible ? "#1677ff" : headerColor }}
                onClick={() => setRightVisible((v) => !v)}
              />
            </Tooltip>
            <Tooltip title={`主题：${themeLabel}`}>
              <Button
                type="text"
                size="small"
                icon={themeIcon}
                style={{ color: headerColor }}
                onClick={cycleTheme}
              />
            </Tooltip>
            <Tooltip title="路径设置">
              <Button
                type="text"
                size="small"
                icon={<SettingOutlined />}
                style={{ color: headerColor }}
                onClick={() => setSettingsOpen(true)}
              />
            </Tooltip>
          </div>
        </div>

        {/* RunPanel */}
        <RunPanel
          strategyName={selectedStrategy}
          onTaskStarted={handleTaskStarted}
          runningTaskId={runningTaskId}
        />

        {/* Main content */}
        <div style={{ flex: 1, overflow: "hidden" }}>
          <Allotment>
            <Allotment.Pane
              minSize={0}
              preferredSize={220}
              snap
              visible={leftVisible}
            >
              <StrategyPanel
                selected={selectedStrategy}
                onSelect={setSelectedStrategy}
                reloadKey={strategyReloadKey}
              />
            </Allotment.Pane>

            <Allotment.Pane minSize={200}>
              <Allotment vertical>
                <Allotment.Pane minSize={80}>
                  <EditorPanel strategyName={selectedStrategy} />
                </Allotment.Pane>
                <Allotment.Pane
                  minSize={0}
                  preferredSize="35%"
                  snap
                  visible={logVisible}
                >
                  <LogConsole logs={logs} isDark={isDark} />
                </Allotment.Pane>
              </Allotment>
            </Allotment.Pane>

            <Allotment.Pane
              minSize={0}
              preferredSize={380}
              snap
              visible={rightVisible}
            >
              <ResultPanel
                result={result}
                history={history}
                onDeleteHistory={deleteHistory}
              />
            </Allotment.Pane>
          </Allotment>
        </div>

        <SettingsModal
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          onSaved={() => setStrategyReloadKey((k) => k + 1)}
        />
      </div>
    </ConfigProvider>
  );
}
