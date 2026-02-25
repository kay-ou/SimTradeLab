import { useState, useEffect } from "react";
import {
  Modal,
  Form,
  Input,
  Button,
  Space,
  Typography,
  Alert,
  Slider,
  InputNumber,
  Row,
  Col,
  Divider,
  Select,
} from "antd";
import { FolderOpenOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { getBaseURL } from "../services/api";

const { Text } = Typography;

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved?: () => void;
  globalFontSize: number;
  onGlobalFontSizeChange: (v: number) => void;
  language: "zh" | "en" | "de";
  onLanguageChange: (lang: "zh" | "en" | "de") => void;
}

export function SettingsModal({
  open,
  onClose,
  onSaved,
  globalFontSize,
  onGlobalFontSizeChange,
  language,
  onLanguageChange,
}: Props) {
  const { t } = useTranslation();
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
    <Modal title={t("settings.title")} open={open} onCancel={onClose} footer={null} width={560}>
      <Form layout="vertical" style={{ marginTop: 16 }}>
        <Divider orientation="left" style={{ fontSize: 12, margin: "0 0 12px 0" }}>
          {t("settings.section.ui")}
        </Divider>

        <Form.Item label={t("settings.fontSize")}>
          <Row gutter={12} align="middle">
            <Col flex="auto">
              <Slider
                min={12}
                max={18}
                value={globalFontSize}
                onChange={onGlobalFontSizeChange}
              />
            </Col>
            <Col>
              <InputNumber
                min={12}
                max={18}
                value={globalFontSize}
                onChange={(v) => v != null && onGlobalFontSizeChange(v)}
                style={{ width: 60 }}
              />
            </Col>
          </Row>
        </Form.Item>

        <Form.Item label={t("settings.language")}>
          <Select
            value={language}
            onChange={onLanguageChange}
            style={{ width: 120 }}
          >
            <Select.Option value="zh">中文</Select.Option>
            <Select.Option value="en">English</Select.Option>
            <Select.Option value="de">Deutsch</Select.Option>
          </Select>
        </Form.Item>

        <Divider orientation="left" style={{ fontSize: 12, margin: "4px 0 12px 0" }}>
          {t("settings.section.paths")}
        </Divider>

        <Form.Item label={t("settings.dataDir")}>
          <Space.Compact style={{ width: "100%" }}>
            <Input
              value={dataPath}
              onChange={(e) => setDataPath(e.target.value)}
              placeholder={t("settings.dataDir.placeholder")}
            />
            <Button
              icon={<FolderOpenOutlined />}
              onClick={() => pickFolder(setDataPath)}
              disabled={!window.electronAPI}
            />
          </Space.Compact>
          <Text type="secondary">{t("settings.dataDir.help")}</Text>
        </Form.Item>

        <Form.Item label={t("settings.strategyDir")}>
          <Space.Compact style={{ width: "100%" }}>
            <Input
              value={strategiesPath}
              onChange={(e) => setStrategiesPath(e.target.value)}
              placeholder={t("settings.strategyDir.placeholder")}
            />
            <Button
              icon={<FolderOpenOutlined />}
              onClick={() => pickFolder(setStrategiesPath)}
              disabled={!window.electronAPI}
            />
          </Space.Compact>
          <Text type="secondary">{t("settings.strategyDir.help")}</Text>
        </Form.Item>

        {saved && (
          <Alert
            message={t("settings.saveSuccess")}
            type="success"
            showIcon
            style={{ marginBottom: 12 }}
          />
        )}

        <div style={{ textAlign: "right" }}>
          <Space>
            <Button onClick={onClose}>{t("btn.cancel")}</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>
              {t("btn.save")}
            </Button>
          </Space>
        </div>
      </Form>
    </Modal>
  );
}
