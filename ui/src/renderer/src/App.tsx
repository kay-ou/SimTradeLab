import { useEffect, useState, useCallback, useRef } from "react";
import { ConfigProvider, theme, Button, Tooltip, Segmented } from "antd";
import {
  SettingOutlined,
  SunOutlined,
  MoonOutlined,
  LaptopOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BarChartOutlined,
  CodeOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
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
import { OptimizerPanel } from "./components/OptimizerPanel";
import { createLogStream } from "./services/backtest.ws";
import { backtestAPI, historyAPI, getWSBaseURL } from "./services/api";
import type { LogMessage } from "./components/LogConsole";
import type { HistoryEntry } from "./services/api";

export type { HistoryEntry };

type ThemeMode = "light" | "dark" | "system";
type ActiveTab = "backtest" | "optimizer";

function getStoredTheme(): ThemeMode {
  return (localStorage.getItem("themeMode") as ThemeMode) ?? "light";
}

export default function App() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [historySource, setHistorySource] = useState<string | undefined>(undefined);
  const [activeTab, setActiveTab] = useState<ActiveTab>("backtest");

  // Backtest state
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [result, setResult] = useState<any | null>(null);

  // Optimizer state
  const [optimizerTaskId, setOptimizerTaskId] = useState<string | null>(null);
  const [optimizerLogs, setOptimizerLogs] = useState<LogMessage[]>([]);

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [strategyReloadKey, setStrategyReloadKey] = useState(0);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const historyCache = useRef<Map<string, { result: any; logs: LogMessage[]; source?: string }>>(new Map());

  const prefetchHistory = useCallback((entries: HistoryEntry[]) => {
    entries.forEach(async (entry) => {
      if (historyCache.current.has(entry.id)) return;
      const cached: { result: any; logs: LogMessage[]; source?: string } = { result: null, logs: [] };
      if (entry.jsonPath) {
        try {
          const detail = await historyAPI.detail(entry.jsonPath);
          cached.result = { metrics: detail.metrics, series: detail.series };
          cached.source = detail.source;
        } catch {}
      }
      if (entry.logPath) {
        try {
          cached.logs = await historyAPI.getLog(entry.logPath);
        } catch {}
      }
      historyCache.current.set(entry.id, cached);
    });
  }, []);

  // 从磁盘加载历史记录
  const refreshHistory = useCallback(() => {
    historyAPI
      .list()
      .then((entries) => {
        setHistory(entries);
        prefetchHistory(entries);
      })
      .catch(() => {});
  }, [prefetchHistory]);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

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

  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(
    null,
  );

  const handleTaskStarted = useCallback(
    async (taskId: string, _params: any, _startedAt: number) => {
      setRunningTaskId(taskId);
      setLogs([]);
      setResult(null);
      setSelectedHistoryId(null);
      const base = await getWSBaseURL();
      const logsForRun: LogMessage[] = [];
      createLogStream(
        base,
        taskId,
        (msg) => {
          logsForRun.push(msg);
          setLogs((prev) => [...prev, msg]);
        },
        async () => {
          setRunningTaskId(null);
          try {
            const res = await backtestAPI.result(taskId);
            setResult(res);
          } catch {
            // task failed
          }
          refreshHistory();
        },
      );
    },
    [refreshHistory],
  );

  const handleSelectHistory = useCallback(async (entry: HistoryEntry) => {
    setSelectedHistoryId(entry.id);
    setActiveTab("backtest");
    setSelectedStrategy(entry.strategy);

    const cached = historyCache.current.get(entry.id);
    if (cached) {
      setResult(cached.result);
      setLogs(cached.logs);
      setHistorySource(cached.source);
      return;
    }

    if (entry.jsonPath) {
      try {
        const detail = await historyAPI.detail(entry.jsonPath);
        setResult({ metrics: detail.metrics, series: detail.series });
        setHistorySource(detail.source);
      } catch {
        setResult(null);
        setHistorySource(undefined);
      }
    } else {
      setResult(null);
      setHistorySource(undefined);
    }

    if (entry.logPath) {
      try {
        setLogs(await historyAPI.getLog(entry.logPath));
      } catch {
        setLogs([]);
      }
    } else {
      setLogs([]);
    }
  }, []);

  const handleOptimizerTaskStarted = useCallback(async (taskId: string) => {
    setOptimizerTaskId(taskId);
    setOptimizerLogs([]);
    const base = await getWSBaseURL();
    createLogStream(
      base,
      taskId,
      (msg) => setOptimizerLogs((prev) => [...prev, msg]),
      () => setOptimizerTaskId(null),
    );
  }, []);

  const deleteHistory = useCallback((id: string) => {
    setHistory((prev) => {
      const entry = prev.find((e) => e.id === id);
      if (entry?.jsonPath) historyAPI.delete(entry.jsonPath).catch(() => {});
      historyCache.current.delete(id);
      return prev.filter((e) => e.id !== id);
    });
  }, []);

  const currentLogs = activeTab === "backtest" ? logs : optimizerLogs;

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
      }}
    >
      <ThemedLayout
        isDark={isDark}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedStrategy={selectedStrategy}
        setSelectedStrategy={setSelectedStrategy}
        runningTaskId={runningTaskId}
        handleTaskStarted={handleTaskStarted}
        optimizerTaskId={optimizerTaskId}
        handleOptimizerTaskStarted={handleOptimizerTaskStarted}
        logs={currentLogs}
        result={result}
        history={history}
        deleteHistory={deleteHistory}
        selectHistory={handleSelectHistory}
        selectedHistoryId={selectedHistoryId}
        settingsOpen={settingsOpen}
        setSettingsOpen={setSettingsOpen}
        strategyReloadKey={strategyReloadKey}
        setStrategyReloadKey={setStrategyReloadKey}
        leftVisible={leftVisible}
        setLeftVisible={setLeftVisible}
        logVisible={logVisible}
        setLogVisible={setLogVisible}
        rightVisible={rightVisible}
        setRightVisible={setRightVisible}
        themeMode={themeMode}
        cycleTheme={cycleTheme}
        themeIcon={themeIcon}
        themeLabel={themeLabel}
      />
    </ConfigProvider>
  );
}

interface ThemedLayoutProps {
  isDark: boolean;
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  selectedStrategy: string | null;
  setSelectedStrategy: (s: string) => void;
  runningTaskId: string | null;
  handleTaskStarted: (taskId: string, params: any, startedAt: number) => void;
  optimizerTaskId: string | null;
  handleOptimizerTaskStarted: (taskId: string) => void;
  logs: LogMessage[];
  result: any;
  history: HistoryEntry[];
  deleteHistory: (id: string) => void;
  selectHistory: (entry: HistoryEntry) => void;
  selectedHistoryId: string | null;
  settingsOpen: boolean;
  setSettingsOpen: (v: boolean) => void;
  strategyReloadKey: number;
  setStrategyReloadKey: (fn: (k: number) => number) => void;
  leftVisible: boolean;
  setLeftVisible: (fn: (v: boolean) => boolean) => void;
  logVisible: boolean;
  setLogVisible: (fn: (v: boolean) => boolean) => void;
  rightVisible: boolean;
  setRightVisible: (fn: (v: boolean) => boolean) => void;
  themeMode: string;
  cycleTheme: () => void;
  themeIcon: React.ReactNode;
  themeLabel: string;
}

function ThemedLayout({
  isDark,
  activeTab,
  setActiveTab,
  selectedStrategy,
  setSelectedStrategy,
  runningTaskId,
  handleTaskStarted,
  optimizerTaskId,
  handleOptimizerTaskStarted,
  logs,
  result,
  history,
  deleteHistory,
  selectHistory,
  selectedHistoryId,
  settingsOpen,
  setSettingsOpen,
  strategyReloadKey,
  setStrategyReloadKey,
  leftVisible,
  setLeftVisible,
  logVisible,
  setLogVisible,
  rightVisible,
  setRightVisible,
  cycleTheme,
  themeIcon,
  themeLabel,
}: ThemedLayoutProps) {
  const { token } = theme.useToken();

  const headerColor = token.colorTextBase;

  const allotmentStyle = {
    "--separator-border": token.colorBorder,
    "--sash-hover-size": "4px",
    height: "100%",
  } as React.CSSProperties;

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        background: token.colorBgBase,
      }}
    >
      {/* Header */}
      <div
        style={{
          background: token.colorBgElevated,
          color: headerColor,
          padding: "0 8px 0 16px",
          height: 40,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          zIndex: 10,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 14, color: token.colorText }}>
          SimTradeLab
        </span>
        <Segmented
          size="small"
          value={activeTab}
          onChange={(v) => setActiveTab(v as ActiveTab)}
          options={[
            { label: "回测", value: "backtest", icon: <PlayCircleOutlined /> },
            {
              label: "优化器",
              value: "optimizer",
              icon: <ExperimentOutlined />,
            },
          ]}
        />
        <div style={{ display: "flex", gap: 2, alignItems: "center" }}>
          <Tooltip title={leftVisible ? "折叠策略面板" : "展开策略面板"}>
            <Button
              type="text"
              size="small"
              icon={leftVisible ? <MenuFoldOutlined /> : <MenuUnfoldOutlined />}
              onClick={() => setLeftVisible((v) => !v)}
            />
          </Tooltip>
          <Tooltip title={logVisible ? "折叠日志面板" : "展开日志面板"}>
            <Button
              type="text"
              size="small"
              icon={<CodeOutlined />}
              style={{ color: logVisible ? token.colorPrimary : undefined }}
              onClick={() => setLogVisible((v) => !v)}
            />
          </Tooltip>
          <Tooltip title={rightVisible ? "折叠结果面板" : "展开结果面板"}>
            <Button
              type="text"
              size="small"
              icon={<BarChartOutlined />}
              style={{ color: rightVisible ? token.colorPrimary : undefined }}
              onClick={() => setRightVisible((v) => !v)}
            />
          </Tooltip>
          <Tooltip title={`主题：${themeLabel}`}>
            <Button
              type="text"
              size="small"
              icon={themeIcon}
              onClick={cycleTheme}
            />
          </Tooltip>
          <Tooltip title="路径设置">
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => setSettingsOpen(true)}
            />
          </Tooltip>
        </div>
      </div>

      {/* RunPanel - only for backtest mode */}
      {activeTab === "backtest" && (
        <RunPanel
          strategyName={selectedStrategy}
          onTaskStarted={handleTaskStarted}
          runningTaskId={runningTaskId}
        />
      )}

      {/* Main content */}
      <div style={allotmentStyle}>
        <Allotment>
          <Allotment.Pane
            minSize={0}
            preferredSize={220}
            snap
            visible={leftVisible}
          >
            <StrategyPanel
              selected={selectedStrategy}
              onSelect={(s) => { setSelectedStrategy(s); setHistorySource(undefined); }}
              reloadKey={strategyReloadKey}
            />
          </Allotment.Pane>

          <Allotment.Pane minSize={200}>
            <Allotment vertical>
              <Allotment.Pane minSize={80}>
                {activeTab === "backtest" ? (
                  <EditorPanel
                    strategyName={selectedStrategy}
                    isDark={isDark}
                    sourceOverride={historySource}
                  />
                ) : (
                  <OptimizerPanel
                    strategyName={selectedStrategy}
                    isDark={isDark}
                    runningTaskId={optimizerTaskId}
                    onTaskStarted={handleOptimizerTaskStarted}
                  />
                )}
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
              onSelectHistory={selectHistory}
              selectedHistoryId={selectedHistoryId}
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
  );
}
