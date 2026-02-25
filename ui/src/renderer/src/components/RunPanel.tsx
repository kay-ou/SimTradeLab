import { useState } from "react";
import {
  Form,
  DatePicker,
  InputNumber,
  Select,
  Button,
  Space,
  Alert,
  theme,
  ConfigProvider,
} from "antd";
import { PlayCircleOutlined, StopOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import dayjs from "dayjs";
import { backtestAPI } from "../services/api";

interface RunParams {
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  frequency: string;
  benchmark_code: string;
}

interface Props {
  strategyName: string | null;
  onTaskStarted: (taskId: string, params: RunParams, startedAt: number) => void;
  runningTaskId: string | null;
}

export function RunPanel({
  strategyName,
  onTaskStarted,
  runningTaskId,
}: Props) {
  const { token } = theme.useToken();
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    if (!strategyName) return;
    const values = await form.validateFields();
    setLoading(true);
    setError(null);
    try {
      const params: RunParams = {
        strategy_name: strategyName,
        start_date: values.start_date.format("YYYY-MM-DD"),
        end_date: values.end_date.format("YYYY-MM-DD"),
        initial_capital: values.initial_capital,
        frequency: values.frequency,
        benchmark_code: values.benchmark_code,
      };
      const { task_id } = await backtestAPI.run({
        ...params,
        enable_charts: true,
        sandbox: true,
      });
      onTaskStarted(task_id, params, Date.now());
    } catch (e: any) {
      setError(e.response?.data?.detail || t("run.error.start"));
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!runningTaskId) return;
    try {
      await backtestAPI.cancel(runningTaskId);
    } catch {
      // ignore
    }
  };

  return (
    <div
      style={{
        padding: "6px 12px",
        borderBottom: `1px solid ${token.colorBorderSecondary}`,
      }}
    >
      <ConfigProvider theme={{ token: { fontSize: 12 } }}>
        <Form
          form={form}
          layout="inline"
          size="small"
          initialValues={{
            start_date: dayjs("2025-01-01"),
            end_date: dayjs("2025-12-31"),
            initial_capital: 100000,
            frequency: "1d",
            benchmark_code: "000300.SS",
          }}
        >
          <Form.Item
            name="start_date"
            label={t("run.startDate")}
            rules={[{ required: true }]}
          >
            <DatePicker
              disabledDate={(d) => {
                const end = form.getFieldValue("end_date");
                return end ? d.isAfter(end, "day") : false;
              }}
            />
          </Form.Item>
          <Form.Item name="end_date" label={t("run.endDate")} rules={[{ required: true }]}>
            <DatePicker
              disabledDate={(d) => {
                const start = form.getFieldValue("start_date");
                return start ? d.isBefore(start, "day") : false;
              }}
            />
          </Form.Item>
          <Form.Item name="initial_capital" label={t("run.capital")}>
            <InputNumber min={1000} step={10000} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="frequency" label={t("run.frequency")}>
            <Select
              style={{ width: 70 }}
              options={[
                { value: "1d", label: t("run.freq.daily") },
                { value: "1m", label: t("run.freq.minute") },
              ]}
            />
          </Form.Item>
          <Form.Item name="benchmark_code" label={t("run.benchmark")}>
            <Select
              style={{ width: 120 }}
              options={[
                { value: "000300.SS", label: t("run.bench.hs300") },
                { value: "000905.SS", label: t("run.bench.zz500") },
                { value: "000852.SS", label: t("run.bench.zz1000") },
                { value: "399001.SZ", label: t("run.bench.sz") },
                { value: "399006.SZ", label: t("run.bench.cyb") },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                loading={loading}
                disabled={!strategyName || !!runningTaskId}
                onClick={handleRun}
              >
                {t("run.btn.run")}
              </Button>
              {runningTaskId && (
                <Button danger icon={<StopOutlined />} onClick={handleCancel}>
                  {t("run.btn.cancel")}
                </Button>
              )}
            </Space>
          </Form.Item>
        </Form>
      </ConfigProvider>
      {error && (
        <Alert
          type="error"
          message={error}
          style={{ marginTop: 4 }}
          closable
          onClose={() => setError(null)}
        />
      )}
    </div>
  );
}
