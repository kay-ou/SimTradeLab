# -*- coding: utf-8 -*-
"""
市场数据接口模块
"""
import hashlib
import pandas as pd
import numpy as np
from .logger import log

def get_history(engine, count, frequency='1d', field='close', security_list=None, fq=None, include=False, is_dict=False, start_date=None, end_date=None):
    """
    增强的历史数据获取函数
    """
    if security_list is None:
        security_list = list(engine.data.keys())

    if isinstance(field, str):
        field = [field]

    frequency_mapping = {
        '1d': 'D', 'daily': 'D', '1m': 'T', 'minute': 'T', '5m': '5T', '5min': '5T',
        '15m': '15T', '15min': '15T', '30m': '30T', '30min': '30T', '1h': 'H',
        'hour': 'H', '1w': 'W', 'week': 'W', '1M': 'M', 'month': 'M'
    }
    pandas_freq = frequency_mapping.get(frequency, 'D')

    extended_fields = {
        'pre_close', 'change', 'pct_change', 'amplitude',
        'turnover_rate', 'amount', 'vwap', 'high_limit', 'low_limit'
    }

    if is_dict:
        result = {}
        for sec in security_list:
            if sec not in engine.data:
                result[sec] = {col: np.array([]) for col in field}
                continue

            hist_df = engine.data[sec].copy()

            if hasattr(engine, 'context') and engine.context.current_dt:
                valid_hist = hist_df[hist_df.index <= engine.context.current_dt] if include else hist_df[hist_df.index < engine.context.current_dt]
            else:
                valid_hist = hist_df

            if start_date:
                valid_hist = valid_hist[valid_hist.index >= pd.to_datetime(start_date)]
            if end_date:
                valid_hist = valid_hist[valid_hist.index <= pd.to_datetime(end_date)]

            if pandas_freq != 'D' and not valid_hist.empty:
                if pandas_freq in ['T', '5T', '15T', '30T', 'H']:
                    expanded_data = []
                    for _, row in valid_hist.iterrows():
                        periods_per_day = 240 if pandas_freq == 'T' else 48 if pandas_freq == '5T' else 16 if pandas_freq == '15T' else 8 if pandas_freq == '30T' else 4
                        day_start = _.replace(hour=9, minute=30)
                        time_range = pd.date_range(start=day_start, periods=periods_per_day, freq=pandas_freq)
                        daily_range = row['high'] - row['low']
                        for i, _ in enumerate(time_range):
                            progress = i / periods_per_day
                            noise = np.random.normal(0, daily_range * 0.01)
                            minute_close = max(row['low'], min(row['high'], row['low'] + daily_range * progress + noise))
                            expanded_data.append({
                                'open': minute_close * (1 + np.random.normal(0, 0.001)),
                                'high': minute_close * (1 + abs(np.random.normal(0, 0.002))),
                                'low': minute_close * (1 - abs(np.random.normal(0, 0.002))),
                                'close': minute_close,
                                'volume': row['volume'] / periods_per_day
                            })
                    if expanded_data:
                        valid_hist = pd.DataFrame(expanded_data)
                        valid_hist.index = pd.date_range(start=valid_hist.index[0].replace(hour=9, minute=30), periods=len(expanded_data), freq=pandas_freq)
                elif pandas_freq in ['W', 'M']:
                    valid_hist = valid_hist.resample(pandas_freq).agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()

            if count and len(valid_hist) > count:
                valid_hist = valid_hist.tail(count)

            if valid_hist.empty:
                result[sec] = {col: np.array([]) for col in field}
                continue

            for ext_field in field:
                if ext_field in extended_fields:
                    pre_close = valid_hist['close'].shift(1)
                    if ext_field == 'pre_close':
                        valid_hist['pre_close'] = pre_close
                    elif ext_field == 'change':
                        valid_hist['change'] = valid_hist['close'] - pre_close
                    elif ext_field == 'pct_change':
                        valid_hist['pct_change'] = (valid_hist['close'] / pre_close - 1) * 100
                    elif ext_field == 'amplitude':
                        valid_hist['amplitude'] = ((valid_hist['high'] - valid_hist['low']) / pre_close) * 100
                    elif ext_field == 'turnover_rate':
                        hash_factor = int(hashlib.md5(sec.encode()).hexdigest()[:8], 16) / 0xffffffff
                        valid_hist['turnover_rate'] = 2.5 + 5.0 * hash_factor
                    elif ext_field == 'amount':
                        valid_hist['amount'] = valid_hist['volume'] * valid_hist['close'] / 10000
                    elif ext_field == 'vwap':
                        valid_hist['vwap'] = (valid_hist['high'] + valid_hist['low'] + valid_hist['close'] * 2) / 4
                    elif ext_field == 'high_limit':
                        valid_hist['high_limit'] = pre_close * 1.1
                    elif ext_field == 'low_limit':
                        valid_hist['low_limit'] = pre_close * 0.9

            result[sec] = {col: valid_hist[col].to_numpy() if col in valid_hist.columns else np.array([]) for col in field}
        return result

    result_df = pd.DataFrame()
    for sec in security_list:
        if sec not in engine.data:
            continue
        hist_df = engine.data[sec].copy()
        if hasattr(engine, 'context') and engine.context.current_dt:
            valid_hist = hist_df[hist_df.index <= engine.context.current_dt] if include else hist_df[hist_df.index < engine.context.current_dt]
        else:
            valid_hist = hist_df
        if start_date:
            valid_hist = valid_hist[valid_hist.index >= pd.to_datetime(start_date)]
        if end_date:
            valid_hist = valid_hist[valid_hist.index <= pd.to_datetime(end_date)]
        if count and len(valid_hist) > count:
            valid_hist = valid_hist.tail(count)
        if valid_hist.empty:
            continue
        for f in field:
            if f in valid_hist.columns:
                result_df[(f, sec)] = valid_hist[f]
            else:
                log.warning(f"字段 '{f}' 不存在")
    return result_df

def get_price(engine, security, start_date=None, end_date=None, frequency='1d', fields=None, count=None):
    """
    增强的价格数据获取函数
    """
    count = count or 1
    securities = [security] if isinstance(security, str) else security
    fields = ['close'] if fields is None else ([fields] if isinstance(fields, str) else fields)

    all_supported_fields = {
        'open', 'high', 'low', 'close', 'volume', 'pre_close', 'change', 'pct_change',
        'amplitude', 'turnover_rate', 'vwap', 'amount', 'high_limit', 'low_limit'
    }

    result_data = {}
    for sec in securities:
        if sec not in engine.data:
            log.warning(f"股票 {sec} 的数据不存在")
            continue

        hist_df = engine.data[sec]
        current_dt = engine.context.current_dt if hasattr(engine, 'context') else None
        valid_hist = hist_df[hist_df.index < current_dt] if current_dt else hist_df

        if valid_hist.empty:
            log.warning(f"股票 {sec} 没有有效的历史数据")
            continue

        recent_data = valid_hist.tail(count)
        result_data[sec] = {}
        for field in fields:
            if field in recent_data.columns:
                result_data[sec][field] = recent_data[field].tolist()
            elif field in all_supported_fields:
                calculated_values = []
                for _, row in recent_data.iterrows():
                    pre_close = row['close'] * 0.98
                    if field == 'pre_close':
                        calculated_values.append(pre_close)
                    elif field == 'change':
                        calculated_values.append(row['close'] - pre_close)
                    elif field == 'pct_change':
                        calculated_values.append(((row['close'] - pre_close) / pre_close) * 100)
                    elif field == 'amplitude':
                        calculated_values.append(((row['high'] - row['low']) / pre_close) * 100)
                    elif field == 'turnover_rate':
                        hash_factor = int(hashlib.md5(sec.encode()).hexdigest()[:8], 16) / 0xffffffff
                        calculated_values.append(2.5 + 5.0 * hash_factor)
                    elif field == 'vwap':
                        calculated_values.append((row['high'] + row['low'] + row['close'] * 2) / 4)
                    elif field == 'amount':
                        calculated_values.append(row['volume'] * row['close'] / 10000)
                    elif field == 'high_limit':
                        calculated_values.append(pre_close * 1.1)
                    elif field == 'low_limit':
                        calculated_values.append(pre_close * 0.9)
                result_data[sec][field] = calculated_values
            else:
                log.warning(f"不支持的字段: {field}")
                result_data[sec][field] = [None] * count

    if not result_data:
        return pd.DataFrame()

    sample_data = engine.data[securities[0]]
    current_dt = engine.context.current_dt if hasattr(engine, 'context') else None
    valid_hist = sample_data[sample_data.index < current_dt] if current_dt else sample_data
    time_index = valid_hist.tail(count).index

    result_df = pd.DataFrame()
    for field in fields:
        for sec in securities:
            if sec in result_data and field in result_data[sec] and len(result_data[sec][field]) == len(time_index):
                result_df[(field, sec)] = pd.Series(result_data[sec][field], index=time_index)

    if len(fields) == 1:
        result_df.columns = [col[1] for col in result_df.columns]

    return result_df

def get_current_data(engine, security=None):
    """
    获取当前实时市场数据
    """
    securities = list(engine.data.keys()) if security is None else ([security] if isinstance(security, str) else security)
    current_data = {}
    for sec in securities:
        if sec not in engine.data:
            log.warning(f"股票 {sec} 的数据不存在")
            continue

        hist_df = engine.data[sec]
        current_dt = engine.context.current_dt if hasattr(engine, 'context') else None
        valid_hist = hist_df[hist_df.index <= current_dt] if current_dt else hist_df

        if valid_hist.empty:
            continue

        latest_data = valid_hist.iloc[-1]
        hash_factor = int(hashlib.md5(sec.encode()).hexdigest()[:8], 16) / 0xffffffff
        current_price = latest_data['close']
        spread = current_price * 0.001

        current_data[sec] = {
            'open': latest_data['open'], 'high': latest_data['high'], 'low': latest_data['low'],
            'close': current_price, 'volume': latest_data['volume'],
            'bid1': current_price - spread, 'bid2': current_price - spread * 2, 'bid3': current_price - spread * 3,
            'bid4': current_price - spread * 4, 'bid5': current_price - spread * 5,
            'ask1': current_price + spread, 'ask2': current_price + spread * 2, 'ask3': current_price + spread * 3,
            'ask4': current_price + spread * 4, 'ask5': current_price + spread * 5,
            'bid1_volume': int(1000 + 5000 * hash_factor), 'bid2_volume': int(800 + 4000 * hash_factor),
            'bid3_volume': int(600 + 3000 * hash_factor), 'bid4_volume': int(400 + 2000 * hash_factor),
            'bid5_volume': int(200 + 1000 * hash_factor), 'ask1_volume': int(1200 + 5500 * hash_factor),
            'ask2_volume': int(900 + 4500 * hash_factor), 'ask3_volume': int(700 + 3500 * hash_factor),
            'ask4_volume': int(500 + 2500 * hash_factor), 'ask5_volume': int(300 + 1500 * hash_factor),
            'pre_close': current_price * 0.98, 'change': current_price * 0.02, 'pct_change': 2.04,
            'amount': latest_data['volume'] * current_price / 10000,
            'turnover_rate': 2.5 + 5.0 * hash_factor,
            'high_limit': current_price * 0.98 * 1.1, 'low_limit': current_price * 0.98 * 0.9,
            'amplitude': ((latest_data['high'] - latest_data['low']) / (current_price * 0.98)) * 100,
            'vwap': (latest_data['high'] + latest_data['low'] + current_price * 2) / 4,
        }
    return current_data

def get_market_snapshot(engine, security=None, fields=None):
    """
    获取市场快照数据
    """
    current_data = get_current_data(engine, security)
    if not current_data:
        return pd.DataFrame()

    all_fields = [
        'open', 'high', 'low', 'close', 'volume', 'amount', 'pre_close', 'change', 'pct_change',
        'amplitude', 'turnover_rate', 'bid1', 'bid2', 'bid3', 'bid4', 'bid5', 'ask1', 'ask2', 'ask3',
        'ask4', 'ask5', 'bid1_volume', 'bid2_volume', 'bid3_volume', 'bid4_volume', 'bid5_volume',
        'ask1_volume', 'ask2_volume', 'ask3_volume', 'ask4_volume', 'ask5_volume', 'high_limit',
        'low_limit', 'vwap'
    ]
    fields = ['open', 'high', 'low', 'close', 'volume', 'change', 'pct_change'] if fields is None else ([fields] if isinstance(fields, str) else fields)

    data_dict = {field: [current_data[sec].get(field) for sec in current_data] for field in fields}
    return pd.DataFrame(data_dict, index=list(current_data.keys()))

def get_technical_indicators(engine, security, indicators, period=20, **kwargs):
    """
    计算技术指标
    """
    securities = [security] if isinstance(security, str) else security
    indicators = [indicators] if isinstance(indicators, str) else indicators
    result_data = {}

    for sec in securities:
        if sec not in engine.data:
            log.warning(f"股票 {sec} 的数据不存在")
            continue

        hist_df = engine.data[sec]
        current_dt = engine.context.current_dt if hasattr(engine, 'context') else None
        valid_hist = hist_df[hist_df.index <= current_dt] if current_dt else hist_df

        if len(valid_hist) < period:
            log.warning(f"股票 {sec} 的历史数据不足，需要至少 {period} 条数据")
            continue

        result_data[sec] = {}
        close_prices = valid_hist['close'].values
        high_prices = valid_hist['high'].values
        low_prices = valid_hist['low'].values

        for indicator in indicators:
            try:
                if indicator.upper() == 'MA':
                    result_data[sec][f'MA{period}'] = pd.Series(close_prices).rolling(window=period).mean().tolist()
                elif indicator.upper() == 'EMA':
                    result_data[sec][f'EMA{period}'] = pd.Series(close_prices).ewm(span=period, adjust=False).mean().tolist()
                elif indicator.upper() == 'MACD':
                    fast_period = kwargs.get('fast_period', 12)
                    slow_period = kwargs.get('slow_period', 26)
                    signal_period = kwargs.get('signal_period', 9)
                    ema_fast = pd.Series(close_prices).ewm(span=fast_period, adjust=False).mean()
                    ema_slow = pd.Series(close_prices).ewm(span=slow_period, adjust=False).mean()
                    dif = ema_fast - ema_slow
                    dea = dif.ewm(span=signal_period, adjust=False).mean()
                    result_data[sec]['MACD_DIF'] = dif.tolist()
                    result_data[sec]['MACD_DEA'] = dea.tolist()
                    result_data[sec]['MACD_HIST'] = ((dif - dea) * 2).tolist()
                elif indicator.upper() == 'RSI':
                    delta = pd.Series(close_prices).diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rs = gain / loss
                    result_data[sec][f'RSI{period}'] = (100 - (100 / (1 + rs))).tolist()
                elif indicator.upper() == 'BOLL':
                    std_multiplier = kwargs.get('std_multiplier', 2)
                    ma = pd.Series(close_prices).rolling(window=period).mean()
                    std = pd.Series(close_prices).rolling(window=period).std()
                    result_data[sec]['BOLL_UPPER'] = (ma + std_multiplier * std).tolist()
                    result_data[sec]['BOLL_MIDDLE'] = ma.tolist()
                    result_data[sec]['BOLL_LOWER'] = (ma - std_multiplier * std).tolist()
                elif indicator.upper() == 'KDJ':
                    k_period = kwargs.get('k_period', 9)
                    low_min = pd.Series(low_prices).rolling(window=k_period).min()
                    high_max = pd.Series(high_prices).rolling(window=k_period).max()
                    rsv = (pd.Series(close_prices) - low_min) / (high_max - low_min) * 100
                    k_values = rsv.ewm(com=2, adjust=False).mean()
                    d_values = k_values.ewm(com=2, adjust=False).mean()
                    j_values = 3 * k_values - 2 * d_values
                    result_data[sec]['KDJ_K'] = k_values.tolist()
                    result_data[sec]['KDJ_D'] = d_values.tolist()
                    result_data[sec]['KDJ_J'] = j_values.tolist()
            except Exception as e:
                log.warning(f"计算技术指标 {indicator} 时出错: {e}")

    if not result_data:
        return pd.DataFrame()

    sample_data = engine.data[securities[0]]
    current_dt = engine.context.current_dt if hasattr(engine, 'context') else None
    valid_hist = sample_data[sample_data.index <= current_dt] if current_dt else sample_data
    time_index = valid_hist.index

    result_df = pd.DataFrame()
    for sec in result_data:
        for indicator_name, values in result_data[sec].items():
            if len(values) == len(time_index):
                result_df[(indicator_name, sec)] = pd.Series(values, index=time_index)

    return result_df
