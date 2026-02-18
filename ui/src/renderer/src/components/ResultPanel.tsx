import ReactECharts from 'echarts-for-react'
import { Card, Statistic, Row, Col, Divider } from 'antd'

interface Props {
  result: any | null
}

export function ResultPanel({ result }: Props) {
  if (!result) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#999', fontSize: 13 }}>
        运行回测后结果显示在此处
      </div>
    )
  }

  const { metrics, series } = result

  const navOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['策略净值'], bottom: 0 },
    grid: { top: 20, bottom: 40, left: 50, right: 20 },
    xAxis: { type: 'category', data: series.dates, axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value', scale: true },
    series: [{
      name: '策略净值',
      type: 'line',
      data: series.portfolio_values.map((v: number) =>
        +(v / (series.portfolio_values[0] || 1)).toFixed(4)),
      lineStyle: { width: 2, color: '#1677ff' },
      symbol: 'none',
    }],
  }

  const pnlOption = {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, bottom: 40, left: 60, right: 20 },
    xAxis: { type: 'category', data: series.dates, axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{
      name: '每日盈亏',
      type: 'bar',
      data: series.daily_pnl,
      itemStyle: {
        color: (params: any) => params.value >= 0 ? '#ef5350' : '#26a69a',
      },
    }],
  }

  const fmt = (v: number, pct = false) =>
    pct ? `${(v * 100).toFixed(2)}%` : v.toFixed(3)

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 12 }}>
      <Row gutter={[8, 8]}>
        {[
          { title: '总收益', value: fmt(metrics.total_return, true), color: metrics.total_return >= 0 ? '#cf1322' : '#3f8600' },
          { title: '年化收益', value: fmt(metrics.annual_return, true) },
          { title: '最大回撤', value: fmt(metrics.max_drawdown, true), color: '#cf1322' },
          { title: '夏普比率', value: fmt(metrics.sharpe_ratio) },
          { title: '胜率', value: fmt(metrics.win_rate, true) },
          { title: '超额收益', value: fmt(metrics.excess_return, true) },
        ].map(({ title, value, color }) => (
          <Col span={8} key={title}>
            <Card size="small" bodyStyle={{ padding: '8px 12px' }}>
              <Statistic title={title} value={value} valueStyle={{ fontSize: 16, color }} />
            </Card>
          </Col>
        ))}
      </Row>
      <Divider style={{ margin: '10px 0', fontSize: 12 }}>净值曲线</Divider>
      <ReactECharts option={navOption} style={{ height: 200 }} />
      <Divider style={{ margin: '10px 0', fontSize: 12 }}>每日盈亏</Divider>
      <ReactECharts option={pnlOption} style={{ height: 160 }} />
    </div>
  )
}
