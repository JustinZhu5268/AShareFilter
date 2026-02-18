"""
技术指标计算模块
功能：
1. KDJ指标计算
2. MACD指标计算
3. 均线系统 (MA5/10/20/60)
4. 布林带计算
5. 底背离检测
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# 导入配置
from config import config


def calculate_kdj(df: pd.DataFrame, n: int = None) -> pd.DataFrame:
    """
    计算KDJ指标
    
    Args:
        df: 包含 high, low, close 列的DataFrame
        n: KDJ周期，默认使用配置值
    
    Returns:
        添加了 K, D, J 列的DataFrame
    """
    if n is None:
        n = config.KDJ_PERIOD
    
    if df is None or len(df) < n:
        return df
    
    df = df.copy()
    
    # 计算RSV
    low_min = df['low'].rolling(window=n, min_periods=1).min()
    high_max = df['high'].rolling(window=n, min_periods=1).max()
    
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)
    
    # 计算K, D, J
    df['K'] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/3, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    return df


def calculate_macd(df: pd.DataFrame, 
                   fast: int = None, 
                   slow: int = None, 
                   signal: int = None) -> pd.DataFrame:
    """
    计算MACD指标
    
    Args:
        df: 包含 close 列的DataFrame
        fast: 快线周期
        slow: 慢线周期  
        signal: 信号线周期
    
    Returns:
        添加了 macd, macd_signal, macd_hist 列的DataFrame
    """
    if fast is None:
        fast = config.MACD_FAST
    if slow is None:
        slow = config.MACD_SLOW
    if signal is None:
        signal = config.MACD_SIGNAL
    
    if df is None or len(df) < slow:
        return df
    
    df = df.copy()
    
    # 计算EMA
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    
    # DIF (MACD线)
    df['macd'] = ema_fast - ema_slow
    
    # DEA (信号线)
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    
    # MACD柱
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    return df


def calculate_ma(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
    """
    计算移动平均线
    
    Args:
        df: 包含 close 列的DataFrame
        periods: 均线周期列表
    
    Returns:
        添加了 ma5, ma10, ma20, ma60 等列的DataFrame
    """
    if periods is None:
        periods = [5, 10, 20, 60]
    
    if df is None or len(df) < max(periods):
        return df
    
    df = df.copy()
    
    for period in periods:
        df[f'ma{period}'] = df['close'].rolling(window=period).mean()
    
    return df


def calculate_bollinger_bands(df: pd.DataFrame, 
                              period: int = None, 
                              std_dev: float = None) -> pd.DataFrame:
    """
    计算布林带
    
    Args:
        df: 包含 close 列的DataFrame
        period: 布林带周期
        std_dev: 标准差倍数
    
    Returns:
        添加了 bb_upper, bb_middle, bb_lower 列的DataFrame
    """
    if period is None:
        period = config.BB_PERIOD
    if std_dev is None:
        std_dev = config.BB_STD
    
    if df is None or len(df) < period:
        return df
    
    df = df.copy()
    
    # 中轨
    df['bb_middle'] = df['close'].rolling(window=period).mean()
    
    # 标准差
    std = df['close'].rolling(window=period).std()
    
    # 上轨和下轨
    df['bb_upper'] = df['bb_middle'] + std_dev * std
    df['bb_lower'] = df['bb_middle'] - std_dev * std
    
    return df


def calculate_ema(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
    """
    计算指数移动平均线
    
    Args:
        df: 包含 close 列的DataFrame
        periods: EMA周期列表
    
    Returns:
        添加了 emaXX 列的DataFrame
    """
    if periods is None:
        periods = [12, 26]
    
    if df is None:
        return df
    
    df = df.copy()
    
    for period in periods:
        df[f'ema{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    
    return df


def check_kdj_golden_cross(df: pd.DataFrame) -> bool:
    """
    检查KDJ是否金叉 (K线上穿D线)
    
    Args:
        df: 包含 K, D 列的DataFrame
    
    Returns:
        True if golden cross occurred
    """
    if df is None or len(df) < 2:
        return False
    
    # 取最近两天的K和D
    k_current = df['K'].iloc[-1]
    d_current = df['D'].iloc[-1]
    k_prev = df['K'].iloc[-2]
    d_prev = df['D'].iloc[-2]
    
    # 金叉条件：昨天K<=D，今天K>D
    return k_prev <= d_prev and k_current > d_current


def check_kdj_dead_cross(df: pd.DataFrame) -> bool:
    """
    检查KDJ是否死叉 (K线下穿D线)
    """
    if df is None or len(df) < 2:
        return False
    
    k_current = df['K'].iloc[-1]
    d_current = df['D'].iloc[-1]
    k_prev = df['K'].iloc[-2]
    d_prev = df['D'].iloc[-2]
    
    # 死叉条件：昨天K>=D，今天K<D
    return k_prev >= d_prev and k_current < d_current


def check_macd_divergence(df: pd.DataFrame, lookback: int = 60) -> Dict[str, bool]:
    """
    检查MACD背离
    
    Args:
        df: 包含 close, macd_hist 列的DataFrame
        lookback: 回溯周期
    
    Returns:
        {'bullish': bool, 'bearish': bool}
    """
    if df is None or len(df) < lookback:
        return {'bullish': False, 'bearish': False}
    
    df = df.tail(lookback).copy()
    
    # 找最低价
    min_price_idx = df['close'].idxmin()
    min_price = df.loc[min_price_idx, 'close']
    min_macd = df.loc[min_price_idx, 'macd_hist']
    
    # 检查最近20天是否新低
    price_20_low = df['close'].iloc[:20].min()
    is_new_low = min_price <= price_20_low
    
    # 检查MACD是否未创新低 (底背离)
    macd_20_low = df['macd_hist'].iloc[:20].min()
    is_macd_higher = min_macd > macd_20_low
    
    bullish_divergence = is_new_low and is_macd_higher
    
    # 检查顶背离 (股价创新高，MACD未创新高)
    max_price_idx = df['close'].idxmax()
    max_price = df.loc[max_price_idx, 'close']
    max_macd = df.loc[max_price_idx, 'macd_hist']
    
    price_20_high = df['close'].iloc[:20].max()
    is_new_high = max_price >= price_20_high
    
    macd_20_high = df['macd_hist'].iloc[:20].max()
    is_macd_lower = max_macd < macd_20_high
    
    bearish_divergence = is_new_high and is_macd_lower
    
    return {
        'bullish': bullish_divergence,
        'bearish': bearish_divergence
    }


def calculate_ma_bias(df: pd.DataFrame, ma_period: int = None) -> float:
    """
    计算均线乖离率
    
    Args:
        df: 包含 close, ma{ma_period} 列的DataFrame
        ma_period: 均线周期
    
    Returns:
        乖离率 (百分比)
    """
    if ma_period is None:
        ma_period = config.MA_PERIOD
    
    if df is None or len(df) < ma_period:
        return 0.0
    
    latest = df.iloc[-1]
    close = latest['close']
    ma = latest.get(f'ma{ma_period}', df['close'].tail(ma_period).mean())
    
    if ma == 0:
        return 0.0
    
    return (close - ma) / ma * 100


def calculate_volume_ratio(df: pd.DataFrame, period: int = None) -> float:
    """
    计算量比
    
    Args:
        df: 包含 vol 列的DataFrame
        period: 成交量均线周期
    
    Returns:
        量比
    """
    if period is None:
        period = config.VOLUME_MA_PERIOD
    
    if df is None or len(df) < period:
        return 1.0
    
    latest = df.iloc[-1]
    current_vol = latest['vol']
    avg_vol = df['vol'].tail(period).mean()
    
    if avg_vol == 0:
        return 1.0
    
    return current_vol / avg_vol


def get_latest_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    获取最新的技术指标值
    
    Args:
        df: 包含所有技术指标的DataFrame
    
    Returns:
        包含最新指标值的字典
    """
    if df is None or df.empty:
        return {}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest
    
    return {
        'close': float(latest.get('close', 0)),
        'open': float(latest.get('open', 0)),
        'high': float(latest.get('high', 0)),
        'low': float(latest.get('low', 0)),
        'vol': float(latest.get('vol', 0)),
        
        # KDJ
        'K': float(latest.get('K', 50)),
        'D': float(latest.get('D', 50)),
        'J': float(latest.get('J', 50)),
        
        # MACD
        'macd': float(latest.get('macd', 0)),
        'macd_signal': float(latest.get('macd_signal', 0)),
        'macd_hist': float(latest.get('macd_hist', 0)),
        
        # 均线
        'ma5': float(latest.get('ma5', 0)),
        'ma10': float(latest.get('ma10', 0)),
        'ma20': float(latest.get('ma20', 0)),
        'ma60': float(latest.get('ma60', 0)),
        
        # 布林带
        'bb_upper': float(latest.get('bb_upper', 0)),
        'bb_middle': float(latest.get('bb_middle', 0)),
        'bb_lower': float(latest.get('bb_lower', 0)),
        
        # K线状态
        'kdj_golden_cross': check_kdj_golden_cross(df),
        'kdj_dead_cross': check_kdj_dead_cross(df),
        
        # MACD背离
        'macd_divergence': check_macd_divergence(df),
        
        # 乖离率
        'ma_bias': calculate_ma_bias(df),
        
        # 量比
        'volume_ratio': calculate_volume_ratio(df),
    }
