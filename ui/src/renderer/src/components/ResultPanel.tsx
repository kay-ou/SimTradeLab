import ReactECharts from "echarts-for-react";
import {
  Card,
  Statistic,
  Row,
  Col,
  Divider,
  Table,
  Button,
  Popconfirm,
  Tag,
} from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { theme } from "antd";
import type { HistoryEntry } from "../App";

interface Props {
  result: any | null;
  history: HistoryEntry[];
  onDeleteHistory: (id: string) => void;
}

export function ResultPanel({ result, history, onDeleteHistory }: Props) {
  const { token } = theme.useToken();

  if (!result) {
    return (
      <div style={{ height: "100%", overflowY: "auto", padding: 12 }}>
        {history.length === 0 ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: token.colorTextSecondary,
              fontSize: 13,
            }}
          >
            运行回测后结果显示在此处
          </div>
        ) : (
          <>
            <Divider style={{ margin: "10px 0", fontSize: 12 }}>
              回测历史
            </Divider>
            <HistoryTable history={history} onDelete={onDeleteHistory} />
          </>
        )}
      </div>
    );
  }

  const { metrics, series } = result;

  // 日期 → 时间戳（ECharts time axis）
  const toTs = (s: string) => new Date(s).getTime();
  const dates = (series.dates as string[]).map(toTs);

  const initial = series.portfolio_values[0] || 1;
  const navValues = (series.portfolio_values as number[]).map((v, i) => [
    dates[i],
    +(v / initial).toFixed(6),
  ]);

  // 基准净值（可能长度不一致，按策略日期对齐）
  const bm: number[] = series.benchmark_nav ?? [];
  const bmValues =
    bm.length === dates.length
      ? bm.map((v: number, i: number) => [dates[i], +v.toFixed(6)])
      : [];

  // 买卖点：有成交的日期取对应净值
  const buyPoints = (series.daily_buy_amount as number[])
    .map((v, i) => (v > 0 ? [dates[i], navValues[i][1]] : null))
    .filter(Boolean);
  const sellPoints = (series.daily_sell_amount as number[])
    .map((v, i) => (v > 0 ? [dates[i], navValues[i][1]] : null))
    .filter(Boolean);

  const axisStyle = {
    type: "time" as const,
    axisLabel: {
      fontSize: 10,
      color: token.colorTextSecondary,
      hideOverlap: true,
    },
    splitLine: { lineStyle: { color: token.colorBorderSecondary } },
    axisLine: { lineStyle: { color: token.colorBorder } },
  };

  const dataZoomNav = [
    { type: "inside", xAxisIndex: 0, filterMode: "none" },
    {
      type: "slider",
      xAxisIndex: 0,
      height: 18,
      bottom: 4,
      textStyle: { fontSize: 9 },
      handleSize: "80%",
      filterMode: "none",
    },
  ];
  const dataZoomPnl = [{ type: "inside", xAxisIndex: 0, filterMode: "none" }];

  const navOption = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) =>
        params
          .map(
            (p: any) => `${p.marker}${p.seriesName}: ${p.value[1].toFixed(4)}`,
          )
          .join("<br/>"),
    },
    legend: {
      data: ["策略净值", metrics.benchmark_name || "基准"],
      bottom: 0,
      textStyle: { color: token.colorText },
    },
    grid: { top: 16, bottom: 56, left: 52, right: 16 },
    xAxis: axisStyle,
    yAxis: {
      type: "value" as const,
      scale: true,
      axisLabel: { fontSize: 10, color: token.colorTextSecondary },
      splitLine: { lineStyle: { color: token.colorBorderSecondary } },
    },
    dataZoom: dataZoomNav,
    series: [
      {
        name: "策略净值",
        type: "line",
        data: navValues,
        lineStyle: { width: 2, color: "#1677ff" },
        symbol: "none",
        z: 2,
      },
      ...(bmValues.length > 0
        ? [
            {
              name: metrics.benchmark_name || "基准",
              type: "line" as const,
              data: bmValues,
              lineStyle: { width: 1.5, color: "#aaa", type: "dashed" as const },
              symbol: "none",
              z: 1,
            },
          ]
        : []),
      {
        name: "买入",
        type: "scatter",
        data: buyPoints,
        symbol: "triangle",
        symbolSize: 8,
        itemStyle: { color: "#ef5350" },
        z: 3,
        tooltip: { show: false },
      },
      {
        name: "卖出",
        type: "scatter",
        data: sellPoints,
        symbol: "triangle",
        symbolRotate: 180,
        symbolSize: 8,
        itemStyle: { color: "#26a69a" },
        z: 3,
        tooltip: { show: false },
      },
    ],
  };

  const pnlOption = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { top: 8, bottom: 36, left: 60, right: 16 },
    xAxis: { ...axisStyle },
    yAxis: {
      type: "value" as const,
      axisLabel: { fontSize: 10, color: token.colorTextSecondary },
      splitLine: { lineStyle: { color: token.colorBorderSecondary } },
    },
    dataZoom: dataZoomPnl,
    series: [
      {
        name: "每日盈亏",
        type: "bar",
        data: (series.daily_pnl as number[]).map((v, i) => [dates[i], v]),
        itemStyle: {
          color: (p: any) => (p.value[1] >= 0 ? "#ef5350" : "#26a69a"),
        },
      },
    ],
  };

  const fmt = (v: number, pct = false) =>
    pct ? `${(v * 100).toFixed(2)}%` : v.toFixed(3);

  const statsCards = [
    {
      title: "总收益",
      value: fmt(metrics.total_return, true),
      color: metrics.total_return >= 0 ? "#cf1322" : "#3f8600",
    },
    { title: "年化收益", value: fmt(metrics.annual_return, true) },
    {
      title: "最大回撤",
      value: fmt(metrics.max_drawdown, true),
      color: "#cf1322",
    },
    { title: "夏普比率", value: fmt(metrics.sharpe_ratio) },
    { title: "胜率", value: fmt(metrics.win_rate, true) },
    { title: "超额收益", value: fmt(metrics.excess_return, true) },
  ];

  return (
    <div style={{ height: "100%", overflowY: "auto", padding: 12 }}>
      <Row gutter={[8, 8]}>
        {statsCards.map(({ title, value, color }) => (
          <Col span={8} key={title}>
            <Card size="small" styles={{ body: { padding: "8px 12px" } }}>
              <Statistic
                title={title}
                value={value}
                valueStyle={{ fontSize: 15, color }}
              />
            </Card>
          </Col>
        ))}
      </Row>
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>
        净值 vs {metrics.benchmark_name || "基准"}
      </Divider>
      <ReactECharts option={navOption} style={{ height: 220 }} />
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>每日盈亏</Divider>
      <ReactECharts option={pnlOption} style={{ height: 150 }} />

      {history.length > 0 && (
        <>
          <Divider style={{ margin: "10px 0", fontSize: 12 }}>回测历史</Divider>
          <HistoryTable history={history} onDelete={onDeleteHistory} />
        </>
      )}
    </div>
  );
}

function pct(v: number) {
  return `${(v * 100).toFixed(2)}%`;
}
function num(v: number) {
  return v.toFixed(3);
}

function HistoryTable({
  history,
  onDelete,
}: {
  history: HistoryEntry[];
  onDelete: (id: string) => void;
}) {
  const { token } = theme.useToken();

  const columns = [
    {
      title: "时间",
      dataIndex: "runAt",
      width: 80,
      render: (v: number) =>
        new Date(v).toLocaleString("zh-CN", {
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        }),
    },
    { title: "策略", dataIndex: "strategy", ellipsis: true },
    {
      title: "区间",
      key: "range",
      width: 120,
      render: (_: any, r: HistoryEntry) => `${r.startDate} ~ ${r.endDate}`,
    },
    {
      title: "总收益",
      key: "ret",
      width: 72,
      render: (_: any, r: HistoryEntry) => {
        const v = r.metrics.total_return ?? 0;
        return (
          <span
            style={{ color: v >= 0 ? token.colorError : token.colorSuccess }}
          >
            {pct(v)}
          </span>
        );
      },
    },
    {
      title: "年化",
      key: "ann",
      width: 68,
      render: (_: any, r: HistoryEntry) => pct(r.metrics.annual_return ?? 0),
    },
    {
      title: "夏普",
      key: "sharpe",
      width: 58,
      render: (_: any, r: HistoryEntry) => num(r.metrics.sharpe_ratio ?? 0),
    },
    {
      title: "回撤",
      key: "dd",
      width: 68,
      render: (_: any, r: HistoryEntry) => (
        <span style={{ color: token.colorError }}>
          {pct(r.metrics.max_drawdown ?? 0)}
        </span>
      ),
    },
    {
      title: "耗时",
      key: "dur",
      width: 56,
      render: (_: any, r: HistoryEntry) => `${r.duration.toFixed(1)}s`,
    },
    {
      title: "",
      key: "del",
      width: 32,
      render: (_: any, r: HistoryEntry) => (
        <Popconfirm title="删除此记录？" onConfirm={() => onDelete(r.id)}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <Table
      size="small"
      dataSource={history}
      columns={columns}
      rowKey="id"
      pagination={false}
      scroll={{ x: true }}
      style={{ fontSize: 11 }}
    />
  );
}
