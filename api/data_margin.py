"""
融资融券数据获取模块
功能：
1. 获取融资融券数据 (margin)
2. 支持缓存机制
3. 提供融资余额分析
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, Optional, List

# 导入配置
from config import config

# 导入缓存管理
from data.cache_manager import (
    is_cache_valid, load_cache, save_cache,
)

# 导入Mock数据
from data.mock_data import MockTushareClient


class MarginClient:
    """融资融券数据客户端"""

    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        self._pro = None
        self._mock_client = MockTushareClient()

        # 运行时缓存
        self._runtime_cache: Dict[str, Any] = {}

        # 如果在config中设置了USE_MOCK_DATA
        if not self.use_mock and config.USE_MOCK_DATA:
            self.use_mock = True

    def _init_client(self):
        """初始化Tushare客户端"""
        if self.use_mock:
            return

        try:
            import tushare as ts
            ts.set_token(config.TUSHARE_TOKEN)
            self._pro = ts.pro_api(config.TUSHARE_TOKEN)
        except Exception as e:
            print(f"⚠️ Tushare初始化失败: {e}，使用Mock数据")
            self.use_mock = True

    def get_margin_data(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取融资融券数据

        Args:
            ts_code: 股票代码 (如 '300274.SZ')
            start_date: 开始日期，默认最近30天
            end_date: 结束日期，默认今天

        Returns:
            DataFrame with margin data
        """
        cache_key = f"margin_{ts_code}_{start_date}_{end_date}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 默认日期范围：最近30天
        if end_date is None:
            end_date = datetime.datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')

        # 从缓存获取
        df_cache = self._load_margin_cache()

        if df_cache is not None and not df_cache.empty:
            filtered = df_cache[df_cache['ts_code'] == ts_code]
            if 'trade_date' in filtered.columns:
                filtered = filtered[
                    (filtered['trade_date'] >= start_date) &
                    (filtered['trade_date'] <= end_date)
                ]
            self._runtime_cache[cache_key] = filtered
            return filtered

        # 从API获取
        df = self._fetch_margin(ts_code, start_date, end_date)

        if df is not None and not df.empty:
            self._runtime_cache[cache_key] = df
        else:
            df = pd.DataFrame()

        return df

    def get_margin_balance(self, ts_code: str) -> Dict[str, Any]:
        """
        获取融资余额

        Args:
            ts_code: 股票代码

        Returns:
            {
                'rzye': float,     # 融资余额(元)
                'rqye': float,     # 融券余额(元)
                'rzrqye': float,   # 融资融券余额(元)
                'rz_rate': float,  # 融资占比(%)
            }
        """
        df = self.get_margin_data(ts_code)

        if df is None or df.empty:
            return {
                'rzye': 0.0,
                'rqye': 0.0,
                'rzrqye': 0.0,
                'rz_rate': 0.0,
            }

        # 获取最新数据
        row = df.iloc[-1]

        rzye = float(row.get('rzye', 0))  # 融资余额
        rqye = float(row.get('rqye', 0))  # 融券余额
        rzrqye = rzye + rqye  # 融资融券余额

        # 融资占比
        rz_rate = (rzye / rzrqye * 100) if rzrqye > 0 else 0.0

        return {
            'rzye': rzye,
            'rqye': rqye,
            'rzrqye': rzrqye,
            'rz_rate': rz_rate,
        }

    def get_margin_trend(self, ts_code: str, days: int = 10) -> Dict[str, Any]:
        """
        获取融资趋势

        Args:
            ts_code: 股票代码
            days: 统计天数

        Returns:
            {
                'rz_change': float,     # 融资变化(元)
                'rz_change_pct': float, # 融资变化比例(%)
                'trend': str,           # 趋势: 'increasing', 'decreasing', 'stable'
            }
        """
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')

        df = self.get_margin_data(ts_code, start_date, end_date)

        if df is None or df.empty or len(df) < 2:
            return {
                'rz_change': 0.0,
                'rz_change_pct': 0.0,
                'trend': 'stable',
            }

        # 计算融资变化
        latest = df.iloc[-1]
        oldest = df.iloc[0]

        rz_change = float(latest.get('rzye', 0)) - float(oldest.get('rzye', 0))
        rz_change_pct = (rz_change / float(oldest.get('rzye', 1)) * 100) if float(oldest.get('rzye', 1)) > 0 else 0.0

        # 判断趋势
        if rz_change_pct > 10:
            trend = 'increasing'
        elif rz_change_pct < -10:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'rz_change': rz_change,
            'rz_change_pct': rz_change_pct,
            'trend': trend,
        }

    def is_margin_high(self, ts_code: str, threshold: float = 0.3) -> bool:
        """
        判断融资占比是否过高

        Args:
            ts_code: 股票代码
            threshold: 阈值，默认30%

        Returns:
            True if margin ratio is high
        """
        balance = self.get_margin_balance(ts_code)
        return balance['rz_rate'] / 100 > threshold

    def _fetch_margin(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """从API获取融资融券数据"""
        if self.use_mock:
            return self._mock_client.margin(ts_code, start_date, end_date)

        try:
            return self._pro.margin(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            print(f"    ⚠️ 获取融资融券数据失败: {e}")
            return None

    def _load_margin_cache(self) -> Optional[pd.DataFrame]:
        """加载融资融券缓存"""
        return load_cache('margin')

    def _save_margin_cache(self, df: pd.DataFrame):
        """保存融资融券缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'margin.csv'


# 全局客户端实例
_margin_client: Optional[MarginClient] = None


def get_margin_client(use_mock: bool = False) -> MarginClient:
    """获取全局融资融券客户端"""
    global _margin_client
    if _margin_client is None:
        _margin_client = MarginClient(use_mock=use_mock)
    return _margin_client


def reset_margin_client():
    """重置客户端"""
    global _margin_client
    _margin_client = None
