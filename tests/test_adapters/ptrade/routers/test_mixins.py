# -*- coding: utf-8 -*-
"""
PTrade Mixin类测试

测试所有Mixin类的功能和集成
"""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from simtradelab.adapters.ptrade.routers.common_utils_mixin import CommonUtilsMixin
from simtradelab.adapters.ptrade.routers.data_retrieval_mixin import DataRetrievalMixin
from simtradelab.adapters.ptrade.routers.stock_info_mixin import StockInfoMixin
from simtradelab.adapters.ptrade.routers.technical_indicator_mixin import (
    TechnicalIndicatorMixin,
)


class TestStockInfoMixin:
    """测试股票信息Mixin"""

    @pytest.fixture
    def mixin(self):
        """创建StockInfoMixin实例"""
        mixin = StockInfoMixin()
        mixin._data_plugin = MagicMock()
        return mixin

    def test_initialization(self):
        """测试初始化"""
        mixin = StockInfoMixin()
        assert hasattr(mixin, "_logger")
        assert hasattr(mixin, "_data_plugin")

    def test_get_stock_name_success(self, mixin):
        """测试获取股票名称成功"""
        # 设置mock返回值
        mixin._data_plugin.get_stock_name.return_value = "平安银行"

        result = mixin.get_stock_name("000001.XSHE")
        assert result == "平安银行"
        mixin._data_plugin.get_stock_name.assert_called_once_with("000001.XSHE")

    def test_get_stock_name_no_plugin(self, mixin):
        """测试无数据插件时获取股票名称"""
        mixin._data_plugin = None

        with pytest.raises(RuntimeError, match="Data plugin is not available"):
            mixin.get_stock_name("000001.XSHE")

    def test_get_stock_name_plugin_not_support(self, mixin):
        """测试数据插件不支持该方法"""
        # 移除方法支持
        delattr(mixin._data_plugin, "get_stock_name")

        with pytest.raises(
            NotImplementedError, match="does not support get_stock_name"
        ):
            mixin.get_stock_name("000001.XSHE")

    def test_get_stock_status_success(self, mixin):
        """测试获取股票状态成功"""
        expected_status = {"status": "normal", "trading": True, "suspended": False}
        mixin._data_plugin.get_stock_status.return_value = expected_status

        result = mixin.get_stock_status("000001.XSHE")
        assert result == expected_status

    def test_get_stock_exrights_success(self, mixin):
        """测试获取除权除息信息成功"""
        expected_df = pd.DataFrame(
            {"date": ["2023-06-01"], "dividend": [0.5], "split_ratio": [1.0]}
        )
        mixin._data_plugin.get_stock_exrights.return_value = expected_df

        result = mixin.get_stock_exrights("000001.XSHE")
        pd.testing.assert_frame_equal(result, expected_df)

    def test_get_stock_blocks_success(self, mixin):
        """测试获取股票板块成功"""
        expected_blocks = ["银行", "金融", "深圳本地"]
        mixin._data_plugin.get_stock_blocks.return_value = expected_blocks

        result = mixin.get_stock_blocks("000001.XSHE")
        assert result == expected_blocks

    def test_get_index_stocks_success(self, mixin):
        """测试获取指数成份股成功"""
        expected_stocks = ["000001.XSHE", "000002.XSHE", "600000.XSHG"]
        mixin._data_plugin.get_index_stocks.return_value = expected_stocks

        result = mixin.get_index_stocks("000300.SH")
        assert result == expected_stocks

    def test_get_industry_stocks_success(self, mixin):
        """测试获取行业成份股成功"""
        expected_stocks = ["000001.XSHE", "600036.XSHG"]
        mixin._data_plugin.get_industry_stocks.return_value = expected_stocks

        result = mixin.get_industry_stocks("银行")
        assert result == expected_stocks

    def test_get_ashares_success(self, mixin):
        """测试获取A股列表成功"""
        expected_stocks = ["000001.XSHE", "000002.XSHE", "600000.XSHG"]
        mixin._data_plugin.get_Ashares.return_value = expected_stocks

        result = mixin.get_Ashares("2023-12-29")
        assert result == expected_stocks

    def test_get_etf_list_success(self, mixin):
        """测试获取ETF列表成功"""
        expected_etfs = ["510050.XSHG", "159919.XSHE", "512880.XSHG"]
        mixin._data_plugin.get_etf_list.return_value = expected_etfs

        result = mixin.get_etf_list()
        assert result == expected_etfs

    def test_get_ipo_stocks_success(self, mixin):
        """测试获取IPO股票成功"""
        expected_ipos = ["300999.XSHE"]
        mixin._data_plugin.get_ipo_stocks.return_value = expected_ipos

        result = mixin.get_ipo_stocks("2023-12-29")
        assert result == expected_ipos


class TestTechnicalIndicatorMixin:
    """测试技术指标Mixin"""

    @pytest.fixture
    def mixin(self):
        """创建TechnicalIndicatorMixin实例"""
        return TechnicalIndicatorMixin()

    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        return {
            "close": np.array(
                [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
            ),
            "high": np.array(
                [10.2, 10.3, 10.4, 10.1, 10.5, 10.6, 10.3, 10.7, 10.8, 10.2]
            ),
            "low": np.array([9.8, 9.9, 10.0, 9.7, 10.1, 10.2, 9.9, 10.3, 10.4, 9.8]),
        }

    def test_initialization(self):
        """测试初始化"""
        mixin = TechnicalIndicatorMixin()
        assert hasattr(mixin, "_logger")

    def test_get_macd(self, mixin, sample_data):
        """测试MACD指标计算"""
        result = mixin.get_MACD(sample_data["close"])

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        assert len(result) == len(sample_data["close"])
        assert not result.isnull().all().any()  # 不应该全是NaN

    def test_get_macd_with_custom_params(self, mixin, sample_data):
        """测试带自定义参数的MACD"""
        result = mixin.get_MACD(sample_data["close"], short=5, long=10, m=3)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        assert len(result) == len(sample_data["close"])

    def test_get_kdj(self, mixin, sample_data):
        """测试KDJ指标计算"""
        result = mixin.get_KDJ(
            sample_data["high"], sample_data["low"], sample_data["close"]
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["K", "D", "J"]
        assert len(result) == len(sample_data["close"])

    def test_get_kdj_with_custom_params(self, mixin, sample_data):
        """测试带自定义参数的KDJ"""
        result = mixin.get_KDJ(
            sample_data["high"],
            sample_data["low"],
            sample_data["close"],
            n=5,
            m1=2,
            m2=2,
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["K", "D", "J"]

    def test_get_rsi(self, mixin, sample_data):
        """测试RSI指标计算"""
        result = mixin.get_RSI(sample_data["close"])

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["RSI"]
        assert len(result) == len(sample_data["close"])

    def test_get_rsi_with_custom_params(self, mixin, sample_data):
        """测试带自定义参数的RSI"""
        result = mixin.get_RSI(sample_data["close"], n=14)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["RSI"]

    def test_get_cci(self, mixin, sample_data):
        """测试CCI指标计算"""
        result = mixin.get_CCI(
            sample_data["high"], sample_data["low"], sample_data["close"]
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["CCI"]
        assert len(result) == len(sample_data["close"])

    def test_get_cci_with_custom_params(self, mixin, sample_data):
        """测试带自定义参数的CCI"""
        result = mixin.get_CCI(
            sample_data["high"], sample_data["low"], sample_data["close"], n=20
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["CCI"]

    def test_invalid_data_handling(self, mixin):
        """测试无效数据处理"""
        # 空数组
        empty_data = np.array([])

        with pytest.raises(RuntimeError):
            mixin.get_MACD(empty_data)

        # 包含NaN的数据
        nan_data = np.array([10.0, np.nan, 10.2, 9.9])

        # 应该能处理NaN（pandas会处理）
        result = mixin.get_RSI(nan_data)
        assert isinstance(result, pd.DataFrame)


class TestDataRetrievalMixin:
    """测试数据获取Mixin"""

    @pytest.fixture
    def mixin(self):
        """创建DataRetrievalMixin实例"""
        mixin = DataRetrievalMixin()
        mixin._data_plugin = MagicMock()
        # 模拟context
        mixin.context = MagicMock()
        mixin.context.universe = ["000001.XSHE", "000002.XSHE"]
        return mixin

    def test_initialization(self):
        """测试初始化"""
        mixin = DataRetrievalMixin()
        assert hasattr(mixin, "_logger")
        assert hasattr(mixin, "_data_plugin")

    def test_get_history_success(self, mixin):
        """测试获取历史数据成功"""
        expected_df = pd.DataFrame(
            {
                "open": [10.0, 10.1],
                "high": [10.2, 10.3],
                "low": [9.8, 9.9],
                "close": [10.1, 10.2],
                "volume": [1000, 1100],
            },
            index=pd.date_range("2023-12-28", periods=2),
        )

        mixin._data_plugin.get_multiple_history_data.return_value = expected_df

        result = mixin.get_history(
            count=2, field=["open", "high", "low", "close", "volume"]
        )
        pd.testing.assert_frame_equal(result, expected_df)

    def test_get_history_as_dict(self, mixin):
        """测试获取历史数据字典格式"""
        # DataRetrievalMixin expects DataFrame from data plugin, then converts to dict
        expected_df = pd.DataFrame(
            {
                "security": [
                    "000001.XSHE",
                    "000001.XSHE",
                    "000002.XSHE",
                    "000002.XSHE",
                ],
                "close": [10.1, 10.2, 20.1, 20.2],
                "volume": [1000, 1100, 2000, 2100],
            }
        )

        mixin._data_plugin.get_multiple_history_data.return_value = expected_df

        result = mixin.get_history(count=2, field=["close", "volume"], is_dict=True)

        # Check the result is a dictionary with expected structure
        assert isinstance(result, dict)
        assert "000001.XSHE" in result
        assert "000002.XSHE" in result
        assert "close" in result["000001.XSHE"]
        assert "volume" in result["000001.XSHE"]

    def test_get_price_success(self, mixin):
        """测试获取价格数据成功"""
        expected_df = pd.DataFrame(
            {
                "open": [10.0, 10.1],
                "high": [10.2, 10.3],
                "low": [9.8, 9.9],
                "close": [10.1, 10.2],
                "volume": [1000, 1100],
            }
        )

        mixin._data_plugin.get_multiple_history_data.return_value = expected_df

        result = mixin.get_price("000001.XSHE", count=2)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_get_snapshot_success(self, mixin):
        """测试获取快照数据成功"""
        # DataRetrievalMixin expects get_market_snapshot to return a dict
        snapshot_data = {
            "000001.XSHE": {
                "last_price": 10.5,
                "volume": 1500,
                "datetime": pd.Timestamp.now(),
            },
            "000002.XSHE": {
                "last_price": 20.3,
                "volume": 2500,
                "datetime": pd.Timestamp.now(),
            },
        }

        mixin._data_plugin.get_market_snapshot.return_value = snapshot_data

        result = mixin.get_snapshot(["000001.XSHE", "000002.XSHE"])

        assert isinstance(result, pd.DataFrame)
        assert result.shape[0] == 2
        assert "current_price" in result.columns
        assert "volume" in result.columns

    def test_get_stock_info_success(self, mixin):
        """测试获取股票信息成功"""

        # DataRetrievalMixin uses get_stock_basic_info method
        def mock_get_stock_basic_info(security):
            if security == "000001.XSHE":
                return {"name": "平安银行", "market": "SZSE", "type": "stock"}
            elif security == "000002.XSHE":
                return {"name": "万科A", "market": "SZSE", "type": "stock"}
            else:
                raise Exception("Stock not found")

        mixin._data_plugin.get_stock_basic_info.side_effect = mock_get_stock_basic_info

        result = mixin.get_stock_info(["000001.XSHE", "000002.XSHE"])

        assert isinstance(result, dict)
        assert "000001.XSHE" in result
        assert "000002.XSHE" in result
        assert result["000001.XSHE"]["name"] == "平安银行"
        assert result["000002.XSHE"]["name"] == "万科A"

    def test_get_fundamentals_success(self, mixin):
        """测试获取基本面数据成功"""
        expected_df = pd.DataFrame(
            {
                "code": ["000001.XSHE", "000002.XSHE"],
                "revenue": [100000, 200000],
                "net_profit": [20000, 30000],
                "date": ["2023-12-31", "2023-12-31"],
            }
        )

        mixin._data_plugin.get_fundamentals.return_value = expected_df

        result = mixin.get_fundamentals(
            stocks=["000001.XSHE", "000002.XSHE"],
            table="income",
            fields=["revenue", "net_profit"],
            date="2023-12-31",
        )
        pd.testing.assert_frame_equal(result, expected_df)


class TestCommonUtilsMixin:
    """测试通用工具Mixin"""

    @pytest.fixture
    def mixin(self):
        """创建CommonUtilsMixin实例"""
        mixin = CommonUtilsMixin()
        mixin._data_plugin = MagicMock()
        return mixin

    def test_initialization(self):
        """测试初始化"""
        mixin = CommonUtilsMixin()
        assert hasattr(mixin, "_logger")

    def test_log_info(self, mixin):
        """测试信息日志"""
        # 这个测试主要验证方法调用不出错
        mixin.log("Test info message", "info")
        # 由于是日志记录，我们主要确认不抛出异常

    def test_log_warning(self, mixin):
        """测试警告日志"""
        mixin.log("Test warning message", "warning")

    def test_log_error(self, mixin):
        """测试错误日志"""
        mixin.log("Test error message", "error")

    def test_log_invalid_level(self, mixin):
        """测试无效日志级别"""
        # 无效级别应该被处理，不应该抛出异常
        mixin.log("Test message", "invalid_level")

    def test_check_limit_success(self, mixin):
        """测试检查涨跌停成功"""
        expected_result = {
            "000001.XSHE": {
                "limit_up": False,
                "limit_down": False,
                "current_price": 10.5,
                "limit_up_price": 11.55,
                "limit_down_price": 9.45,
            }
        }

        mixin._data_plugin.check_limit_status.return_value = expected_result

        result = mixin.check_limit("000001.XSHE")
        assert result == expected_result

    def test_get_trading_day_success(self, mixin):
        """测试获取交易日成功"""
        mixin._data_plugin.get_trading_day.return_value = "2024-01-02"

        result = mixin.get_trading_day("2023-12-29", 1)
        assert result == "2024-01-02"

    def test_get_all_trades_days_success(self, mixin):
        """测试获取所有交易日成功"""
        expected_days = [
            "2023-12-25",
            "2023-12-26",
            "2023-12-27",
            "2023-12-28",
            "2023-12-29",
        ]

        mixin._data_plugin.get_all_trading_days.return_value = expected_days

        result = mixin.get_all_trades_days()
        assert result == expected_days

    def test_get_trade_days_success(self, mixin):
        """测试获取指定范围交易日成功"""
        expected_days = ["2023-12-25", "2023-12-26", "2023-12-27"]

        mixin._data_plugin.get_trading_days_range.return_value = expected_days

        result = mixin.get_trade_days("2023-12-25", "2023-12-27")
        assert result == expected_days

    def test_is_trade_current_time(self, mixin):
        """测试is_trade()使用当前时间"""
        # 测试不传入时间参数时使用当前时间
        result = mixin.is_trade()
        assert isinstance(result, bool)

    def test_is_trade_weekdays_trading_hours(self, mixin):
        """测试工作日交易时间"""
        from datetime import datetime

        # 周一上午交易时间 (09:30-11:30)
        monday_morning = datetime(2024, 1, 8, 10, 30, 0)  # 2024年1月8日是周一
        assert mixin.is_trade(monday_morning) is True

        # 周二下午交易时间 (13:00-15:00)
        tuesday_afternoon = datetime(2024, 1, 9, 14, 30, 0)  # 2024年1月9日是周二
        assert mixin.is_trade(tuesday_afternoon) is True

        # 周三上午交易开始时间 (09:30)
        wednesday_start = datetime(2024, 1, 10, 9, 30, 0)  # 2024年1月10日是周三
        assert mixin.is_trade(wednesday_start) is True

        # 周四上午交易结束时间 (11:30)
        thursday_end = datetime(2024, 1, 11, 11, 30, 0)  # 2024年1月11日是周四
        assert mixin.is_trade(thursday_end) is True

        # 周五下午交易开始时间 (13:00)
        friday_afternoon_start = datetime(2024, 1, 12, 13, 0, 0)  # 2024年1月12日是周五
        assert mixin.is_trade(friday_afternoon_start) is True

        # 周五下午交易结束时间 (15:00)
        friday_afternoon_end = datetime(2024, 1, 12, 15, 0, 0)
        assert mixin.is_trade(friday_afternoon_end) is True

    def test_is_trade_weekdays_non_trading_hours(self, mixin):
        """测试工作日非交易时间"""
        from datetime import datetime

        # 周一早晨交易前 (09:29)
        monday_early = datetime(2024, 1, 8, 9, 29, 0)
        assert mixin.is_trade(monday_early) is False

        # 周二中午休市时间 (12:00)
        tuesday_lunch = datetime(2024, 1, 9, 12, 0, 0)
        assert mixin.is_trade(tuesday_lunch) is False

        # 周三上午交易结束后 (11:31)
        wednesday_after_morning = datetime(2024, 1, 10, 11, 31, 0)
        assert mixin.is_trade(wednesday_after_morning) is False

        # 周四下午交易前 (12:59)
        thursday_before_afternoon = datetime(2024, 1, 11, 12, 59, 0)
        assert mixin.is_trade(thursday_before_afternoon) is False

        # 周五晚上交易后 (15:01)
        friday_after_trading = datetime(2024, 1, 12, 15, 1, 0)
        assert mixin.is_trade(friday_after_trading) is False

        # 凌晨时间
        early_morning = datetime(2024, 1, 8, 3, 0, 0)
        assert mixin.is_trade(early_morning) is False

        # 深夜时间
        late_night = datetime(2024, 1, 8, 23, 0, 0)
        assert mixin.is_trade(late_night) is False

    def test_is_trade_weekends(self, mixin):
        """测试周末时间"""
        from datetime import datetime

        # 周六上午交易时间段
        saturday_morning = datetime(2024, 1, 13, 10, 30, 0)  # 2024年1月13日是周六
        assert mixin.is_trade(saturday_morning) is False

        # 周六下午交易时间段
        saturday_afternoon = datetime(2024, 1, 13, 14, 30, 0)
        assert mixin.is_trade(saturday_afternoon) is False

        # 周日上午交易时间段
        sunday_morning = datetime(2024, 1, 14, 10, 30, 0)  # 2024年1月14日是周日
        assert mixin.is_trade(sunday_morning) is False

        # 周日下午交易时间段
        sunday_afternoon = datetime(2024, 1, 14, 14, 30, 0)
        assert mixin.is_trade(sunday_afternoon) is False

        # 周末非交易时间段
        saturday_night = datetime(2024, 1, 13, 20, 0, 0)
        assert mixin.is_trade(saturday_night) is False

        sunday_early = datetime(2024, 1, 14, 8, 0, 0)
        assert mixin.is_trade(sunday_early) is False

    def test_is_trade_boundary_times(self, mixin):
        """测试边界时间点"""
        from datetime import datetime

        # 上午交易边界时间
        morning_before = datetime(2024, 1, 8, 9, 29, 59)  # 09:29:59
        assert mixin.is_trade(morning_before) is False

        morning_start_exact = datetime(2024, 1, 8, 9, 30, 0)  # 09:30:00
        assert mixin.is_trade(morning_start_exact) is True

        morning_end_exact = datetime(2024, 1, 8, 11, 30, 0)  # 11:30:00
        assert mixin.is_trade(morning_end_exact) is True

        morning_after = datetime(2024, 1, 8, 11, 30, 1)  # 11:30:01
        assert mixin.is_trade(morning_after) is False

        # 下午交易边界时间
        afternoon_before = datetime(2024, 1, 8, 12, 59, 59)  # 12:59:59
        assert mixin.is_trade(afternoon_before) is False

        afternoon_start_exact = datetime(2024, 1, 8, 13, 0, 0)  # 13:00:00
        assert mixin.is_trade(afternoon_start_exact) is True

        afternoon_end_exact = datetime(2024, 1, 8, 15, 0, 0)  # 15:00:00
        assert mixin.is_trade(afternoon_end_exact) is True

        afternoon_after = datetime(2024, 1, 8, 15, 0, 1)  # 15:00:01
        assert mixin.is_trade(afternoon_after) is False

    def test_is_trade_all_weekdays(self, mixin):
        """测试所有工作日"""
        from datetime import datetime

        # 测试2024年1月8-12日 (周一到周五)
        weekdays = [
            (2024, 1, 8),  # 周一
            (2024, 1, 9),  # 周二
            (2024, 1, 10),  # 周三
            (2024, 1, 11),  # 周四
            (2024, 1, 12),  # 周五
        ]

        for year, month, day in weekdays:
            # 测试上午交易时间
            morning_time = datetime(year, month, day, 10, 30, 0)
            assert (
                mixin.is_trade(morning_time) is True
            ), f"Failed for {year}-{month}-{day} morning"

            # 测试下午交易时间
            afternoon_time = datetime(year, month, day, 14, 30, 0)
            assert (
                mixin.is_trade(afternoon_time) is True
            ), f"Failed for {year}-{month}-{day} afternoon"

            # 测试非交易时间
            non_trading_time = datetime(year, month, day, 8, 0, 0)
            assert (
                mixin.is_trade(non_trading_time) is False
            ), f"Failed for {year}-{month}-{day} non-trading"

    def test_is_trade_special_cases(self, mixin):
        """测试特殊情况"""
        from datetime import datetime

        # 测试不同年份
        different_years = [
            datetime(2023, 6, 15, 10, 30, 0),  # 2023年周四
            datetime(2025, 3, 10, 14, 30, 0),  # 2025年周一
        ]

        for test_time in different_years:
            if test_time.weekday() < 5:  # 工作日
                assert mixin.is_trade(test_time) is True
            else:  # 周末
                assert mixin.is_trade(test_time) is False

        # 测试闰年2月29日 (如果是工作日)
        leap_year_date = datetime(2024, 2, 29, 10, 30, 0)  # 2024年2月29日是周四
        assert mixin.is_trade(leap_year_date) is True

        # 测试年末年初
        year_end = datetime(2023, 12, 29, 10, 30, 0)  # 2023年12月29日是周五
        assert mixin.is_trade(year_end) is True

        year_start = datetime(2024, 1, 2, 10, 30, 0)  # 2024年1月2日是周二
        assert mixin.is_trade(year_start) is True


class TestMixinIntegration:
    """测试Mixin集成功能"""

    def test_multiple_inheritance(self):
        """测试多重继承"""

        class TestRouter(
            StockInfoMixin,
            TechnicalIndicatorMixin,
            DataRetrievalMixin,
            CommonUtilsMixin,
        ):
            def __init__(self):
                super().__init__()
                self._data_plugin = MagicMock()
                self.context = MagicMock()
                self.context.universe = ["000001.XSHE"]

        router = TestRouter()

        # 验证所有Mixin的方法都可用
        assert hasattr(router, "get_stock_name")
        assert hasattr(router, "get_MACD")
        assert hasattr(router, "get_history")
        assert hasattr(router, "log")

    def test_method_resolution_order(self):
        """测试方法解析顺序"""

        class TestRouter(
            StockInfoMixin,
            TechnicalIndicatorMixin,
            DataRetrievalMixin,
            CommonUtilsMixin,
        ):
            pass

        # 检查MRO中包含所有Mixin
        mro_names = [cls.__name__ for cls in TestRouter.__mro__]
        assert "StockInfoMixin" in mro_names
        assert "TechnicalIndicatorMixin" in mro_names
        assert "DataRetrievalMixin" in mro_names
        assert "CommonUtilsMixin" in mro_names

    def test_shared_attributes(self):
        """测试共享属性"""

        class TestRouter(
            StockInfoMixin,
            TechnicalIndicatorMixin,
            DataRetrievalMixin,
            CommonUtilsMixin,
        ):
            def __init__(self):
                super().__init__()

        router = TestRouter()

        # 所有Mixin都应该共享_logger属性
        assert hasattr(router, "_logger")
        assert router._logger is not None
