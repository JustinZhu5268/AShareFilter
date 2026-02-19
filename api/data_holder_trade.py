"""
股东增减持数据获取模块
功能：
1. 获取股东增减持公告 (stk_holdertrade)
2. 支持缓存机制
3. 提供增减持摘要统计
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


class HolderTradeClient:
    """股东增减持数据客户端"""

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

    def get_holder_trade(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取股东增减持公告

        Args:
            ts_code: 股票代码 (如 '300274.SZ')
            start_date: 开始日期 (如 '20250101')，默认最近90天
            end_date: 结束日期 (如 '20250218')，默认今天

        Returns:
            DataFrame with holder trade data
        """
        cache_key = f"holder_trade_{ts_code}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 默认日期范围：最近90天
        if end_date is None:
            end_date = datetime.datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y%m%d')

        # 尝试从批量缓存获取
        df_cache = self._load_holder_trade_cache()
        if df_cache is not None and not df_cache.empty:
            filtered = df_cache[df_cache['ts_code'] == ts_code]
            if not filtered.empty:
                # 按日期过滤
                if 'ann_date' in filtered.columns:
                    filtered = filtered[
                        (filtered['ann_date'] >= start_date) &
                        (filtered['ann_date'] <= end_date)
                    ]
                self._runtime_cache[cache_key] = filtered
                return filtered

        # 从API获取
        df = self._fetch_holder_trade(ts_code, start_date, end_date)

        if df is not None and not df.empty:
            self._runtime_cache[cache_key] = df
        else:
            df = pd.DataFrame()

        return df

    def get_holder_trade_summary(self, ts_code: str, days: int = 90) -> Dict[str, Any]:
        """
        获取增减持摘要统计

        Args:
            ts_code: 股票代码
            days: 统计天数

        Returns:
            {
                'total_increase': int,      # 增持次数
                'total_decrease': int,     # 减持次数
                'total_increase_amount': float,  # 增持总额(股)
                'total_decrease_amount': float,  # 减持总额(股)
                'net_change': float,        # 净变化
                'recent_increase': bool,    # 近期是否有增持
            }
        """
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')

        df = self.get_holder_trade(ts_code, start_date, end_date)

        if df is None or df.empty:
            return {
                'total_increase': 0,
                'total_decrease': 0,
                'total_increase_amount': 0.0,
                'total_decrease_amount': 0.0,
                'net_change': 0.0,
                'recent_increase': False,
            }

        # 统计增持和减持
        # holder_type: C=增持, D=减持
        increase_df = df[df.get('holder_type', '') == 'C'] if 'holder_type' in df.columns else pd.DataFrame()
        decrease_df = df[df.get('holder_type', '') == 'D'] if 'holder_type' in df.columns else pd.DataFrame()

        # 持有股份变化字段: holder_vol (持有股份变化)
        total_increase = len(increase_df)
        total_decrease = len(decrease_df)

        increase_amount = 0.0
        decrease_amount = 0.0
        if 'holder_vol' in df.columns:
            if not increase_df.empty:
                increase_amount = increase_df['holder_vol'].fillna(0).sum()
            if not decrease_df.empty:
                decrease_amount = decrease_df['holder_vol'].fillna(0).sum()

        # 近期是否有增持（最近30天内）
        recent_increase = False
        if not increase_df.empty and 'ann_date' in increase_df.columns:
            recent_30d = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')
            recent_increase = any(increase_df['ann_date'] >= recent_30d)

        return {
            'total_increase': total_increase,
            'total_decrease': total_decrease,
            'total_increase_amount': float(increase_amount),
            'total_decrease_amount': float(decrease_amount),
            'net_change': float(increase_amount - decrease_amount),
            'recent_increase': recent_increase,
        }

    def get_recent_increase(self, ts_code: str, days: int = 30) -> bool:
        """
        检查近期是否有增持

        Args:
            ts_code: 股票代码
            days: 检查天数

        Returns:
            True if recent increase found
        """
        summary = self.get_holder_trade_summary(ts_code, days)
        return summary['recent_increase']

    def _fetch_holder_trade(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """从API获取股东增减持数据"""
        if self.use_mock:
            return self._mock_client.stk_holdertrade(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

        try:
            # stk_holdertrade 接口字段说明:
            # ts_code, ann_date, holder_name, holder_type(C=增持,D=减持), holder_vol, holder_ratio, after_share, after_ratio
            return self._pro.stk_holdertrade(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,ann_date,holder_name,holder_type,holder_vol,holder_ratio,after_share,after_ratio'
            )
        except Exception as e:
            print(f"    ⚠️ 获取股东增减持失败 {ts_code}: {e}")
            return None

    def _load_holder_trade_cache(self) -> Optional[pd.DataFrame]:
        """加载股东增减持缓存"""
        return load_cache('holder_trade')

    def _save_holder_trade_cache(self, df: pd.DataFrame):
        """保存股东增减持缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'holder_trade.csv'


# 全局客户端实例
_holder_trade_client: Optional[HolderTradeClient] = None


def get_holder_trade_client(use_mock: bool = False) -> HolderTradeClient:
    """获取全局股东增减持客户端"""
    global _holder_trade_client
    if _holder_trade_client is None:
        _holder_trade_client = HolderTradeClient(use_mock=use_mock)
    return _holder_trade_client


def reset_holder_trade_client():
    """重置客户端"""
    global _holder_trade_client
    _holder_trade_client = None
