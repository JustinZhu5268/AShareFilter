"""
涨跌停数据获取模块
功能：
1. 获取涨跌停记录 (stk_limitlist)
2. 支持缓存机制
3. 判断当前股票是否涨停/跌停
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


class LimitListClient:
    """涨跌停数据客户端"""

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

    def get_limit_list(self, ts_code: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取涨跌停记录

        Args:
            ts_code: 股票代码 (如 '300274.SZ')，None表示全部股票
            start_date: 开始日期 (如 '20250101')，默认最近30天
            end_date: 结束日期 (如 '20250218')，默认今天

        Returns:
            DataFrame with limit list data
        """
        cache_key = f"limit_list_{ts_code}_{start_date}_{end_date}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 默认日期范围：最近30天
        if end_date is None:
            end_date = datetime.datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')

        # 从缓存获取
        df_cache = self._load_limit_list_cache()

        if df_cache is not None and not df_cache.empty:
            filtered = df_cache
            if ts_code:
                filtered = filtered[filtered['ts_code'] == ts_code]
            if 'trade_date' in filtered.columns:
                filtered = filtered[
                    (filtered['trade_date'] >= start_date) &
                    (filtered['trade_date'] <= end_date)
                ]
            self._runtime_cache[cache_key] = filtered
            return filtered

        # 从API获取
        df = self._fetch_limit_list(ts_code, start_date, end_date)

        if df is not None and not df.empty:
            self._runtime_cache[cache_key] = df
        else:
            df = pd.DataFrame()

        return df

    def is_limit_up(self, ts_code: str, trade_date: str = None) -> Dict[str, Any]:
        """
        判断是否涨停

        Args:
            ts_code: 股票代码
            trade_date: 交易日期，默认今天

        Returns:
            {
                'is_limit_up': bool,
                'limit_type': str,  # 'limit_up', 'limit_down', 'normal'
                'pct_chg': float,   # 涨跌幅
            }
        """
        if trade_date is None:
            trade_date = datetime.datetime.now().strftime('%Y%m%d')

        df = self.get_limit_list(ts_code, start_date=trade_date, end_date=trade_date)

        if df is None or df.empty:
            return {
                'is_limit_up': False,
                'limit_type': 'normal',
                'pct_chg': 0.0,
            }

        # 获取最新记录
        row = df.iloc[-1]

        # limit: U=涨停, D=跌停
        limit_type = str(row.get('limit', '')).upper()
        pct_chg = float(row.get('pct_chg', 0.0))

        return {
            'is_limit_up': limit_type == 'U',
            'limit_type': 'limit_up' if limit_type == 'U' else ('limit_down' if limit_type == 'D' else 'normal'),
            'pct_chg': pct_chg,
        }

    def is_limit_down(self, ts_code: str, trade_date: str = None) -> bool:
        """
        判断是否跌停

        Args:
            ts_code: 股票代码
            trade_date: 交易日期，默认今天

        Returns:
            True if limit down
        """
        result = self.is_limit_up(ts_code, trade_date)
        return result['limit_type'] == 'limit_down'

    def get_limit_stats(self, ts_code: str, days: int = 30) -> Dict[str, Any]:
        """
        获取涨停/跌停统计

        Args:
            ts_code: 股票代码
            days: 统计天数

        Returns:
            {
                'limit_up_count': int,   # 涨停次数
                'limit_down_count': int, # 跌停次数
                'total_limit': int,     # 总涨跌停次数
            }
        """
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')

        df = self.get_limit_list(ts_code, start_date, end_date)

        if df is None or df.empty:
            return {
                'limit_up_count': 0,
                'limit_down_count': 0,
                'total_limit': 0,
            }

        # 统计涨跌停
        limit_up_count = len(df[df['limit'] == 'U']) if 'limit' in df.columns else 0
        limit_down_count = len(df[df['limit'] == 'D']) if 'limit' in df.columns else 0

        return {
            'limit_up_count': int(limit_up_count),
            'limit_down_count': int(limit_down_count),
            'total_limit': int(limit_up_count + limit_down_count),
        }

    def is_locked_limit_up(self, ts_code: str, days: int = 10) -> bool:
        """
        判断是否涨停锁筹（连续涨停）

        Args:
            ts_code: 股票代码
            days: 检查天数

        Returns:
            True if locked limit up (连续涨停)
        """
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')

        df = self.get_limit_list(ts_code, start_date, end_date)

        if df is None or df.empty:
            return False

        # 检查是否连续涨停
        if 'limit' not in df.columns:
            return False

        # 按日期排序
        df = df.sort_values('trade_date', ascending=False)

        # 检查最近是否都是涨停
        limit_ups = df[df['limit'] == 'U']
        return len(limit_ups) >= 2

    def _fetch_limit_list(self, ts_code: Optional[str], start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """从API获取涨跌停数据"""
        if self.use_mock:
            return self._mock_client.stk_limitlist(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

        try:
            return self._pro.stk_limitlist(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,limit,pct_chg,open,high,low,close'
            )
        except Exception as e:
            print(f"    ⚠️ 获取涨跌停数据失败: {e}")
            return None

    def _load_limit_list_cache(self) -> Optional[pd.DataFrame]:
        """加载涨跌停缓存"""
        return load_cache('limit_list')

    def _save_limit_list_cache(self, df: pd.DataFrame):
        """保存涨跌停缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'limit_list.csv'


# 全局客户端实例
_limit_list_client: Optional[LimitListClient] = None


def get_limit_list_client(use_mock: bool = False) -> LimitListClient:
    """获取全局涨跌停客户端"""
    global _limit_list_client
    if _limit_list_client is None:
        _limit_list_client = LimitListClient(use_mock=use_mock)
    return _limit_list_client


def reset_limit_list_client():
    """重置客户端"""
    global _limit_list_client
    _limit_list_client = None
