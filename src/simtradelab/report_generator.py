# -*- coding: utf-8 -*-
"""
回测报告生成器模块

提供多种格式的回测报告生成功能，包括策略内容绑定输出
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

from .logger import log
from .performance import calculate_performance_metrics


class ReportGenerator:
    """回测报告生成器"""
    
    def __init__(self, engine, output_dir: str = "reports"):
        """
        初始化报告生成器

        Args:
            engine: 回测引擎实例
            output_dir: 输出目录
        """
        self.engine = engine
        self.strategy_name = os.path.basename(engine.strategy_file).replace('.py', '')
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 为每个策略创建单独的目录
        self.output_dir = os.path.join(output_dir, self.strategy_name)

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_filename(self, format_type: str = "txt", include_params: bool = True) -> str:
        """
        生成报告文件名

        Args:
            format_type: 文件格式类型
            include_params: 是否包含参数信息

        Returns:
            str: 文件名
        """
        parts = [self.strategy_name]

        if self.engine.start_date and self.engine.end_date:
            start_date = self.engine.start_date.strftime("%Y%m%d")
            end_date = self.engine.end_date.strftime("%Y%m%d")
            parts.append(f"{start_date}_{end_date}")

        if include_params:
            # 添加基本参数信息
            parts.append(f"cash{int(self.engine.initial_cash/10000)}w")  # 资金（万元）
            parts.append(f"freq{self.engine.frequency}")  # 频率

            # 如果有股票列表，添加股票数量
            if self.engine.securities:
                parts.append(f"stocks{len(self.engine.securities)}")

        parts.append(self.timestamp)

        filename = "_".join(parts) + f".{format_type}"
        return filename
    
    def generate_comprehensive_report(self, benchmark_returns=None, 
                                    include_strategy_code: bool = True,
                                    include_trade_details: bool = True) -> str:
        """
        生成综合报告（文本格式）
        
        Args:
            benchmark_returns: 基准收益率序列
            include_strategy_code: 是否包含策略代码
            include_trade_details: 是否包含交易明细
            
        Returns:
            str: 报告文件路径
        """
        filename = self.generate_filename("txt")
        filepath = os.path.join(self.output_dir, filename)
        
        # 获取性能指标
        metrics = calculate_performance_metrics(self.engine, benchmark_returns)
        
        if not metrics:
            log.warning("无法生成综合报告")
            return None
        
        # 生成报告内容
        content_sections = []
        
        # 1. 报告头部
        content_sections.append(self._generate_header())
        
        # 2. 基本信息
        content_sections.append(self._generate_basic_info())
        
        # 3. 性能指标
        content_sections.append(self._generate_performance_section(metrics, benchmark_returns))
        
        # 4. 策略代码（可选）
        if include_strategy_code:
            content_sections.append(self._generate_strategy_code_section())
        
        # 5. 交易明细（可选）
        if include_trade_details:
            content_sections.append(self._generate_trade_details_section())
        
        # 6. 持仓信息
        content_sections.append(self._generate_position_section())
        
        # 7. 报告尾部
        content_sections.append(self._generate_footer())
        
        # 写入文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(content_sections))
            
            log.info(f"综合报告已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            log.warning(f"保存综合报告失败: {e}")
            return None
    
    def generate_json_report(self, benchmark_returns=None) -> str:
        """
        生成JSON格式报告
        
        Args:
            benchmark_returns: 基准收益率序列
            
        Returns:
            str: 报告文件路径
        """
        filename = self.generate_filename("json")
        filepath = os.path.join(self.output_dir, filename)
        
        # 获取性能指标
        metrics = calculate_performance_metrics(self.engine, benchmark_returns)
        
        if not metrics:
            log.warning("无法生成JSON报告")
            return None
        
        # 构建报告数据
        report_data = {
            "report_info": {
                "strategy_name": self.strategy_name,
                "strategy_file": self.engine.strategy_file,
                "generated_at": datetime.now().isoformat(),
                "simtradelab_version": "1.0.0"
            },
            "backtest_config": {
                "start_date": self.engine.start_date.isoformat() if self.engine.start_date else None,
                "end_date": self.engine.end_date.isoformat() if self.engine.end_date else None,
                "initial_cash": self.engine.initial_cash,
                "frequency": self.engine.frequency,
                "securities": self.engine.securities,
                "data_source": type(self.engine.data_source).__name__ if hasattr(self.engine, 'data_source') else "CSV"
            },
            "performance_metrics": metrics,
            "portfolio_history": self._get_portfolio_history_data(),
            "final_positions": self._get_final_positions_data(),
            "trade_summary": self._get_trade_summary_data()
        }
        
        # 添加策略代码
        try:
            with open(self.engine.strategy_file, 'r', encoding='utf-8') as f:
                report_data["strategy_code"] = f.read()
        except Exception as e:
            log.warning(f"无法读取策略代码: {e}")
            report_data["strategy_code"] = None
        
        # 写入文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            log.info(f"JSON报告已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            log.warning(f"保存JSON报告失败: {e}")
            return None
    
    def generate_yaml_report(self, benchmark_returns=None) -> str:
        """
        生成YAML格式报告
        
        Args:
            benchmark_returns: 基准收益率序列
            
        Returns:
            str: 报告文件路径
        """
        filename = self.generate_filename("yaml")
        filepath = os.path.join(self.output_dir, filename)
        
        # 获取性能指标
        metrics = calculate_performance_metrics(self.engine, benchmark_returns)
        
        if not metrics:
            log.warning("无法生成YAML报告")
            return None
        
        # 构建报告数据（与JSON类似但格式化为YAML友好）
        report_data = {
            "report_info": {
                "strategy_name": self.strategy_name,
                "strategy_file": self.engine.strategy_file,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "simtradelab_version": "1.0.0"
            },
            "backtest_config": {
                "start_date": self.engine.start_date.strftime("%Y-%m-%d") if self.engine.start_date else None,
                "end_date": self.engine.end_date.strftime("%Y-%m-%d") if self.engine.end_date else None,
                "initial_cash": float(self.engine.initial_cash),
                "frequency": self.engine.frequency,
                "securities": self.engine.securities or [],
                "data_source": type(self.engine.data_source).__name__ if hasattr(self.engine, 'data_source') else "CSV"
            },
            "performance_metrics": {k: float(v) if isinstance(v, (int, float)) else v for k, v in metrics.items()},
            "portfolio_summary": self._get_portfolio_summary_data(),
            "trade_summary": self._get_trade_summary_data()
        }
        
        # 写入文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(report_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2, sort_keys=False)
            
            log.info(f"YAML报告已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            log.warning(f"保存YAML报告失败: {e}")
            return None
    
    def generate_csv_report(self) -> str:
        """
        生成CSV格式的投资组合历史数据
        
        Returns:
            str: 报告文件路径
        """
        filename = self.generate_filename("csv")
        filepath = os.path.join(self.output_dir, filename)
        
        if not hasattr(self.engine, 'portfolio_history') or not self.engine.portfolio_history:
            log.warning("无投资组合历史数据，无法生成CSV报告")
            return None
        
        try:
            # 转换为DataFrame
            df = pd.DataFrame(self.engine.portfolio_history)
            
            # 添加收益率列
            df['daily_return'] = df['total_value'].pct_change()
            df['cumulative_return'] = (df['total_value'] / df['total_value'].iloc[0]) - 1
            
            # 保存到CSV
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            log.info(f"CSV报告已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            log.warning(f"保存CSV报告失败: {e}")
            return None

    def generate_summary_report(self, benchmark_returns=None) -> str:
        """
        生成简洁的摘要报告

        Args:
            benchmark_returns: 基准收益率序列

        Returns:
            str: 报告文件路径
        """
        filename = self.generate_filename("summary.txt")
        filepath = os.path.join(self.output_dir, filename)

        # 获取性能指标
        metrics = calculate_performance_metrics(self.engine, benchmark_returns)

        if not metrics:
            log.warning("无法生成摘要报告")
            return None

        # 生成摘要内容
        summary_content = self._generate_summary_content(metrics)

        # 写入文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(summary_content)

            log.info(f"摘要报告已保存到: {filepath}")
            return filepath

        except Exception as e:
            log.warning(f"保存摘要报告失败: {e}")
            return None

    def _generate_header(self) -> str:
        """生成报告头部"""
        lines = [
            "=" * 100,
            "simtradelab 策略回测综合报告",
            "=" * 100
        ]
        return "\n".join(lines)

    def _generate_basic_info(self) -> str:
        """生成基本信息部分"""
        lines = ["📋 基本信息:"]
        lines.append(f"  策略名称:     {self.strategy_name}")
        lines.append(f"  策略文件:     {self.engine.strategy_file}")

        if self.engine.start_date and self.engine.end_date:
            lines.append(f"  回测期间:     {self.engine.start_date.strftime('%Y-%m-%d')} 至 {self.engine.end_date.strftime('%Y-%m-%d')}")

        lines.append(f"  交易频率:     {self.engine.frequency}")
        lines.append(f"  初始资金:     ¥{self.engine.initial_cash:,.2f}")
        lines.append(f"  报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 数据源信息
        if hasattr(self.engine, 'data_source') and self.engine.data_source:
            lines.append(f"  数据源:       {type(self.engine.data_source).__name__}")
        elif self.engine.data_path:
            lines.append(f"  数据源:       CSV文件 ({os.path.basename(self.engine.data_path)})")

        if self.engine.securities:
            lines.append(f"  股票列表:     {', '.join(self.engine.securities)}")
            lines.append(f"  股票数量:     {len(self.engine.securities)}只")

        return "\n".join(lines)

    def _generate_performance_section(self, metrics: Dict[str, Any], benchmark_returns=None) -> str:
        """生成性能指标部分"""
        lines = []

        # 收益指标
        lines.append("📈 收益指标:")
        lines.append(f"  总收益率:     {metrics['total_return']:.2%}")
        lines.append(f"  年化收益率:   {metrics['annualized_return']:.2%}")
        lines.append(f"  最终资金:     ¥{metrics['final_value']:,.2f}")
        lines.append(f"  净收益:       ¥{metrics['final_value'] - metrics['initial_value']:,.2f}")
        lines.append("")

        # 风险指标
        lines.append("📊 风险指标:")
        lines.append(f"  年化波动率:   {metrics['volatility']:.2%}")
        lines.append(f"  夏普比率:     {metrics['sharpe_ratio']:.3f}")
        lines.append(f"  最大回撤:     {metrics['max_drawdown']:.2%}")
        lines.append(f"  胜率:         {metrics['win_rate']:.2%}")
        lines.append("")

        # 交易统计
        lines.append("📋 交易统计:")
        lines.append(f"  交易天数:     {metrics['trading_days']}天")
        lines.append(f"  总交易次数:   {metrics['total_trades']}次")

        if metrics['trading_days'] > 0:
            avg_trades_per_day = metrics['total_trades'] / metrics['trading_days']
            lines.append(f"  日均交易次数: {avg_trades_per_day:.2f}次")

        # 基准对比（如果有）
        if benchmark_returns is not None and 'alpha' in metrics:
            lines.append("")
            lines.append("📊 基准对比:")
            lines.append(f"  基准总收益率: {metrics['benchmark_total_return']:.2%}")
            lines.append(f"  基准年化收益: {metrics['benchmark_annualized_return']:.2%}")
            lines.append(f"  基准波动率:   {metrics['benchmark_volatility']:.2%}")
            lines.append(f"  Alpha:        {metrics['alpha']:.3f}")
            lines.append(f"  Beta:         {metrics['beta']:.3f}")
            lines.append(f"  信息比率:     {metrics['information_ratio']:.3f}")
            lines.append(f"  跟踪误差:     {metrics['tracking_error']:.2%}")

        return "\n".join(lines)

    def _generate_strategy_code_section(self) -> str:
        """生成策略代码部分"""
        lines = ["📝 策略代码:"]
        lines.append("-" * 80)

        try:
            with open(self.engine.strategy_file, 'r', encoding='utf-8') as f:
                strategy_code = f.read()

            # 添加行号
            code_lines = strategy_code.split('\n')
            for i, line in enumerate(code_lines, 1):
                lines.append(f"{i:4d}: {line}")

        except Exception as e:
            lines.append(f"无法读取策略代码: {e}")

        lines.append("-" * 80)
        return "\n".join(lines)

    def _generate_trade_details_section(self) -> str:
        """生成交易明细部分"""
        lines = ["📊 交易明细:"]

        if hasattr(self.engine, 'context') and hasattr(self.engine.context, 'blotter'):
            trades = self.engine.context.blotter.get_all_trades()

            if trades:
                lines.append(f"  总交易记录: {len(trades)}笔")
                lines.append("")
                lines.append("  交易记录:")
                lines.append("  " + "-" * 70)
                lines.append("  时间                股票代码    方向    数量      价格      金额")
                lines.append("  " + "-" * 70)

                for trade in trades[-20:]:  # 只显示最近20笔交易
                    direction = "买入" if trade.amount > 0 else "卖出"
                    amount = abs(trade.amount)
                    value = amount * trade.price

                    # 使用trade_time属性而不是datetime
                    trade_time = getattr(trade, 'trade_time', None)
                    if trade_time:
                        time_str = trade_time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        time_str = "未知时间"

                    lines.append(f"  {time_str} "
                               f"{trade.security:10s} {direction:4s} "
                               f"{amount:8.0f} {trade.price:8.2f} {value:10.2f}")

                if len(trades) > 20:
                    lines.append(f"  ... (省略{len(trades)-20}笔交易记录)")

                lines.append("  " + "-" * 70)
            else:
                lines.append("  无交易记录")
        else:
            lines.append("  无法获取交易记录")

        return "\n".join(lines)

    def _generate_position_section(self) -> str:
        """生成持仓信息部分"""
        lines = ["💼 最终持仓:"]

        if hasattr(self.engine, 'context') and hasattr(self.engine.context, 'portfolio'):
            portfolio = self.engine.context.portfolio
            lines.append(f"  现金余额:     ¥{portfolio.cash:,.2f}")

            if hasattr(portfolio, 'positions') and portfolio.positions:
                lines.append("  股票持仓:")
                total_stock_value = 0

                for security, position in portfolio.positions.items():
                    if hasattr(position, 'amount') and position.amount > 0:
                        market_value = getattr(position, 'market_value', 0)
                        avg_cost = getattr(position, 'avg_cost', 0)
                        total_stock_value += market_value

                        lines.append(f"    {security:12s}: {position.amount:8.0f}股, "
                                   f"成本¥{avg_cost:8.2f}, 市值¥{market_value:10.2f}")

                lines.append(f"  股票总市值:   ¥{total_stock_value:,.2f}")
                lines.append(f"  总资产:       ¥{portfolio.total_value:,.2f}")
            else:
                lines.append("  无股票持仓")
        else:
            lines.append("  无法获取持仓信息")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """生成报告尾部"""
        lines = [
            "=" * 100,
            f"报告生成完成 - simtradelab v1.0.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 100
        ]
        return "\n".join(lines)

    def _get_portfolio_history_data(self) -> List[Dict]:
        """获取投资组合历史数据"""
        if hasattr(self.engine, 'portfolio_history') and self.engine.portfolio_history:
            return [
                {
                    "datetime": item["datetime"].isoformat() if hasattr(item["datetime"], "isoformat") else str(item["datetime"]),
                    "total_value": float(item["total_value"]),
                    "cash": float(item["cash"])
                }
                for item in self.engine.portfolio_history
            ]
        return []

    def _get_portfolio_summary_data(self) -> Dict:
        """获取投资组合摘要数据"""
        if hasattr(self.engine, 'portfolio_history') and self.engine.portfolio_history:
            history = self.engine.portfolio_history
            return {
                "start_value": float(history[0]["total_value"]),
                "end_value": float(history[-1]["total_value"]),
                "start_cash": float(history[0]["cash"]),
                "end_cash": float(history[-1]["cash"]),
                "trading_days": len(history)
            }
        return {}

    def _get_final_positions_data(self) -> Dict:
        """获取最终持仓数据"""
        positions = {}

        if hasattr(self.engine, 'context') and hasattr(self.engine.context, 'portfolio'):
            portfolio = self.engine.context.portfolio

            if hasattr(portfolio, 'positions') and portfolio.positions:
                for security, position in portfolio.positions.items():
                    if hasattr(position, 'amount') and position.amount > 0:
                        positions[security] = {
                            "amount": float(position.amount),
                            "avg_cost": float(getattr(position, 'avg_cost', 0)),
                            "market_value": float(getattr(position, 'market_value', 0))
                        }

        return positions

    def _get_trade_summary_data(self) -> Dict:
        """获取交易摘要数据"""
        summary = {
            "total_trades": 0,
            "buy_trades": 0,
            "sell_trades": 0,
            "total_volume": 0.0,
            "total_amount": 0.0
        }

        if hasattr(self.engine, 'context') and hasattr(self.engine.context, 'blotter'):
            trades = self.engine.context.blotter.get_all_trades()

            summary["total_trades"] = len(trades)

            for trade in trades:
                if trade.amount > 0:
                    summary["buy_trades"] += 1
                else:
                    summary["sell_trades"] += 1

                summary["total_volume"] += abs(trade.amount)
                summary["total_amount"] += abs(trade.amount) * trade.price

        return summary

    def _generate_summary_content(self, metrics: Dict[str, Any]) -> str:
        """生成摘要报告内容"""

        # 计算关键指标
        total_return = metrics['total_return']
        sharpe_ratio = metrics['sharpe_ratio']
        max_drawdown = metrics['max_drawdown']
        win_rate = metrics['win_rate']

        # 评级逻辑
        def get_performance_rating():
            score = 0
            if total_return > 0.1:  # 收益率 > 10%
                score += 2
            elif total_return > 0.05:  # 收益率 > 5%
                score += 1

            if sharpe_ratio > 2.0:  # 夏普比率 > 2
                score += 2
            elif sharpe_ratio > 1.0:  # 夏普比率 > 1
                score += 1

            if max_drawdown < 0.05:  # 最大回撤 < 5%
                score += 2
            elif max_drawdown < 0.1:  # 最大回撤 < 10%
                score += 1

            if win_rate > 0.6:  # 胜率 > 60%
                score += 1

            if score >= 6:
                return "🌟 优秀"
            elif score >= 4:
                return "👍 良好"
            elif score >= 2:
                return "⚠️ 一般"
            else:
                return "❌ 较差"

        performance_rating = get_performance_rating()

        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                    📊 策略回测摘要报告                        ║
╠══════════════════════════════════════════════════════════════╣
║ 策略名称: {self.strategy_name:<45} ║
║ 回测期间: {self.engine.start_date.strftime('%Y-%m-%d')} 至 {self.engine.end_date.strftime('%Y-%m-%d'):<35} ║
║ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<45} ║
╠══════════════════════════════════════════════════════════════╣
║                        🎯 核心指标                           ║
╠══════════════════════════════════════════════════════════════╣
║ 💰 总收益率:     {total_return:>8.2%}                           ║
║ 📈 年化收益率:   {metrics['annualized_return']:>8.2%}                           ║
║ ⚡ 夏普比率:     {sharpe_ratio:>8.3f}                           ║
║ 📉 最大回撤:     {max_drawdown:>8.2%}                           ║
║ 🎯 胜率:         {win_rate:>8.1%}                           ║
║ 🔄 交易次数:     {metrics['total_trades']:>8d}                           ║
╠══════════════════════════════════════════════════════════════╣
║                        💼 资金状况                           ║
╠══════════════════════════════════════════════════════════════╣
║ 初始资金: ¥{metrics['initial_value']:>12,.2f}                      ║
║ 最终资金: ¥{metrics['final_value']:>12,.2f}                      ║
║ 净收益:   ¥{metrics['final_value'] - metrics['initial_value']:>12,.2f}                      ║
╠══════════════════════════════════════════════════════════════╣
║                        🏆 策略评级                           ║
╠══════════════════════════════════════════════════════════════╣
║ 综合评级: {performance_rating:<45} ║
╚══════════════════════════════════════════════════════════════╝

📝 评级说明:
🌟 优秀: 收益率高、风险控制好、夏普比率优秀
👍 良好: 收益率较好、风险适中
⚠️ 一般: 收益率一般或风险较高
❌ 较差: 收益率低或风险过高

📊 由 simtradelab v1.0.0 生成
        """

        return summary.strip()


