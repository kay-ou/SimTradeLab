import { useState, useEffect } from "react";
import { Modal, Form, Input, Button, Space, Typography, Alert } from "antd";
import { FolderOpenOutlined } from "@ant-design/icons";

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
    (window as any).electronAPI.getConfig().then((cfg: any) => {
      setDataPath(cfg.dataPath ?? "");
      setStrategiesPath(cfg.strategiesPath ?? "");
    });
  }, [open]);

  async function pickFolder(setter: (v: string) => void) {
    const path = await (window as any).electronAPI.openFolderDialog();
    if (path) setter(path);
  }

  async function handleSave() {
    setSaving(true);
    try {
      // 更新 server 端路径
      const port = await (window as any).electronAPI.getServerPort();
      await fetch(`http://127.0.0.1:${port}/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data_path: dataPath,
          strategies_path: strategiesPath,
        }),
      });
      // 持久化到本地配置
      await (window as any).electronAPI.saveConfig({
        dataPath,
        strategiesPath,
      });
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
