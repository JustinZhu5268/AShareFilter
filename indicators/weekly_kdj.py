"""
周线KDJ指标计算模块
功能：
1. 计算周线KDJ指标
2. 检测周线J值是否在未超买区域(J<50)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# 导入配置
from config import config


def calculate_weekly_kdj(df: pd.DataFrame, n: int = None) -> pd.DataFrame:
    """
    计算周线KDJ指标

    Args:
        df: 包含 high, low, close 列的周线DataFrame
        n: KDJ周期，默认使用配置值

    Returns:
        添加了 K, D, J 列的DataFrame
    """
    if n is None:
        n = config.WEEKLY_KDJ_PERIOD

    if df is None or len(df) < n:
        return df

    df = df.copy()

    # 计算RSV
    low_min = df['low'].rolling(window=n, min_periods=1).min()
    high_max = df['high'].rolling(window=n, min_periods=1).max()

    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)

    # 计算K, D, J (使用EMA方式，与日线一致)
    df['K'] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/3, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']

    return df


def check_weekly_kdj_oversold(df: pd.DataFrame, threshold: float = None) -> bool:
    """
    检查周线KDJ是否处于未超买区域 (J < 阈值)

    Args:
        df: 包含 J 列的周线DataFrame
        threshold: J值阈值，默认使用配置值

    Returns:
        True if J < threshold (未超买)
    """
    if threshold is None:
        threshold = config.WEEKLY_KDJ_THRESHOLD

    if df is None or len(df) < 1:
        return False

    # 取最新的J值
    j_value = df['J'].iloc[-1]

    # 如果J值为NaN，返回False
    if pd.isna(j_value):
        return False

    return j_value < threshold


def check_weekly_kdj_oversold_detailed(df: pd.DataFrame, threshold: float = None) -> Dict[str, Any]:
    """
    检查周线KDJ详细状态

    Args:
        df: 包含 K, D, J 列的周线DataFrame
        threshold: J值阈值

    Returns:
        包含J值和是否未超买的字典
    """
    if threshold is None:
        threshold = config.WEEKLY_KDJ_THRESHOLD

    if df is None or len(df) < 1:
        return {
            'j_value': None,
            'k_value': None,
            'd_value': None,
            'is_oversold': False,
            'status': '数据不足'
        }

    latest = df.iloc[-1]
    j_value = latest.get('J', 50)
    k_value = latest.get('K', 50)
    d_value = latest.get('D', 50)

    # 处理NaN
    if pd.isna(j_value):
        j_value = 50
    if pd.isna(k_value):
        k_value = 50
    if pd.isna(d_value):
        d_value = 50

    is_oversold = j_value < threshold

    # 状态描述
    if j_value < 20:
        status = '超卖区域'
    elif j_value < threshold:
        status = '未超买'
    elif j_value < 80:
        status = '正常区域'
    else:
        status = '超买区域'

    return {
        'j_value': float(j_value),
        'k_value': float(k_value),
        'd_value': float(d_value),
        'is_oversold': is_oversold,
        'status': status,
        'threshold': threshold
    }


def get_weekly_kdj_signal(df: pd.DataFrame, threshold: float = None) -> str:
    """
    获取周线KDJ信号

    Args:
        df: 包含 K, D, J 列的周线DataFrame
        threshold: J值阈值

    Returns:
        信号描述字符串
    """
    if threshold is None:
        threshold = config.WEEKLY_KDJ_THRESHOLD

    if df is None or len(df) < 2:
        return '数据不足'

    # 获取最近两天的K和D
    k_current = df['K'].iloc[-1]
    d_current = df['D'].iloc[-1]
    k_prev = df['K'].iloc[-2]
    d_prev = df['D'].iloc[-2]

    # J值
    j_value = df['J'].iloc[-1]

    # 检查金叉/死叉
    golden_cross = k_prev <= d_prev and k_current > d_current
    dead_cross = k_prev >= d_prev and k_current < d_current

    # 未超买检查
    is_oversold = j_value < threshold if not pd.isna(j_value) else False

    # 信号描述
    if golden_cross and is_oversold:
        return '周线金叉+未超买'
    elif golden_cross:
        return '周线金叉'
    elif dead_cross:
        return '周线死叉'
    elif is_oversold:
        return '周线未超买'
    else:
        return '周线正常'


def analyze_weekly_tech(df: pd.DataFrame, threshold: float = None) -> Dict[str, Any]:
    """
    综合分析周线技术指标

    Args:
        df: 包含周线OHLCV数据的DataFrame
        threshold: J值阈值

    Returns:
        完整的周线技术分析结果
    """
    if df is None or len(df) < config.WEEKLY_KDJ_PERIOD:
        return {
            'has_data': False,
            'error': '数据不足'
        }

    # 计算KDJ
    df_kdj = calculate_weekly_kdj(df, config.WEEKLY_KDJ_PERIOD)

    # 获取详细状态
    kdj_detail = check_weekly_kdj_oversold_detailed(df_kdj, threshold)

    # 获取信号
    signal = get_weekly_kdj_signal(df_kdj, threshold)

    # 计算周线均线
    df_ma = calculate_weekly_ma(df_kdj, [5, 10, 20])

    # 获取最新均线值
    latest = df_ma.iloc[-1] if len(df_ma) > 0 else None

    # 周线趋势判断
    if latest is not None:
        ma5 = latest.get('ma5', 0)
        ma10 = latest.get('ma10', 0)
        ma20 = latest.get('ma20', 0)
        close = latest.get('close', 0)

        # 多头排列判断
        if ma5 > ma10 > ma20 and close > ma5:
            trend = '周线多头'
        elif ma5 < ma10 < ma20 and close < ma5:
            trend = '周线空头'
        else:
            trend = '周线震荡'
    else:
        trend = '数据不足'

    return {
        'has_data': True,
        'kdj': kdj_detail,
        'signal': signal,
        'trend': trend,
        'ma5': float(latest.get('ma5', 0)) if latest is not None else None,
        'ma10': float(latest.get('ma10', 0)) if latest is not None else None,
        'ma20': float(latest.get('ma20', 0)) if latest is not None else None,
    }


def calculate_weekly_ma(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
    """
    计算周线均线

    Args:
        df: 包含 close 列的周线DataFrame
        periods: 均线周期列表

    Returns:
        添加了 ma{period} 列的DataFrame
    """
    if periods is None:
        periods = [5, 10, 20]

    if df is None or len(df) < max(periods):
        return df

    df = df.copy()

    for period in periods:
        df[f'ma{period}'] = df['close'].rolling(window=period).mean()

    return df
