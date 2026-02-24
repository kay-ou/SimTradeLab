import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import { Button, Space, message, Tag, theme, Tooltip } from "antd";
import { SaveOutlined } from "@ant-design/icons";
import { strategiesAPI } from "../services/api";
import { isMac } from "../utils/platform";

interface Props {
  strategyName: string | null;
  isDark?: boolean;
  sourceOverride?: string;
}

export function EditorPanel({ strategyName, isDark, sourceOverride }: Props) {
  const { token } = theme.useToken();
  const [source, setSource] = useState("");
  const [saved, setSaved] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!strategyName) return;
    if (sourceOverride !== undefined) {
      setSource(sourceOverride);
      setSaved(true);
      return;
    }
    setLoading(true);
    strategiesAPI
      .get(strategyName)
      .then((s) => {
        setSource(s.source);
        setSaved(true);
      })
      .finally(() => setLoading(false));
  }, [strategyName, sourceOverride]);

  const handleSave = async () => {
    if (!strategyName) return;
    try {
      await strategiesAPI.save(strategyName, source);
      message.success("已保存");
      setSaved(true);
    } catch {
      message.error("保存失败");
    }
  };

  const handleKeyDown = (event: KeyboardEvent) => {
    // Check for Ctrl+S (Windows/Linux) or Cmd+S (macOS)
    if ((event.ctrlKey || (isMac && event.metaKey)) && event.key === 's') {
      event.preventDefault(); // Prevent default browser save dialog
      handleSave();
      // Show a brief message to indicate the shortcut was used
      message.info("使用 Ctrl+S 保存策略");
    }
  };

  useEffect(() => {
    // Add keyboard event listener
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      // Clean up event listener on component unmount
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [strategyName, source, handleSave]);

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
        从左侧选择或新建策略
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
        }}
      >
        <Space>
          <span style={{ fontWeight: 600 }}>{strategyName}</span>
          {!saved && <Tag color="orange">未保存</Tag>}
        </Space>
        <Tooltip title={`保存策略 (${isMac ? "⌘" : "Ctrl"}+S)`}>
          <Button
            size="small"
            icon={<SaveOutlined />}
            onClick={handleSave}
            type={saved ? "default" : "primary"}
          >
            保存
          </Button>
        </Tooltip>
      </div>
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
