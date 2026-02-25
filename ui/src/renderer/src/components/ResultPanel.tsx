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
  Tooltip,
} from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { theme, ConfigProvider } from "antd";
import { Resizable } from "react-resizable";
import { useTranslation } from "react-i18next";
import "react-resizable/css/styles.css";
import type { HistoryEntry } from "../services/api";
const CHART_FONT = { zoom: 9, axis: 10, tooltip: 11 } as const;

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
  const { t, i18n } = useTranslation();
  const navChartRef = useRef<any>(null);
  const pnlChartRef = useRef<any>(null);
  const tradeAmtChartRef = useRef<any>(null);
  const posValChartRef = useRef<any>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const ZOOM_GROUP = "result-charts-zoom";

  const handleChartReady = useCallback((inst: echarts.ECharts) => {
    inst.group = ZOOM_GROUP;
    echarts.connect(ZOOM_GROUP);
  }, []);

  useEffect(() => {
    if (!result) return;
    const insts = [navChartRef, pnlChartRef, tradeAmtChartRef, posValChartRef]
      .map((r) => r.current?.getEchartsInstance())
      .filter((inst): inst is echarts.ECharts => inst != null);
    if (insts.length < 2) return;
    insts.forEach((inst) => {
      inst.group = ZOOM_GROUP;
    });
    echarts.connect(ZOOM_GROUP);
    return () => {
      echarts.disconnect(ZOOM_GROUP);
    };
  }, [result]);

  useEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const handler = (e: WheelEvent) => {
      if (e.ctrlKey) return;
      const target = e.target as HTMLElement;
      if (target.tagName === "CANVAS") {
        e.stopPropagation();
        el.scrollTop += e.deltaY;
      }
    };
    el.addEventListener("wheel", handler, { capture: true, passive: false });
    return () => el.removeEventListener("wheel", handler, { capture: true });
  }, []);

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
              fontSize: 12,
            }}
          >
            {t("result.empty")}
          </div>
        ) : (
          <>
            <Divider style={{ margin: "10px 0", fontSize: 12 }}>
              {t("result.history")}
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
      console.error("Invalid date:", s, e);
      return 0;
    }
  };
  const dates = (series.dates as string[]).map(toTs);

  // 检查数据有效性
  if (!dates || dates.length === 0) {
    console.error("No dates data");
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
    for (let i = 0; i < dates.length; i++) {
      bmValues.push([
        dates[i],
        +(i < bm.length ? bm[i] : bm[bm.length - 1]).toFixed(6),
      ]);
    }
  }

  // 买卖点：有成交的日期取对应净值
  const buyPoints = (series.daily_buy_amount as number[])
    .map((v, i) => (v > 0 ? [dates[i], navValues[i][1]] : null))
    .filter(Boolean);
  const sellPoints = (series.daily_sell_amount as number[])
    .map((v, i) => (v > 0 ? [dates[i], navValues[i][1]] : null))
    .filter(Boolean);

  // 调试信息已移除

  const axisStyle = {
    type: "time" as const,
    axisLabel: {
      fontSize: CHART_FONT.axis,
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
      zoomOnMouseWheel: "ctrl",
    },
    {
      type: "slider",
      xAxisIndex: 0,
      height: 18,
      bottom: 4,
      textStyle: { fontSize: CHART_FONT.zoom },
      handleSize: "80%",
      filterMode: "none",
      group: "zoomGroup",
    },
  ];
  const dataZoomNoSlider = [
    {
      type: "inside",
      xAxisIndex: 0,
      filterMode: "none",
      group: "zoomGroup",
      zoomOnMouseWheel: "ctrl",
    },
    {
      type: "slider",
      xAxisIndex: 0,
      height: 18,
      bottom: 4,
      textStyle: { fontSize: CHART_FONT.zoom },
      handleSize: "80%",
      filterMode: "none",
      show: false,
      group: "zoomGroup",
    },
  ];

  const positionsSnapshot: Array<
    Array<{ c: string; nm: string; n: number; v: number; b: number }>
  > = series.daily_positions_snapshot ?? [];

  const navOption = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      confine: true,
      textStyle: { fontSize: CHART_FONT.tooltip },
      formatter: (params: any[]) => {
        const valueParts = params
          .filter((p: any) => p.seriesType !== "scatter")
          .map(
            (p: any) => `${p.marker}${p.seriesName}: ${p.value[1].toFixed(4)}`,
          );
        const idx: number = params[0]?.dataIndex ?? -1;
        const positions = idx >= 0 ? (positionsSnapshot[idx] ?? []) : [];
        let html = valueParts.join("<br/>");
        if (positions.length > 0) {
          const rows = positions
            .map(({ c, nm, n, v, b }) => {
              const pnlPct = b > 0 ? ((v / n - b) / b) * 100 : 0;
              const color = pnlPct >= 0 ? "#ef5350" : "#26a69a";
              return (
                `<div style="display:flex;justify-content:space-between;gap:8px">` +
                `<span>${nm && nm !== c ? nm : c}<span style="color:#888;font-size:${CHART_FONT.axis}px"> ${nm && nm !== c ? c : ""}</span></span>` +
                `<span>${n}股</span>` +
                `<span style="color:${color}">${pnlPct >= 0 ? "+" : ""}${pnlPct.toFixed(1)}%</span>` +
                `</div>`
              );
            })
            .join("");
          html += `<div style="margin-top:4px;border-top:1px solid rgba(128,128,128,0.3);padding-top:4px;font-size:${CHART_FONT.tooltip}px">${rows}</div>`;
        }
        return html;
      },
    },
    legend: {
      data: [
        t("result.series.strategyNav"),
        metrics.benchmark_name || t("result.series.benchmark"),
      ],
      bottom: 0,
      textStyle: { color: token.colorText },
    },
    grid: { top: 16, bottom: 56, left: 52, right: 16 },
    xAxis: axisStyle,
    yAxis: {
      type: "value" as const,
      scale: true,
      axisLabel: { fontSize: CHART_FONT.axis, color: token.colorTextSecondary },
      splitLine: { lineStyle: { color: token.colorBorderSecondary } },
    },
    dataZoom: dataZoomNav,
    series: [
      {
        name: t("result.series.strategyNav"),
        type: "line",
        data: navValues,
        lineStyle: { width: 2, color: "#1677ff" },
        symbol: "none",
        z: 2,
      },
      ...(bmValues.length > 0
        ? [
            {
              name: metrics.benchmark_name || t("result.series.benchmark"),
              type: "line" as const,
              data: bmValues,
              lineStyle: { width: 1.5, color: "#aaa", type: "dashed" as const },
              symbol: "none",
              z: 1,
            },
          ]
        : []),
      {
        name: t("result.series.buy"),
        type: "scatter",
        data: buyPoints,
        symbol: "triangle",
        symbolSize: 8,
        itemStyle: { color: "#ef5350" },
        z: 3,
        tooltip: { show: false },
      },
      {
        name: t("result.series.sell"),
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

  const isChinese = i18n.language === "zh";
  const fmtMoney = (v: number) =>
    isChinese && v >= 1e4
      ? `${(v / 1e4).toFixed(2)}万`
      : Math.round(v).toLocaleString();

  const moneyTooltip = {
    trigger: "axis" as const,
    confine: true,
    textStyle: { fontSize: CHART_FONT.tooltip },
    formatter: (params: any[]) =>
      params
        .map((p: any) => `${p.marker}${p.seriesName}: ${fmtMoney(p.value[1])}`)
        .join("<br/>"),
  };

  const moneyYAxis = {
    type: "value" as const,
    axisLabel: {
      fontSize: CHART_FONT.axis,
      color: token.colorTextSecondary,
      formatter: (v: number) =>
        isChinese && v >= 1e4
          ? `${(v / 1e4).toFixed(0)}万`
          : Math.round(v).toLocaleString(),
    },
    splitLine: { lineStyle: { color: token.colorBorderSecondary } },
  };

  const pnlOption = {
    backgroundColor: "transparent",
    tooltip: moneyTooltip,
    grid: { top: 8, bottom: 36, left: 60, right: 16 },
    xAxis: { ...axisStyle },
    yAxis: moneyYAxis,
    dataZoom: dataZoomNoSlider,
    series: [
      {
        name: t("result.series.pnl"),
        type: "bar",
        data: (series.daily_pnl as number[]).map((v, i) => [dates[i], v]),
        itemStyle: {
          color: (p: any) => (p.value[1] >= 0 ? "#ef5350" : "#26a69a"),
        },
      },
    ],
  };

  const tradeAmtOption = {
    backgroundColor: "transparent",
    tooltip: moneyTooltip,
    legend: { show: false },
    grid: { top: 8, bottom: 8, left: 60, right: 16 },
    xAxis: { ...axisStyle },
    yAxis: moneyYAxis,
    dataZoom: dataZoomNoSlider,
    series: [
      {
        name: t("result.series.buyAmt"),
        type: "bar",
        data: (series.daily_buy_amount as number[]).map((v, i) => [
          dates[i],
          v,
        ]),
        itemStyle: { color: "#ef5350" },
      },
      {
        name: t("result.series.sellAmt"),
        type: "bar",
        data: (series.daily_sell_amount as number[]).map((v, i) => [
          dates[i],
          v,
        ]),
        itemStyle: { color: "#26a69a" },
      },
    ],
  };

  const posValOption = {
    backgroundColor: "transparent",
    tooltip: moneyTooltip,
    grid: { top: 8, bottom: 36, left: 60, right: 16 },
    xAxis: { ...axisStyle },
    yAxis: moneyYAxis,
    dataZoom: dataZoomNoSlider,
    series: [
      {
        name: t("result.series.posVal"),
        type: "line",
        data: (series.daily_positions_value as number[]).map((v, i) => [
          dates[i],
          v,
        ]),
        lineStyle: { width: 2, color: "#9467bd" },
        symbol: "none",
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(148,103,189,0.3)" },
              { offset: 1, color: "rgba(148,103,189,0.05)" },
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
      title: t("result.metric.totalReturn"),
      value: fmt(metrics.total_return, true),
      color: metrics.total_return >= 0 ? "#cf1322" : "#3f8600",
    },
    {
      title: t("result.metric.annualReturn"),
      value: fmt(metrics.annual_return, true),
    },
    {
      title: t("result.metric.maxDrawdown"),
      value: fmt(metrics.max_drawdown, true),
      color: "#cf1322",
    },
    { title: t("result.metric.sharpe"), value: fmt(metrics.sharpe_ratio) },
    {
      title: t("result.metric.alpha"),
      value: fmt(metrics.alpha ?? 0, true),
      color: (metrics.alpha ?? 0) >= 0 ? "#cf1322" : "#3f8600",
    },
    { title: t("result.metric.beta"), value: fmt(metrics.beta ?? 0) },
    { title: t("result.metric.winRate"), value: fmt(metrics.win_rate, true) },
    {
      title: t("result.metric.excess"),
      value: fmt(metrics.excess_return, true),
    },
    { title: t("result.metric.winDays"), value: metrics.win_count ?? 0 },
    { title: t("result.metric.loseDays"), value: metrics.lose_count ?? 0 },
    {
      title: t("result.metric.plRatio"),
      value: fmt(metrics.profit_loss_ratio ?? 0),
    },
    {
      title: t("result.metric.infoRatio"),
      value: fmt(metrics.information_ratio ?? 0),
    },
  ];

  return (
    <div
      ref={scrollContainerRef}
      style={{ height: "100%", overflowY: "auto", padding: 12 }}
    >
      <Row gutter={[6, 6]}>
        {statsCards.map(({ title, value, color }) => (
          <Col span={6} key={title}>
            <Card size="small" styles={{ body: { padding: "4px 8px" } }}>
              <Statistic
                title={title}
                value={value}
                valueStyle={{ fontSize: 12, color }}
                styles={{ title: { fontSize: 12, fontWeight: 600 } }}
              />
            </Card>
          </Col>
        ))}
      </Row>
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>
        {t("result.chart.nav", {
          benchmark: metrics.benchmark_name || t("result.series.benchmark"),
        })}
      </Divider>
      <ReactECharts
        ref={navChartRef}
        option={navOption}
        style={{ height: 220 }}
        onChartReady={handleChartReady}
      />
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>
        {t("result.chart.pnl")}
      </Divider>
      <ReactECharts
        ref={pnlChartRef}
        option={pnlOption}
        style={{ height: 150 }}
        onChartReady={handleChartReady}
      />
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>
        {t("result.chart.tradeAmt")}
      </Divider>
      <ReactECharts
        ref={tradeAmtChartRef}
        option={tradeAmtOption}
        style={{ height: 150 }}
        onChartReady={handleChartReady}
      />
      <Divider style={{ margin: "10px 0", fontSize: 12 }}>
        {t("result.chart.posVal")}
      </Divider>
      <ReactECharts
        ref={posValChartRef}
        option={posValOption}
        style={{ height: 150 }}
        onChartReady={handleChartReady}
      />

      {history.length > 0 && (
        <>
          <Divider style={{ margin: "10px 0", fontSize: 12 }}>
            {t("result.history")}
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

function pct(v: number) {
  return `${(v * 100).toFixed(2)}%`;
}
function num(v: number) {
  return v.toFixed(3);
}

const ResizableTitle = (props: any) => {
  const { onResize, width, ...restProps } = props;
  if (!width)
    return <th {...restProps} style={{ ...restProps.style, fontSize: 12 }} />;
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
      <th
        {...restProps}
        style={{ ...restProps.style, position: "relative", fontSize: 12 }}
      />
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
  const { t } = useTranslation();

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
      title: t("result.table.time"),
      dataIndex: "runAt",
      key: "runAt",
      width: colWidths.runAt,
      sorter: (a: HistoryEntry, b: HistoryEntry) => a.runAt - b.runAt,
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("runAt"),
      }),
      render: (v: number) =>
        new Date(v).toLocaleString(i18n.language, {
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        }),
    },
    {
      title: t("result.table.strategy"),
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
      title: t("result.table.range"),
      key: "range",
      width: colWidths.range,
      onHeaderCell: (col: any) => ({
        width: col.width,
        onResize: handleResize("range"),
      }),
      render: (_: any, r: HistoryEntry) => `${r.startDate} ~ ${r.endDate}`,
    },
    {
      title: t("result.table.return"),
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
      title: t("result.table.annual"),
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
      title: t("result.table.sharpe"),
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
      title: t("result.table.drawdown"),
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
      title: t("result.table.duration"),
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
        <Popconfirm
          title={t("result.confirmDelete")}
          onConfirm={() => onDelete(r.id)}
        >
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <ConfigProvider theme={{ token: { fontSize: 11 } }}>
      <Table
        size="small"
        dataSource={history}
        columns={columns}
        rowKey="id"
        pagination={false}
        scroll={{ x: true }}
        style={{
          border: `1px solid ${token.colorBorderSecondary}`,
        }}
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
    </ConfigProvider>
  );
}
