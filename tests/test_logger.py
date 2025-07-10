# -*- coding: utf-8 -*-
"""
Logger模块测试

专注测试日志系统的核心业务价值：
1. 在交易系统中记录关键业务事件
2. 支持策略执行过程的可追溯性
3. 为问题诊断和性能分析提供支持
"""

import sys
from datetime import datetime
from io import StringIO

import pytest

from simtradelab.logger import Logger, log


class TestLogger:
    """测试Logger类的核心业务能力"""

    @pytest.fixture
    def logger(self):
        """创建清洁的Logger实例"""
        return Logger()

    def test_trading_strategy_execution_logging(self, logger, capsys):
        """测试交易策略执行日志 - 量化交易的核心需求"""
        # 模拟策略执行日志场景
        strategy_name = "momentum_strategy_v2"
        symbol = "000001.XSHE"
        signal = "BUY"
        confidence = 0.85
        position_size = 1000
        
        # 记录策略决策过程
        logger.info(f"Strategy Decision: {strategy_name} generated {signal} signal for {symbol}")
        logger.info(f"Signal Details: confidence={confidence}, position_size={position_size}")
        logger.warning(f"Risk Alert: Large position size detected for {symbol}: {position_size} shares")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 验证业务价值：日志包含关键交易信息
        assert "momentum_strategy_v2" in output
        assert "BUY" in output
        assert "000001.XSHE" in output
        assert "confidence=0.85" in output
        assert "Risk Alert" in output
        assert "Large position size" in output
        
        # 验证日志级别正确
        assert "INFO" in output
        assert "WARNING" in output

    def test_risk_management_logging(self, logger, capsys):
        """测试风险管理日志 - 量化系统的安全保障"""
        # 模拟风险事件
        portfolio_var = 0.25  # 25% VaR
        max_drawdown = 0.18   # 18% 最大回撤
        position_concentration = 0.45  # 45%集中度
        
        # 记录风险告警
        logger.warning(f"Risk Threshold Exceeded: Portfolio VaR={portfolio_var:.2%}")
        logger.error(f"Critical Risk: Max drawdown reached {max_drawdown:.2%}")
        logger.critical(f"Emergency: Position concentration {position_concentration:.2%} exceeds limit")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 验证业务价值：风险信息被正确记录
        assert "Risk Threshold Exceeded" in output
        assert "25.00%" in output
        assert "Critical Risk" in output
        assert "18.00%" in output
        assert "Emergency" in output
        assert "45.00%" in output
        
        # 验证日志级别递增
        assert "WARNING" in output
        assert "ERROR" in output
        assert "CRITICAL" in output

    def test_portfolio_performance_logging(self, logger, capsys):
        """测试组合绩效日志 - 投资组合管理的关键信息"""
        # 模拟组合绩效数据
        daily_return = 0.025
        cumulative_return = 0.158
        sharpe_ratio = 1.85
        total_value = 1250000
        
        # 记录组合绩效
        logger.info(f"Portfolio Performance: Daily return {daily_return:.2%}, Cumulative {cumulative_return:.2%}")
        logger.info(f"Risk Metrics: Sharpe ratio {sharpe_ratio:.2f}, Total value ${total_value:,}")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 验证业务价值：绩效数据被正确记录
        assert "Portfolio Performance" in output
        assert "2.50%" in output  # daily_return
        assert "15.80%" in output  # cumulative_return
        assert "Sharpe ratio 1.85" in output
        assert "$1,250,000" in output

    def test_backtesting_simulation_logging(self, logger, capsys):
        """测试回测模拟日志 - 策略验证的核心过程"""
        # 设置回测时间
        backtest_time = datetime(2023, 12, 29, 14, 30, 45)
        logger.current_dt = backtest_time
        
        # 模拟回测过程
        strategy_id = "momentum_ma_crossover"
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        initial_capital = 1000000
        
        logger.info(f"Backtest Started: {strategy_id} from {start_date} to {end_date}")
        logger.info(f"Initial Capital: ${initial_capital:,}")
        logger.debug(f"Processing market data for date range...")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 验证业务价值：回测流程信息完整
        assert "Backtest Started" in output
        assert "momentum_ma_crossover" in output
        assert "2023-01-01" in output
        assert "$1,000,000" in output
        assert "2023-12-29 14:30:45" in output  # 时间戳
        
        # 验证日志级别
        assert "INFO" in output
        assert "DEBUG" in output

    def test_timestamp_precision_in_trading_context(self, logger):
        """测试交易上下文中的时间戳精度 - 交易系统的基本要求"""
        # 设置精确的交易时间
        trading_time = datetime(2023, 12, 29, 9, 30, 15)  # 开盘后15秒
        logger.current_dt = trading_time
        
        timestamp = logger._format_timestamp()
        assert timestamp == "2023-12-29 09:30:15"
        
        # 验证时间戳一致性（重要：同一秒内的多次交易应该有相同时间戳）
        timestamp2 = logger._format_timestamp()
        assert timestamp == timestamp2

    def test_system_error_recovery_logging(self, logger, capsys):
        """测试系统错误恢复日志 - 系统稳定性的关键指标"""
        # 模拟系统错误和恢复过程
        error_component = "data_feed"
        error_details = "Connection timeout to market data provider"
        recovery_action = "Switched to backup data source"
        
        logger.error(f"System Error in {error_component}: {error_details}")
        logger.info(f"Recovery Action: {recovery_action}")
        logger.info("System fully operational - resuming strategy execution")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 验证业务价值：错误和恢复过程被完整记录
        assert "System Error" in output
        assert "data_feed" in output
        assert "Connection timeout" in output
        assert "Recovery Action" in output
        assert "backup data source" in output
        assert "fully operational" in output


class TestGlobalLogInstance:
    """测试全局日志实例的核心功能"""

    def test_global_logger_trading_integration(self, capsys):
        """测试全局日志实例在交易场景中的使用"""
        # 使用全局日志实例记录交易事件
        order_id = "ORD_20241201_001"
        symbol = "000001.XSHE"
        quantity = 1000
        price = 15.25
        
        log.info(f"Order Placed: {order_id} - {symbol} {quantity}@{price}")
        log.info(f"Order Filled: {order_id} - execution successful")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 验证业务价值：全局日志可以跟踪完整的交易流程
        assert order_id in output
        assert symbol in output
        assert "1000@15.25" in output
        assert "execution successful" in output
        assert "INFO" in output

    def test_global_logger_system_monitoring(self, capsys):
        """测试全局日志实例的系统监控能力"""
        # 记录系统监控信息
        cpu_usage = 78.5
        memory_usage = 65.2
        active_strategies = 5
        
        log.warning(f"System Load: CPU {cpu_usage}%, Memory {memory_usage}%")
        log.info(f"Active Strategies: {active_strategies} running normally")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 验证业务价值：系统状态被持续监控和记录
        assert "System Load" in output
        assert "78.5%" in output
        assert "65.2%" in output
        assert "5 running normally" in output
        assert "WARNING" in output
        assert "INFO" in output