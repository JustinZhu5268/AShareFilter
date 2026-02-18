"""
筹码计算模块
功能：
1. VWAP筹码计算
2. 获利比例计算
3. 筹码集中度计算
4. 单峰密集判定
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

# 导入配置
from config import config


def calculate_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算VWAP (成交量加权平均价)
    
    Args:
        df: 包含 close, vol 列的DataFrame
    
    Returns:
        添加了 vwap 列的DataFrame
    """
    if df is None or 'close' not in df.columns or 'vol' not in df.columns:
        return df
    
    df = df.copy()
    
    # 计算VWAP
    # 累计(成交额) / 累计(成交量)
    df['vwap'] = (df['close'] * df['vol']).cumsum() / df['vol'].cumsum()
    
    return df


def calculate_vwap_chips(df: pd.DataFrame, lookback: int = 60) -> Dict[str, float]:
    """
    VWAP筹码计算
    
    Args:
        df: 包含 close, vol 列的DataFrame
        lookback: 回溯周期
    
    Returns:
        {
            'profit_ratio': 获利比例 (百分比),
            'concentration': 筹码集中度 (百分比),
            'single_peak': 是否单峰密集
        }
    """
    if df is None or len(df) < 30:
        return {
            'profit_ratio': 100.0,
            'concentration': 100.0,
            'single_peak': False
        }
    
    df = calculate_vwap(df)
    
    # 取最近lookback天
    recent = df.tail(lookback).copy()
    
    if recent.empty:
        return {
            'profit_ratio': 100.0,
            'concentration': 100.0,
            'single_peak': False
        }
    
    # 1. 计算获利比例 (基于VWAP)
    # 当前价格相对VWAP低点的涨幅
    low_vwap = recent['vwap'].min()
    current_vwap = recent['vwap'].iloc[-1]
    
    if low_vwap > 0:
        profit_ratio = (current_vwap - low_vwap) / low_vwap * 100
    else:
        profit_ratio = 100.0
    
    # 限制在0-100之间
    profit_ratio = max(0, min(100, profit_ratio))
    
    # 2. 计算筹码集中度
    # (VWAP高点 - VWAP低点) / 当前价格
    high_vwap = recent['vwap'].max()
    current_price = recent['close'].iloc[-1]
    
    if current_price > 0:
        concentration = (high_vwap - low_vwap) / current_price * 100
    else:
        concentration = 100.0
    
    # 3. 单峰密集判定
    # 峰值在现价下方15%内
    single_peak = False
    
    # 简单判定：如果大部分筹码在当前价格下方
    avg_price = recent['close'].mean()
    if current_price < avg_price * 1.15:
        # 价格在平均价格下方15%以内，可能形成单峰
        single_peak = True
    
    return {
        'profit_ratio': profit_ratio,
        'concentration': concentration,
        'single_peak': single_peak
    }


def calculate_cost_distribution(df: pd.DataFrame, bins: int = 20) -> Dict[str, Any]:
    """
    计算筹码成本分布
    
    Args:
        df: 包含 close, vol 列的DataFrame
        bins: 分箱数量
    
    Returns:
        筹码分布统计
    """
    if df is None or len(df) < 30:
        return {}
    
    df = calculate_vwap(df)
    recent = df.tail(60).copy()
    
    if recent.empty:
        return {}
    
    # 简单计算：基于价格区间的筹码分布
    prices = recent['close'].values
    volumes = recent['vol'].values
    
    # 价格区间
    min_price = prices.min()
    max_price = prices.max()
    
    if max_price == min_price:
        return {}
    
    # 分箱
    price_bins = np.linspace(min_price, max_price, bins + 1)
    volume_dist = np.zeros(bins)
    
    for i in range(len(prices)):
        for j in range(bins):
            if price_bins[j] <= prices[i] < price_bins[j + 1]:
                volume_dist[j] += volumes[i]
                break
    
    # 归一化
    total_vol = volume_dist.sum()
    if total_vol > 0:
        volume_dist = volume_dist / total_vol
    
    # 找到峰值区间
    peak_idx = np.argmax(volume_dist)
    peak_price = (price_bins[peak_idx] + price_bins[peak_idx + 1]) / 2
    peak_ratio = volume_dist[peak_idx]
    
    current_price = prices[-1]
    
    # 计算当前价格下方筹码比例
    below_current = 0
    for i in range(peak_idx):
        below_current += volume_dist[i]
    
    return {
        'peak_price': float(peak_price),
        'peak_ratio': float(peak_ratio),
        'current_price': float(current_price),
        'cost_below_current': float(below_current),
        'distribution': volume_dist.tolist()
    }


def check_single_peak(df: pd.DataFrame) -> bool:
    """
    判定是否单峰密集形态
    
    Args:
        df: 包含 close, vol 列的DataFrame
    
    Returns:
        True if single peak formation detected
    """
    cost_dist = calculate_cost_distribution(df)
    
    if not cost_dist:
        return False
    
    # 峰值在现价下方
    peak_price = cost_dist['peak_price']
    current_price = cost_dist['current_price']
    
    # 峰值在现价下方15%内
    if peak_price >= current_price * 0.85 and peak_price <= current_price:
        # 峰值集中度高
        if cost_dist['peak_ratio'] > 0.3:  # 峰值占比超过30%
            return True
    
    return False


def analyze_chips(stock_data: pd.DataFrame) -> Dict[str, Any]:
    """
    综合筹码分析
    
    Args:
        stock_data: 股票日线数据
    
    Returns:
        完整的筹码分析结果
    """
    # VWAP筹码
    vwap_chips = calculate_vwap_chips(stock_data)
    
    # 成本分布
    cost_dist = calculate_cost_distribution(stock_data)
    
    # 单峰密集
    single_peak = check_single_peak(stock_data)
    
    return {
        'profit_ratio': vwap_chips['profit_ratio'],  # 获利比例
        'concentration': vwap_chips['concentration'],  # 集中度
        'single_peak': single_peak,  # 单峰密集
        'cost_distribution': cost_dist,
        
        # 判定结果
        'chips_qualified': (
            vwap_chips['profit_ratio'] <= config.MAX_PROFIT_RATIO and
            vwap_chips['concentration'] <= config.MAX_CHIP_CONCENTRATION
        )
    }
