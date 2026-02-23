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
} from "antd";
import { PlayCircleOutlined, StopOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { backtestAPI } from "../services/api";

interface RunParams {
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  frequency: string;
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
      };
      const { task_id } = await backtestAPI.run({
        ...params,
        enable_charts: true,
        sandbox: true,
      });
      onTaskStarted(task_id, params, Date.now());
    } catch (e: any) {
      setError(e.response?.data?.detail || "启动失败");
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
      <Form
        form={form}
        layout="inline"
        size="small"
        initialValues={{
          start_date: dayjs("2025-01-01"),
          end_date: dayjs("2025-12-31"),
          initial_capital: 100000,
          frequency: "1d",
        }}
      >
        <Form.Item name="start_date" label="开始" rules={[{ required: true }]}>
          <DatePicker />
        </Form.Item>
        <Form.Item name="end_date" label="结束" rules={[{ required: true }]}>
          <DatePicker />
        </Form.Item>
        <Form.Item name="initial_capital" label="本金">
          <InputNumber min={1000} step={10000} style={{ width: 120 }} />
        </Form.Item>
        <Form.Item name="frequency" label="频率">
          <Select
            style={{ width: 70 }}
            options={[
              { value: "1d", label: "日线" },
              { value: "1m", label: "分钟" },
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
              运行
            </Button>
            {runningTaskId && (
              <Button danger icon={<StopOutlined />} onClick={handleCancel}>
                取消
              </Button>
            )}
          </Space>
        </Form.Item>
      </Form>
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
