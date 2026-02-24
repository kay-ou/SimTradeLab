import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import { Button, Space, message, Tag, theme, Alert } from "antd";
import { SaveOutlined, PlayCircleOutlined, StopOutlined } from "@ant-design/icons";
import { optimizerAPI } from "../services/api";

interface Props {
  strategyName: string | null;
  isDark?: boolean;
  runningTaskId: string | null;
  onTaskStarted: (taskId: string) => void;
}

export function OptimizerPanel({
  strategyName,
  isDark,
  runningTaskId,
  onTaskStarted,
}: Props) {
  const { token } = theme.useToken();
  const [source, setSource] = useState("");
  const [saved, setSaved] = useState(true);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!strategyName) return;
    setLoading(true);
    optimizerAPI
      .getScript(strategyName)
      .then((res) => {
        setSource(res.source);
        setSaved(res.exists);
      })
      .finally(() => setLoading(false));
  }, [strategyName]);

  // When external runningTaskId clears, reset our running state
  useEffect(() => {
    if (!runningTaskId) setRunning(false);
  }, [runningTaskId]);

  const handleSave = async () => {
    if (!strategyName) return;
    try {
      await optimizerAPI.saveScript(strategyName, source);
      message.success("已保存");
      setSaved(true);
    } catch {
      message.error("保存失败");
    }
  };

  const handleRun = async () => {
    if (!strategyName || runningTaskId) return;
    if (!saved) {
      // Auto-save before running
      try {
        await optimizerAPI.saveScript(strategyName, source);
        setSaved(true);
      } catch {
        message.error("保存失败，无法启动优化");
        return;
      }
    }
    setRunning(true);
    setError(null);
    try {
      const { task_id } = await optimizerAPI.run(strategyName);
      onTaskStarted(task_id);
    } catch (e: any) {
      setError(e.response?.data?.detail || "启动失败");
      setRunning(false);
    }
  };

  const handleCancel = async () => {
    if (!runningTaskId) return;
    try {
      await optimizerAPI.cancel(runningTaskId);
    } catch {
      // ignore
    }
  };

  if (!strategyName) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: token.colorTextSecondary,
        }}
      >
        从左侧选择策略
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "4px 8px",
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          flexShrink: 0,
        }}
      >
        <Space>
          <span style={{ fontWeight: 600 }}>optimize_params.py</span>
          {!saved && <Tag color="orange">未保存</Tag>}
        </Space>
        <Space>
          <Button size="small" icon={<SaveOutlined />} onClick={handleSave} type={saved ? "default" : "primary"}>
            保存
          </Button>
          {runningTaskId ? (
            <Button size="small" danger icon={<StopOutlined />} onClick={handleCancel}>
              取消
            </Button>
          ) : (
            <Button
              size="small"
              type="primary"
              icon={<PlayCircleOutlined />}
              loading={running}
              onClick={handleRun}
            >
              运行优化
            </Button>
          )}
        </Space>
      </div>
      {error && (
        <Alert
          type="error"
          message={error}
          style={{ margin: "4px 8px" }}
          closable
          onClose={() => setError(null)}
        />
      )}
      <Editor
        height="100%"
        defaultLanguage="python"
        value={source}
        loading={loading ? "加载中..." : undefined}
        theme={isDark ? "vs-dark" : "vs-light"}
        options={{
          fontSize: 13,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: "on",
        }}
        onChange={(val) => {
          setSource(val ?? "");
          setSaved(false);
        }}
      />
    </div>
  );
}
