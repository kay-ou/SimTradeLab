import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import { Button, Space, message, Tag, theme, Alert } from "antd";
import {
  SaveOutlined,
  PlayCircleOutlined,
  StopOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { optimizerAPI } from "../services/api";

interface Props {
  strategyName: string | null;
  isDark?: boolean;
  runningTaskId: string | null;
  onTaskStarted: (taskId: string) => void;
  editorFontSize?: number;
}

export function OptimizerPanel({
  strategyName,
  isDark,
  runningTaskId,
  onTaskStarted,
  editorFontSize = 13,
}: Props) {
  const { token } = theme.useToken();
  const { t } = useTranslation();
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
      message.success(t("optimizer.saved"));
      setSaved(true);
    } catch {
      message.error(t("optimizer.saveFailed"));
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
        message.error(t("optimizer.saveBeforeRun"));
        return;
      }
    }
    setRunning(true);
    setError(null);
    try {
      const { task_id } = await optimizerAPI.run(strategyName);
      onTaskStarted(task_id);
    } catch (e: any) {
      setError(e.response?.data?.detail || t("optimizer.startFailed"));
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
        {t("optimizer.selectStrategy")}
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
          {!saved && <Tag color="orange">{t("optimizer.unsaved")}</Tag>}
        </Space>
        <Space>
          <Button
            size="small"
            icon={<SaveOutlined />}
            onClick={handleSave}
            type={saved ? "default" : "primary"}
          >
            {t("btn.save")}
          </Button>
          {runningTaskId ? (
            <Button
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={handleCancel}
            >
              {t("optimizer.btn.cancel")}
            </Button>
          ) : (
            <Button
              size="small"
              type="primary"
              icon={<PlayCircleOutlined />}
              loading={running}
              onClick={handleRun}
            >
              {t("optimizer.btn.run")}
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
        loading={loading ? t("optimizer.loading") : undefined}
        theme={isDark ? "vs-dark" : "vs-light"}
        options={{
          fontSize: editorFontSize,
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
