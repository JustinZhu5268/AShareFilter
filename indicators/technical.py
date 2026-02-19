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


# ==================== 支撑位共振判断 ====================

def check_support_at_ma60(df: pd.DataFrame, tolerance: float = 0.03) -> Dict[str, Any]:
    """
    检查价格是否回踩MA60均线获得支撑

    Args:
        df: 包含close和ma60的DataFrame
        tolerance: 容差范围（默认3%）

    Returns:
        {
            'at_ma60': bool,           # 是否在MA60附近
            'distance': float,          # 距离MA60的百分比
            'close': float,            # 当前收盘价
            'ma60': float,             # MA60值
        }
    """
    if df is None or df.empty:
        return {'at_ma60': False, 'distance': 0, 'close': 0, 'ma60': 0}

    if 'ma60' not in df.columns:
        df = calculate_ma(df, periods=[60])

    if len(df) < 60 or df['ma60'].isna().iloc[-1]:
        return {'at_ma60': False, 'distance': 0, 'close': 0, 'ma60': 0}

    close = float(df['close'].iloc[-1])
    ma60 = float(df['ma60'].iloc[-1])

    if ma60 == 0:
        return {'at_ma60': False, 'distance': 0, 'close': close, 'ma60': 0}

    distance = (close - ma60) / ma60
    at_ma60 = abs(distance) <= tolerance

    return {
        'at_ma60': at_ma60,
        'distance': distance,
        'close': close,
        'ma60': ma60,
    }


def check_support_at_bollinger(df: pd.DataFrame, tolerance: float = 0.03) -> Dict[str, Any]:
    """
    检查价格是否回踩布林下轨获得支撑
    """
    if df is None or df.empty:
        return {'at_bollinger': False, 'distance': 0, 'close': 0, 'bb_lower': 0}

    if 'bb_lower' not in df.columns:
        df = calculate_bollinger_bands(df)

    if len(df) < 20 or df['bb_lower'].isna().iloc[-1]:
        return {'at_bollinger': False, 'distance': 0, 'close': 0, 'bb_lower': 0}

    close = float(df['close'].iloc[-1])
    bb_lower = float(df['bb_lower'].iloc[-1])

    if bb_lower == 0:
        return {'at_bollinger': False, 'distance': 0, 'close': close, 'bb_lower': 0}

    distance = (close - bb_lower) / bb_lower
    at_bollinger = abs(distance) <= tolerance

    return {
        'at_bollinger': at_bollinger,
        'distance': distance,
        'close': close,
        'bb_lower': bb_lower,
    }


def check_support_resonance(df: pd.DataFrame,
                            ma60_tolerance: float = 0.03,
                            bollinger_tolerance: float = 0.03) -> Dict[str, Any]:
    """
    检查支撑位共振 - 价格同时接近MA60和布林下轨
    """
    if df is None or df.empty:
        return {
            'resonance': False,
            'at_ma60': False,
            'at_bollinger': False,
            'ma60_info': {},
            'bollinger_info': {},
            'support_level': 'none'
        }

    ma60_info = check_support_at_ma60(df, ma60_tolerance)
    bollinger_info = check_support_at_bollinger(df, bollinger_tolerance)

    resonance = ma60_info['at_ma60'] and bollinger_info['at_bollinger']

    if resonance:
        support_level = 'strong'
    elif ma60_info['at_ma60'] or bollinger_info['at_bollinger']:
        support_level = 'medium'
    else:
        support_level = 'none'

    return {
        'resonance': resonance,
        'at_ma60': ma60_info['at_ma60'],
        'at_bollinger': bollinger_info['at_bollinger'],
        'ma60_info': ma60_info,
        'bollinger_info': bollinger_info,
        'support_level': support_level
    }


def analyze_support_level(stock_data) -> Dict[str, Any]:
    """
    分析支撑位级别

    Args:
        stock_data: 包含技术指标数据的字典或DataFrame

    Returns:
        支撑位分析结果
    """
    # 支持字典或DataFrame输入
    if isinstance(stock_data, pd.DataFrame):
        df = stock_data
    else:
        # 重建DataFrame用于分析
        df = pd.DataFrame([stock_data])
    return check_support_resonance(df)


# ==================== 行业趋势判断 ====================

def check_industry_above_ma20(industry_df: pd.DataFrame) -> Dict[str, Any]:
    """
    检查行业指数是否站上20日均线

    Args:
        industry_df: 包含行业指数数据的DataFrame，需要有 close 列

    Returns:
        {
            'above_ma20': bool,        # 是否站上20日均线
            'close': float,            # 当前收盘价
            'ma20': float,             # 20日均线值
            'distance': float,         # 距离MA20的百分比
            'trend': str,              # 趋势: 'uptrend'/'downtrend'/'sideways'
        }
    """
    if industry_df is None or industry_df.empty:
        return {
            'above_ma20': False,
            'close': 0,
            'ma20': 0,
            'distance': 0,
            'trend': 'sideways'
        }

    if 'close' not in industry_df.columns:
        return {
            'above_ma20': False,
            'close': 0,
            'ma20': 0,
            'distance': 0,
            'trend': 'sideways'
        }

    if len(industry_df) < 20:
        return {
            'above_ma20': False,
            'close': float(industry_df['close'].iloc[-1]) if len(industry_df) > 0 else 0,
            'ma20': 0,
            'distance': 0,
            'trend': 'sideways'
        }

    ma20 = industry_df['close'].rolling(window=20).mean()
    close = industry_df['close'].iloc[-1]
    ma20_value = ma20.iloc[-1]

    if ma20_value == 0 or pd.isna(ma20_value):
        return {
            'above_ma20': False,
            'close': close,
            'ma20': 0,
            'distance': 0,
            'trend': 'sideways'
        }

    distance = (close - ma20_value) / ma20_value
    above_ma20 = close > ma20_value

    if len(industry_df) >= 40:
        recent_ma20 = ma20.iloc[-1]
        previous_ma20 = ma20.iloc[-20]

        if recent_ma20 > previous_ma20 * 1.02:
            trend = 'uptrend'
        elif recent_ma20 < previous_ma20 * 0.98:
            trend = 'downtrend'
        else:
            trend = 'sideways'
    else:
        trend = 'sideways'

    return {
        'above_ma20': above_ma20,
        'close': close,
        'ma20': ma20_value,
        'distance': distance,
        'trend': trend,
    }


def get_industry_trend(industry_df: pd.DataFrame, ma_periods: list = None) -> Dict[str, Any]:
    """
    获取行业趋势综合分析
    """
    if ma_periods is None:
        ma_periods = [5, 10, 20, 60]

    if industry_df is None or industry_df.empty or 'close' not in industry_df.columns:
        return {
            'trend': 'sideways',
            'above_ma20': False,
            'above_ma60': False,
            'ma_levels': {},
            'strength': 0
        }

    ma_values = {}
    for period in ma_periods:
        if len(industry_df) >= period:
            ma = industry_df['close'].rolling(window=period).mean()
            ma_values[f'ma{period}'] = ma.iloc[-1]

    close = industry_df['close'].iloc[-1]

    above_ma20 = ma_values.get('ma20', 0) and close > ma_values['ma20']
    above_ma60 = ma_values.get('ma60', 0) and close > ma_values['ma60']

    strength = 0
    if above_ma20:
        strength += 50
    if above_ma60:
        strength += 30
    if ma_values.get('ma20', 0) > ma_values.get('ma60', 0):
        strength += 20

    if strength >= 70:
        trend = 'uptrend'
    elif strength >= 40:
        trend = 'sideways'
    else:
        trend = 'downtrend'

    return {
        'trend': trend,
        'above_ma20': above_ma20,
        'above_ma60': above_ma60,
        'ma_levels': ma_values,
        'strength': strength,
        'close': close,
    }


def check_industry_momentum(industry_df: pd.DataFrame, periods: list = None) -> Dict[str, Any]:
    """
    检查行业动量 - 短期、中期、长期趋势
    """
    if periods is None:
        periods = [5, 20, 60]

    if industry_df is None or industry_df.empty:
        return {
            'short_term': 'sideways',
            'mid_term': 'sideways',
            'long_term': 'sideways',
            'momentum_score': 0
        }

    momentum = {}

    for period in periods:
        if len(industry_df) >= period:
            current_price = industry_df['close'].iloc[-1]
            past_price = industry_df['close'].iloc[-period]

            if past_price > 0:
                change_pct = (current_price - past_price) / past_price * 100

                if change_pct > 5:
                    momentum[f'{period}d'] = 'up'
                elif change_pct < -5:
                    momentum[f'{period}d'] = 'down'
                else:
                    momentum[f'{period}d'] = 'sideways'
            else:
                momentum[f'{period}d'] = 'sideways'
        else:
            momentum[f'{period}d'] = 'sideways'

    # 计算动量得分
    momentum_score = 0
    for period in periods:
        if momentum.get(f'{period}d') == 'up':
            if period == 5:
                momentum_score += 30
            elif period == 20:
                momentum_score += 40
            elif period == 60:
                momentum_score += 30

    return {
        'short_term': momentum.get('5d', 'sideways'),
        'mid_term': momentum.get('20d', 'sideways'),
        'long_term': momentum.get('60d', 'sideways'),
        'momentum_score': momentum_score
    }