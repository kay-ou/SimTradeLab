import { useState, useCallback } from "react";
import { ConfigProvider, Layout, theme, Button } from "antd";
import { SettingOutlined } from "@ant-design/icons";
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

const { Header, Content } = Layout;

export default function App() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [result, setResult] = useState<any | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [strategyReloadKey, setStrategyReloadKey] = useState(0);

  const handleTaskStarted = useCallback(async (taskId: string) => {
    setRunningTaskId(taskId);
    setLogs([]);
    setResult(null);

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
        } catch {
          // task failed
        }
      },
    );
  }, []);

  return (
    <ConfigProvider locale={zhCN} theme={{ algorithm: theme.defaultAlgorithm }}>
      <Layout style={{ height: "100vh", overflow: "hidden" }}>
        <Header
          style={{
            background: "#141414",
            color: "#fff",
            padding: "0 16px",
            height: 40,
            lineHeight: "40px",
            fontSize: 14,
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>SimTradeLab</span>
          <Button
            type="text"
            icon={<SettingOutlined />}
            style={{ color: "#fff" }}
            onClick={() => setSettingsOpen(true)}
          />
        </Header>

        <RunPanel
          strategyName={selectedStrategy}
          onTaskStarted={handleTaskStarted}
          runningTaskId={runningTaskId}
        />

        <Content style={{ overflow: "hidden", flex: 1 }}>
          <Allotment>
            <Allotment.Pane minSize={120} preferredSize={220} snap>
              <StrategyPanel
                selected={selectedStrategy}
                onSelect={setSelectedStrategy}
                reloadKey={strategyReloadKey}
              />
            </Allotment.Pane>

            <Allotment.Pane minSize={300}>
              <Allotment vertical>
                <Allotment.Pane minSize={100} preferredSize="60%">
                  <EditorPanel strategyName={selectedStrategy} />
                </Allotment.Pane>
                <Allotment.Pane minSize={60} snap>
                  <LogConsole logs={logs} />
                </Allotment.Pane>
              </Allotment>
            </Allotment.Pane>

            <Allotment.Pane minSize={120} preferredSize={380} snap>
              <ResultPanel result={result} />
            </Allotment.Pane>
          </Allotment>
        </Content>

        <SettingsModal
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          onSaved={() => setStrategyReloadKey((k) => k + 1)}
        />
      </Layout>
    </ConfigProvider>
  );
}
