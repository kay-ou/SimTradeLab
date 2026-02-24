import { useState, useCallback, useRef, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import * as echarts from "echarts";
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
import { Resizable } from "react-resizable";
import "react-resizable/css/styles.css";
import type { HistoryEntry } from "../services/api";

interface Props {
  result: any | null;
  history: HistoryEntry[];
  onDeleteHistory: (id: string) => void;
  onSelectHistory?: (entry: HistoryEntry) => void;
  selectedHistoryId?: string | null;
}

export function ResultPanel({
  result,
  history,
  onDeleteHistory,
  onSelectHistory,
  selectedHistoryId,
}: Props) {
  const { token } = theme.useToken();
  const navChartRef = useRef<any>(null);
  const pnlChartRef = useRef<any>(null);
  const benchmarkChartRef = useRef<any>(null);

  useEffect(() => {
    const charts = [];
    if (navChartRef.current?.getEchartsInstance()) {
      charts.push(navChartRef.current.getEchartsInstance());
    }
    if (pnlChartRef.current?.getEchartsInstance()) {
      charts.push(pnlChartRef.current.getEchartsInstance());
    }
    if (benchmarkChartRef.current?.getEchartsInstance()) {
      charts.push(benchmarkChartRef.current.getEchartsInstance());
    }
    if (charts.length > 1) {
      echarts.connect(charts);
    }
    return () => {
      echarts.disconnect(charts);
    };
  }, [result]);

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
            <HistoryTable
              history={history}
              onDelete={onDeleteHistory}
              onSelect={onSelectHistory}
              selectedId={selectedHistoryId}
            />
          </>
        )}
      </div>
    );
  }

  const { metrics, series } = result;

  // 日期 → 时间戳（ECharts time axis）
  const toTs = (s: string) => {
    try {
      return new Date(s).getTime();
    } catch (e) {
      console.error('Invalid date:', s, e);
      return 0;
    }
  };
  const dates = (series.dates as string[]).map(toTs);

  // 检查数据有效性
  if (!dates || dates.length === 0) {
    console.error('No dates data');
  }

  const initial = series.portfolio_values[0] || 1;
  const navValues = (series.portfolio_values as number[]).map((v, i) => [
    dates[i],
    +(v / initial).toFixed(6),
  ]);

  // 基准净值（按策略日期对齐）
  const bm: number[] = series.benchmark_nav ?? [];
  const bmValues = [];
  if (bm.length > 0 && dates.length > 0) {
    // 确保基准数据与策略数据长度一致
    for (let i = 0; i < dates.length; i++) {
      if (i < bm.length) {
        bmValues.push([dates[i], +bm[i].toFixed(6)]);
      } else {
        // 如果基准数据不足，使用最后一个值
        bmValues.push([dates[i], +bm[bm.length - 1].toFixed(6)]);
      }
    }
  }

  // 买卖点：有成交的日期取对应净值
  const buyPoints = (series.daily_buy_amount as number[])
    .map((v, i) => (v > 0 ? [dates[i], navValues[i][1]] : null))
    .filter(Boolean);
  const sellPoints = (series.daily_sell_amount as number[])
    .map((v, i) => (v > 0 ? [dates[i], navValues[i][1]] : null))
    .filter(Boolean);

  // 调试信息
  console.log('ResultPanel data:', {
    datesLength: dates.length,
    navValuesLength: navValues.length,
    bmValuesLength: bmValues.length,
    buyPointsLength: buyPoints.length,
    sellPointsLength: sellPoints.length,
    sampleDates: dates.slice(0, 3),
    sampleNav: navValues.slice(0, 3),
    sampleBm: bmValues.slice(0, 3),
    seriesKeys: Object.keys(series),
    hasBenchmarkNav: 'benchmark_nav' in series,
    benchmarkNavLength: series.benchmark_nav?.length || 0,
  });

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
    { 
      type: "inside", 
      xAxisIndex: 0, 
      filterMode: "none",
      group: "zoomGroup",
    },
    {
      type: "slider",
      xAxisIndex: 0,
      height: 18,
      bottom: 4,
      textStyle: { fontSize: 9 },
      handleSize: "80%",
      filterMode: "none",
      group: "zoomGroup",
    },
  ];
  const dataZoomPnl = [
    { 
      type: "inside", 
      xAxisIndex: 0, 
      filterMode: "none",
      group: "zoomGroup",
    },
    {
      type: "slider",
      xAxisIndex: 0,
      height: 18,
      bottom: 4,
      textStyle: { fontSize: 9 },
      handleSize: "80%",
      filterMode: "none",
      show: false,
      group: "zoomGroup",
    },
  ];

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

  // 独立基准图
  const benchmarkOption = {
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
    grid: { top: 16, bottom: 36, left: 52, right: 16 },
    xAxis: axisStyle,
    yAxis: {
      type: "value" as const,
      scale: true,
      axisLabel: { fontSize: 10, color: token.colorTextSecondary },
      splitLine: { lineStyle: { color: token.colorBorderSecondary } },
    },
    dataZoom: dataZoomPnl,
    series: [
      {
        name: metrics.benchmark_name || "基准",
        type: "line",
        data: bmValues,
        lineStyle: { width: 2, color: "#52c41a" },
        symbol: "none",
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(82, 196, 26, 0.3)" },
              { offset: 1, color: "rgba(82, 196, 26, 0.05)" },
            ],
          },
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
    {
      title: "Alpha",
      value: fmt(metrics.alpha ?? 0, true),
      color: (metrics.alpha ?? 0) >= 0 ? "#cf1322" : "#3f8600",
    },
    { title: "Beta", value: fmt(metrics.beta ?? 0) },
    { title: "胜率", value: fmt(metrics.win_rate, true) },
    { title: "超额收益", value: fmt(metrics.excess_return, true) },
    { title: "盈利天数", value: metrics.win_count ?? 0 },
    { title: "亏损天数", value: metrics.lose_count ?? 0 },
    { title: "盈亏比", value: fmt(metrics.profit_loss_ratio ?? 0) },
    { title: "信息比率", value: fmt(metrics.information_ratio ?? 0) },
  ];

  return (
    <div style={{ height: "100%", overflowY: "auto", padding: 12 }}>
      <Row gutter={[6, 6]}>
        {statsCards.map(({ title, value, color }) => (
          <Col span={6} key={title}>
            <Card size="small" styles={{ body: { padding: "4px 8px" } }}>
              <Statistic
                title={title}
                value={value}
                valueStyle={{ fontSize: 13, color }}
                titleStyle={{ fontSize: 11 }}
              />
            </Card>
          </Col>
        ))}
      </Row>
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>
        净值 vs {metrics.benchmark_name || "基准"}
      </Divider>
      <ReactECharts ref={navChartRef} option={navOption} style={{ height: 220 }} />
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>
        {metrics.benchmark_name || "基准"} 独立走势
      </Divider>
      <ReactECharts ref={benchmarkChartRef} option={benchmarkOption} style={{ height: 150 }} />
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>每日盈亏</Divider>
      <ReactECharts ref={pnlChartRef} option={pnlOption} style={{ height: 150 }} />

      {history.length > 0 && (
        <>
          <Divider style={{ margin: "10px 0", fontSize: 12 }}>回测历史</Divider>
          <HistoryTable
            history={history}
            onDelete={onDeleteHistory}
            onSelect={onSelectHistory}
            selectedId={selectedHistoryId}
          />
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

const ResizableTitle = (props: any) => {
  const { onResize, width, ...restProps } = props;
  if (!width) return <th {...restProps} />;
  return (
    <Resizable
      width={width}
      height={0}
      axis="x"
      handle={
        <span
          onClick={(e) => e.stopPropagation()}
          style={{
            position: "absolute",
            right: -5,
            top: 0,
            zIndex: 1,
            width: 10,
            height: "100%",
            cursor: "col-resize",
          }}
        />
      }
      onResize={onResize}
      draggableOpts={{ enableUserSelectHack: false }}
    >
      <th {...restProps} style={{ ...restProps.style, position: "relative" }} />
    </Resizable>
  );
};

function HistoryTable({
  history,
  onDelete,
  onSelect,
  selectedId,
}: {
  history: HistoryEntry[];
  onDelete: (id: string) => void;
  onSelect?: (entry: HistoryEntry) => void;
  selectedId?: string | null;
}) {
  const { token } = theme.useToken();

  const [colWidths, setColWidths] = useState<Record<string, number>>({
    runAt: 70,
    strategy: 90,
    range: 100,
    ret: 65,
    ann: 60,
    sharpe: 52,
    dd: 60,
    dur: 50,
    del: 28,
  });

  const handleResize = useCallback(
    (key: string) =>
      (_: React.SyntheticEvent, { size }: { size: { width: number } }) => {
        setColWidths((prev) => ({ ...prev, [key]: size.width }));
      },
    [],
  );

  const columns = [
    {
      title: "时间",
      dataIndex: "runAt",
      key: "runAt",
      width: colWidths.runAt,
      sorter: (a: HistoryEntry, b: HistoryEntry) => a.runAt - b.runAt,
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("runAt"),
      }),
      render: (v: number) =>
        new Date(v).toLocaleString("zh-CN", {
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        }),
    },
    {
      title: "策略",
      dataIndex: "strategy",
      key: "strategy",
      width: colWidths.strategy,
      ellipsis: true,
      sorter: (a: HistoryEntry, b: HistoryEntry) =>
        a.strategy.localeCompare(b.strategy),
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("strategy"),
      }),
    },
    {
      title: "区间",
      key: "range",
      width: colWidths.range,
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("range"),
      }),
      render: (_: any, r: HistoryEntry) => `${r.startDate} ~ ${r.endDate}`,
    },
    {
      title: "总收益",
      key: "ret",
      width: colWidths.ret,
      sorter: (a: HistoryEntry, b: HistoryEntry) =>
        (a.metrics.total_return ?? 0) - (b.metrics.total_return ?? 0),
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("ret"),
      }),
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
      width: colWidths.ann,
      sorter: (a: HistoryEntry, b: HistoryEntry) =>
        (a.metrics.annual_return ?? 0) - (b.metrics.annual_return ?? 0),
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("ann"),
      }),
      render: (_: any, r: HistoryEntry) => pct(r.metrics.annual_return ?? 0),
    },
    {
      title: "夏普",
      key: "sharpe",
      width: colWidths.sharpe,
      sorter: (a: HistoryEntry, b: HistoryEntry) =>
        (a.metrics.sharpe_ratio ?? 0) - (b.metrics.sharpe_ratio ?? 0),
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("sharpe"),
      }),
      render: (_: any, r: HistoryEntry) => num(r.metrics.sharpe_ratio ?? 0),
    },
    {
      title: "回撤",
      key: "dd",
      width: colWidths.dd,
      sorter: (a: HistoryEntry, b: HistoryEntry) =>
        (a.metrics.max_drawdown ?? 0) - (b.metrics.max_drawdown ?? 0),
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("dd"),
      }),
      render: (_: any, r: HistoryEntry) => (
        <span style={{ color: token.colorError }}>
          {pct(r.metrics.max_drawdown ?? 0)}
        </span>
      ),
    },
    {
      title: "耗时",
      key: "dur",
      width: colWidths.dur,
      sorter: (a: HistoryEntry, b: HistoryEntry) => a.duration - b.duration,
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("dur"),
      }),
      render: (_: any, r: HistoryEntry) => `${r.duration.toFixed(1)}s`,
    },
    {
      title: "",
      key: "del",
      width: colWidths.del,
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("del"),
      }),
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
      style={{ fontSize: 10, border: `1px solid ${token.colorBorderSecondary}` }}
      components={{ header: { cell: ResizableTitle } }}
      rowClassName="compact-row"
      onRow={(record) => ({
        onClick: () => onSelect?.(record),
        style: {
          cursor: onSelect ? "pointer" : undefined,
          background:
            record.id === selectedId ? token.colorPrimaryBg : undefined,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          padding: "0 6px",
          height: 28,
        },
      })}
    />
  );
}
