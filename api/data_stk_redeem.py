"""
限售股解禁数据获取模块
功能：
1. 获取限售股解禁信息 (stk_redeem)
2. 支持缓存机制
3. 提供即将解禁股票查询
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


class StkRedeemClient:
    """限售股解禁数据客户端"""

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

    def get_redeem_info(self, ts_code: str) -> pd.DataFrame:
        """
        获取限售股解禁信息

        Args:
            ts_code: 股票代码 (如 '300274.SZ')

        Returns:
            DataFrame with redeem info
        """
        cache_key = f"stk_redeem_{ts_code}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 从缓存获取
        df_cache = self._load_redeem_cache()

        if df_cache is not None and not df_cache.empty:
            filtered = df_cache[df_cache['ts_code'] == ts_code]
            if not filtered.empty:
                self._runtime_cache[cache_key] = filtered
                return filtered

        # 从API获取
        df = self._fetch_redeem(ts_code)

        if df is not None and not df.empty:
            self._runtime_cache[cache_key] = df
        else:
            df = pd.DataFrame()

        return df

    def get_upcoming_redeem(self, ts_code: str = None, days: int = 90) -> pd.DataFrame:
        """
        获取即将解禁的股票

        Args:
            ts_code: 股票代码，None表示全部股票
            days: 检查未来天数

        Returns:
            DataFrame with upcoming redeem info
        """
        cache_key = f"upcoming_redeem_{ts_code}_{days}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 从缓存获取
        df_cache = self._load_redeem_cache()

        if df_cache is not None and not df_cache.empty:
            # 过滤
            filtered = df_cache

            if ts_code:
                filtered = filtered[filtered['ts_code'] == ts_code]

            # 未来解禁
            future_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y%m%d')
            today = datetime.datetime.now().strftime('%Y%m%d')

            if 'redeem_date' in filtered.columns:
                filtered = filtered[
                    (filtered['redeem_date'] >= today) &
                    (filtered['redeem_date'] <= future_date)
                ]

            filtered = filtered.sort_values('redeem_date')
            self._runtime_cache[cache_key] = filtered
            return filtered

        # 从API获取
        df = self._fetch_redeem(ts_code)

        if df is not None and not df.empty:
            # 过滤未来解禁
            future_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y%m%d')
            today = datetime.datetime.now().strftime('%Y%m%d')

            if 'redeem_date' in df.columns:
                df = df[
                    (df['redeem_date'] >= today) &
                    (df['redeem_date'] <= future_date)
                ]
                df = df.sort_values('redeem_date')

        self._runtime_cache[cache_key] = df
        return df

    def has_upcoming_redeem(self, ts_code: str, days: int = 30) -> bool:
        """
        检查是否有即将解禁的限售股

        Args:
            ts_code: 股票代码
            days: 检查未来天数

        Returns:
            True if has upcoming redeem
        """
        df = self.get_upcoming_redeem(ts_code, days)
        return df is not None and not df.empty

    def get_redeem_risk_level(self, ts_code: str, days: int = 90) -> str:
        """
        获取解禁风险等级

        Args:
            ts_code: 股票代码
            days: 检查未来天数

        Returns:
            'high': 高风险（有大量解禁）
            'medium': 中风险（有小量解禁）
            'low': 低风险（无解禁）
        """
        df = self.get_upcoming_redeem(ts_code, days)

        if df is None or df.empty:
            return 'low'

        # 计算总解禁量
        if 'redeem_vol' in df.columns:
            total_vol = df['redeem_vol'].sum()

            if total_vol > 50000000:  # > 5000万股
                return 'high'
            elif total_vol > 10000000:  # > 1000万股
                return 'medium'
            else:
                return 'low'

        return 'low'

    def _fetch_redeem(self, ts_code: str = None) -> Optional[pd.DataFrame]:
        """从API获取限售股解禁数据"""
        if self.use_mock:
            return self._mock_client.stk_redeem(ts_code)

        try:
            return self._pro.stk_redeem(
                ts_code=ts_code,
                fields='ts_code,redeem_date,redeem_vol,redeem_ratio'
            )
        except Exception as e:
            print(f"    ⚠️ 获取限售股解禁数据失败: {e}")
            return None

    def _load_redeem_cache(self) -> Optional[pd.DataFrame]:
        """加载限售股解禁缓存"""
        return load_cache('stk_redeem')

    def _save_redeem_cache(self, df: pd.DataFrame):
        """保存限售股解禁缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'stk_redeem.csv'


# 全局客户端实例
_stk_redeem_client: Optional[StkRedeemClient] = None


def get_stk_redeem_client(use_mock: bool = False) -> StkRedeemClient:
    """获取全局限售股解禁客户端"""
    global _stk_redeem_client
    if _stk_redeem_client is None:
        _stk_redeem_client = StkRedeemClient(use_mock=use_mock)
    return _stk_redeem_client


def reset_stk_redeem_client():
    """重置客户端"""
    global _stk_redeem_client
    _stk_redeem_client = None
