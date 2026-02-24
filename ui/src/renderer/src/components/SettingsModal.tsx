import { useState, useEffect } from "react";
import { Modal, Form, Input, Button, Space, Typography, Alert } from "antd";
import { FolderOpenOutlined } from "@ant-design/icons";
import { getBaseURL } from "../services/api";

const { Text } = Typography;

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved?: () => void;
}

export function SettingsModal({ open, onClose, onSaved }: Props) {
  const [dataPath, setDataPath] = useState("");
  const [strategiesPath, setStrategiesPath] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!open) return;
    if (window.electronAPI) {
      window.electronAPI.getConfig().then((cfg) => {
        setDataPath(cfg.dataPath ?? "");
        setStrategiesPath(cfg.strategiesPath ?? "");
      });
    } else {
      getBaseURL().then((base) => {
        fetch(`${base}/settings`)
          .then((r) => r.json())
          .then((cfg) => {
            setDataPath(cfg.data_path ?? "");
            setStrategiesPath(cfg.strategies_path ?? "");
          });
      });
    }
  }, [open]);

  async function pickFolder(setter: (v: string) => void) {
    if (!window.electronAPI) return;
    const path = await window.electronAPI.openFolderDialog();
    if (path) setter(path);
  }

  async function handleSave() {
    setSaving(true);
    try {
      const base = await getBaseURL();
      await fetch(`${base}/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data_path: dataPath,
          strategies_path: strategiesPath,
        }),
      });
      if (window.electronAPI) {
        await window.electronAPI.saveConfig({ dataPath, strategiesPath });
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      onSaved?.();
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      title="路径设置"
      open={open}
      onCancel={onClose}
      footer={null}
      width={560}
    >
      <Form layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item label="数据目录">
          <Space.Compact style={{ width: "100%" }}>
            <Input
              value={dataPath}
              onChange={(e) => setDataPath(e.target.value)}
              placeholder="选择或输入 data/ 目录路径"
            />
            <Button
              icon={<FolderOpenOutlined />}
              onClick={() => pickFolder(setDataPath)}
              disabled={!window.electronAPI}
            />
          </Space.Compact>
          <Text type="secondary" style={{ fontSize: 12 }}>
            包含 stocks/、manifest.json 等数据文件的目录
          </Text>
        </Form.Item>

        <Form.Item label="策略目录">
          <Space.Compact style={{ width: "100%" }}>
            <Input
              value={strategiesPath}
              onChange={(e) => setStrategiesPath(e.target.value)}
              placeholder="选择或输入 strategies/ 目录路径"
            />
            <Button
              icon={<FolderOpenOutlined />}
              onClick={() => pickFolder(setStrategiesPath)}
              disabled={!window.electronAPI}
            />
          </Space.Compact>
          <Text type="secondary" style={{ fontSize: 12 }}>
            包含策略子目录的目录
          </Text>
        </Form.Item>

        {saved && (
          <Alert
            message="保存成功，当前会话立即生效"
            type="success"
            showIcon
            style={{ marginBottom: 12 }}
          />
        )}

        <div style={{ textAlign: "right" }}>
          <Space>
            <Button onClick={onClose}>取消</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>
              保存
            </Button>
          </Space>
        </div>
      </Form>
    </Modal>
  );
}
