"""
pytest配置文件和共享fixtures
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab import BacktestEngine
from simtradelab.data_sources import CSVDataSource, AkshareDataSource


@pytest.fixture(scope="session")
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def sample_data_path(project_root):
    """示例数据文件路径"""
    return project_root / "data" / "sample_data.csv"


@pytest.fixture(scope="session")
def test_strategy_path(project_root):
    """测试策略文件路径"""
    return project_root / "strategies" / "test_strategy.py"


@pytest.fixture
def temp_dir():
    """临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_csv_data():
    """模拟CSV数据"""
    import pandas as pd
    from datetime import datetime, timedelta
    
    dates = [datetime(2023, 1, 3) + timedelta(days=i) for i in range(5)]
    
    data = {
        'date': dates * 2,
        'security': ['STOCK_A'] * 5 + ['STOCK_B'] * 5,
        'open': [100, 101, 102, 103, 104, 50, 51, 52, 53, 54],
        'high': [105, 106, 107, 108, 109, 55, 56, 57, 58, 59],
        'low': [95, 96, 97, 98, 99, 45, 46, 47, 48, 49],
        'close': [102, 103, 104, 105, 106, 52, 53, 54, 55, 56],
        'volume': [1000000] * 10
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def csv_engine(sample_data_path, test_strategy_path):
    """CSV数据源的回测引擎"""
    if not sample_data_path.exists():
        pytest.skip(f"Sample data file not found: {sample_data_path}")
    
    if not test_strategy_path.exists():
        pytest.skip(f"Test strategy file not found: {test_strategy_path}")
    
    return BacktestEngine(
        strategy_file=str(test_strategy_path),
        data_path=str(sample_data_path),
        start_date='2023-01-03',
        end_date='2023-01-05',
        initial_cash=1000000.0
    )


@pytest.fixture
def simple_strategy_file(temp_dir):
    """创建简单的测试策略文件"""
    strategy_content = '''
def initialize(context):
    """策略初始化"""
    context.test_var = "initialized"

def handle_data(context, data):
    """处理数据"""
    pass

def before_trading_start(context, data):
    """交易前处理"""
    pass

def after_trading_end(context, data):
    """交易后处理"""
    pass
'''
    
    strategy_path = Path(temp_dir) / "simple_strategy.py"
    strategy_path.write_text(strategy_content, encoding='utf-8')
    return str(strategy_path)


@pytest.fixture
def mock_akshare_data():
    """模拟AkShare数据"""
    import pandas as pd
    from datetime import datetime, timedelta
    
    dates = pd.date_range('2024-12-01', '2024-12-05', freq='D')
    
    stock_data = {}
    for stock in ['000001.SZ', '000002.SZ']:
        stock_data[stock] = pd.DataFrame({
            'open': [10.0, 10.1, 10.2, 10.3, 10.4],
            'high': [10.5, 10.6, 10.7, 10.8, 10.9],
            'low': [9.5, 9.6, 9.7, 9.8, 9.9],
            'close': [10.2, 10.3, 10.4, 10.5, 10.6],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        }, index=dates)
    
    return stock_data


@pytest.fixture
def mock_akshare_source(mock_akshare_data):
    """模拟的AkShare数据源"""
    with patch('simtradelab.data_sources.akshare_source.ak') as mock_ak:
        # 模拟ak.stock_zh_a_hist函数
        def mock_stock_hist(symbol, period="daily", start_date=None, end_date=None, adjust=""):
            import pandas as pd
            # AkShare数据源会将000001.SZ转换为000001，所以我们需要相应地匹配
            stock_code = symbol
            if not '.' in stock_code:
                # 将6位代码转换为标准格式
                if stock_code.startswith('00') or stock_code.startswith('30'):
                    stock_code = f"{stock_code}.SZ"
                elif stock_code.startswith('60') or stock_code.startswith('68'):
                    stock_code = f"{stock_code}.SH"
                else:
                    stock_code = f"{stock_code}.SZ"

            if stock_code in mock_akshare_data:
                df = mock_akshare_data[stock_code].copy()
                # 重置索引并添加日期列，使用AkShare的列名
                df = df.reset_index()
                df.columns = ['日期', '开盘', '最高', '最低', '收盘', '成交量']
                return df
            else:
                # 返回空DataFrame，但有正确的列名
                return pd.DataFrame(columns=['日期', '开盘', '最高', '最低', '收盘', '成交量'])
        
        mock_ak.stock_zh_a_hist.side_effect = mock_stock_hist
        
        source = AkshareDataSource()
        yield source


@pytest.fixture(autouse=True)
def setup_test_environment():
    """设置测试环境"""
    # 设置测试环境变量
    os.environ['PTRADE_TEST_MODE'] = '1'
    
    yield
    
    # 清理测试环境
    if 'PTRADE_TEST_MODE' in os.environ:
        del os.environ['PTRADE_TEST_MODE']


@pytest.fixture
def capture_logs():
    """捕获日志输出"""
    import logging
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger('simtradelab')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    yield log_capture

    logger.removeHandler(handler)


@pytest.fixture
def sample_strategy_file(temp_dir):
    """创建示例策略文件"""
    strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.counter = 0

def handle_data(context, data):
    context.counter += 1
    if len(data) > 0:
        stock = list(data.keys())[0]
        if context.counter == 1:
            order(stock, 100)

def before_trading_start(context, data):
    pass

def after_trading_end(context, data):
    pass
'''

    strategy_path = Path(temp_dir) / "sample_strategy.py"
    strategy_path.write_text(strategy_content, encoding='utf-8')
    return str(strategy_path)


@pytest.fixture
def sample_data_file(temp_dir):
    """创建示例数据文件"""
    import pandas as pd

    data_rows = []
    for i in range(10):
        for stock in ['STOCK_A', 'STOCK_B']:
            data_rows.append({
                'date': f'2023-01-{i+1:02d}',
                'security': stock,
                'open': 10.0 + i * 0.1,
                'high': 11.0 + i * 0.1,
                'low': 9.0 + i * 0.1,
                'close': 10.5 + i * 0.1,
                'volume': 1000 + i * 100
            })

    df = pd.DataFrame(data_rows)
    data_path = Path(temp_dir) / "sample_data.csv"
    df.to_csv(data_path, index=False)
    return str(data_path)


# 测试标记
def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "data: 需要数据文件的测试")
    config.addinivalue_line("markers", "network: 需要网络访问的测试")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为需要网络的测试添加标记
    for item in items:
        if "akshare" in item.nodeid.lower() or "tushare" in item.nodeid.lower():
            item.add_marker(pytest.mark.network)
        
        if "test_real_data" in item.nodeid:
            item.add_marker(pytest.mark.network)
            item.add_marker(pytest.mark.slow)
