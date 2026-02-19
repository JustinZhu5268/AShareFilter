"""
周线数据获取模块
功能：
1. 获取周线行情数据
2. 日线数据转换为周线
3. 支持缓存机制
"""

import pandas as pd
import numpy as np
import datetime
from typing import Optional

# 导入配置
from config import config

# 导入缓存管理
from data.cache_manager import (
    is_cache_valid, load_cache, save_cache,
)


class WeeklyDataClient:
    """周线数据客户端"""

    def __init__(self):
        # 运行时缓存
        self._runtime_cache = {}

    def get_weekly_data(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取周线数据

        Args:
            ts_code: 股票代码 (如 '300274.SZ')
            start_date: 开始日期 (如 '20250101')
            end_date: 结束日期 (如 '20260218')

        Returns:
            周线DataFrame
        """
        cache_key = f"weekly_{ts_code}_{start_date}_{end_date}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 默认日期范围
        if end_date is None:
            end_date = datetime.datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y%m%d')

        # 尝试从缓存加载
        if is_cache_valid('weekly_data', 7):
            df_cache = self._load_weekly_cache(ts_code)
            if df_cache is not None and not df_cache.empty:
                # 过滤日期范围
                df_cache = df_cache[
                    (df_cache['trade_date'] >= start_date) &
                    (df_cache['trade_date'] <= end_date)
                ]
                self._runtime_cache[cache_key] = df_cache
                return df_cache

        # 从日线数据转换
        df_daily = self._get_daily_data(ts_code, start_date, end_date)

        if df_daily is None or df_daily.empty:
            return pd.DataFrame()

        # 转换为周线
        df_weekly = self._convert_to_weekly(df_daily)

        # 缓存
        self._save_weekly_cache(ts_code, df_weekly)
        self._runtime_cache[cache_key] = df_weekly

        return df_weekly

    def _get_daily_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据"""
        from api.tushare_client import get_client

        client = get_client(use_mock=True)
        return client.get_daily_data(ts_code, start_date, end_date)

    def _convert_to_weekly(self, df_daily: pd.DataFrame) -> pd.DataFrame:
        """
        将日线数据转换为周线数据

        Args:
            df_daily: 日线DataFrame

        Returns:
            周线DataFrame
        """
        if df_daily is None or df_daily.empty:
            return pd.DataFrame()

        df = df_daily.copy()

        # 确保trade_date是日期类型
        df['trade_date'] = pd.to_datetime(df['trade_date'])

        # 按周分组
        df['week'] = df['trade_date'].dt.to_period('W')

        # 按周聚合
        weekly = df.groupby('week').agg({
            'ts_code': 'first',
            'trade_date': 'last',  # 周最后一天
            'open': 'first',  # 周开盘价
            'high': 'max',    # 周最高价
            'low': 'min',     # 周最低价
            'close': 'last',  # 周收盘价
            'vol': 'sum',     # 周成交量
            'amount': 'sum',  # 周成交额
        }).reset_index(drop=True)

        # 格式化trade_date为字符串
        weekly['trade_date'] = weekly['trade_date'].dt.strftime('%Y%m%d')

        # 重新排列列顺序
        weekly = weekly[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']]

        return weekly

    def _load_weekly_cache(self, ts_code: str) -> Optional[pd.DataFrame]:
        """加载周线缓存"""
        cache_path = self._get_cache_path(ts_code)
        if cache_path.exists():
            return pd.read_csv(cache_path)
        return None

    def _save_weekly_cache(self, ts_code: str, df: pd.DataFrame):
        """保存周线缓存"""
        cache_path = self._get_cache_path(ts_code)
        df.to_csv(cache_path, index=False)

    def _get_cache_path(self, ts_code: str):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        # 去除.SZ/.SH后缀
        symbol = ts_code.replace('.SZ', '').replace('.SH', '')
        return cache_dir / f'weekly_{symbol}.csv'

    def get_weekly_data_with_adjustment(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取带复权的周线数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            复权后的周线DataFrame
        """
        from api.tushare_client import get_client

        client = get_client(use_mock=True)

        # 获取复权因子
        adj_factor = client.get_adj_factor(ts_code)

        # 获取周线数据
        df_weekly = self.get_weekly_data(ts_code, start_date, end_date)

        if df_weekly is None or df_weekly.empty:
            return df_weekly

        # 应用复权
        if adj_factor != 1.0:
            df_weekly = df_weekly.copy()
            df_weekly['open'] = df_weekly['open'] * adj_factor
            df_weekly['high'] = df_weekly['high'] * adj_factor
            df_weekly['low'] = df_weekly['low'] * adj_factor
            df_weekly['close'] = df_weekly['close'] * adj_factor

        return df_weekly


# 全局客户端实例
_weekly_client: Optional[WeeklyDataClient] = None


def get_weekly_client() -> WeeklyDataClient:
    """获取全局周线数据客户端"""
    global _weekly_client
    if _weekly_client is None:
        _weekly_client = WeeklyDataClient()
    return _weekly_client


def reset_weekly_client():
    """重置客户端"""
    global _weekly_client
    _weekly_client = None
