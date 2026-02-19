"""
股东人数数据获取模块
功能：
1. 获取股东人数数据 (stk_holdernumber)
2. 支持缓存机制
3. 提供股东人数变化趋势分析
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


class HolderNumberClient:
    """股东人数数据客户端"""

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

    def get_holder_number(self, ts_code: str) -> Dict[str, Any]:
        """
        获取最新股东人数

        Args:
            ts_code: 股票代码 (如 '300274.SZ')

        Returns:
            {
                'holder_num': int,          # 股东人数
                'end_date': str,             # 统计截止日期
                'change': int,              # 人数变化
                'change_ratio': float,      # 变化比例(%)
            }
        """
        cache_key = f"holder_num_{ts_code}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 从缓存获取
        df = self._load_holder_number_cache()

        if df is not None and not df.empty:
            filtered = df[df['ts_code'] == ts_code]
            if not filtered.empty:
                # 按日期排序，取最新数据
                filtered = filtered.sort_values('end_date', ascending=False)
                row = filtered.iloc[0]
                result = {
                    'holder_num': int(row.get('holder_num', 0)),
                    'end_date': str(row.get('end_date', '')),
                    'change': int(row.get('holder_num_change', 0)),
                    'change_ratio': float(row.get('holder_num_change_ratio', 0.0)),
                }
                self._runtime_cache[cache_key] = result
                return result

        # 从API获取
        df = self._fetch_holder_number(ts_code)

        if df is not None and not df.empty:
            # 按日期排序，取最新数据
            df = df.sort_values('end_date', ascending=False)
            row = df.iloc[0]
            result = {
                'holder_num': int(row.get('holder_num', 0)),
                'end_date': str(row.get('end_date', '')),
                'change': int(row.get('holder_num_change', 0)),
                'change_ratio': float(row.get('holder_num_change_ratio', 0.0)),
            }
        else:
            result = {
                'holder_num': 0,
                'end_date': '',
                'change': 0,
                'change_ratio': 0.0,
            }

        self._runtime_cache[cache_key] = result
        return result

    def get_holder_number_change(self, ts_code: str, periods: int = 4) -> Dict[str, Any]:
        """
        获取股东人数变化趋势

        Args:
            ts_code: 股票代码
            periods: 获取季度数，默认4个季度

        Returns:
            {
                'current_num': int,          # 当前人数
                'previous_num': int,         # 上期人数
                'change': int,               # 变化人数
                'change_ratio': float,       # 变化比例
                'trend': str,                # 趋势: 'increasing'(增加)/'decreasing'(减少)/'stable'(稳定)
                'quarters': list,            # 各季度数据列表
            }
        """
        cache_key = f"holder_num_trend_{ts_code}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 从API获取
        df = self._fetch_holder_number(ts_code)

        if df is None or df.empty:
            result = {
                'current_num': 0,
                'previous_num': 0,
                'change': 0,
                'change_ratio': 0.0,
                'trend': 'stable',
                'quarters': [],
            }
            self._runtime_cache[cache_key] = result
            return result

        # 按日期排序
        df = df.sort_values('end_date', ascending=False).head(periods)

        quarters = []
        for _, row in df.iterrows():
            quarters.append({
                'end_date': str(row.get('end_date', '')),
                'holder_num': int(row.get('holder_num', 0)),
                'change': int(row.get('holder_num_change', 0)),
                'change_ratio': float(row.get('holder_num_change_ratio', 0.0)),
            })

        # 计算趋势
        current_num = quarters[0]['holder_num'] if quarters else 0
        previous_num = quarters[1]['holder_num'] if len(quarters) > 1 else current_num
        change = current_num - previous_num
        change_ratio = (change / previous_num * 100) if previous_num > 0 else 0.0

        # 判断趋势
        if change_ratio > 5:
            trend = 'increasing'
        elif change_ratio < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'

        result = {
            'current_num': current_num,
            'previous_num': previous_num,
            'change': change,
            'change_ratio': change_ratio,
            'trend': trend,
            'quarters': quarters,
        }

        self._runtime_cache[cache_key] = result
        return result

    def is_holder_concentrated(self, ts_code: str, threshold: float = -10.0) -> bool:
        """
        判断股东人数是否集中（人数减少）

        Args:
            ts_code: 股票代码
            threshold: 变化比例阈值，默认-10%（即减少超过10%表示集中）

        Returns:
            True if holder number is decreasing significantly
        """
        trend_data = self.get_holder_number_change(ts_code)
        return trend_data['change_ratio'] < threshold

    def _fetch_holder_number(self, ts_code: str) -> Optional[pd.DataFrame]:
        """从API获取股东人数数据"""
        if self.use_mock:
            return self._mock_client.stk_holdernumber(ts_code)

        try:
            # stk_holdernumber 接口字段说明:
            # ts_code, end_date, holder_num, holder_num_change, holder_num_change_ratio
            return self._pro.stk_holdernumber(
                ts_code=ts_code,
                fields='ts_code,end_date,holder_num,holder_num_change,holder_num_change_ratio'
            )
        except Exception as e:
            print(f"    ⚠️ 获取股东人数失败 {ts_code}: {e}")
            return None

    def _load_holder_number_cache(self) -> Optional[pd.DataFrame]:
        """加载股东人数缓存"""
        return load_cache('holder_number')

    def _save_holder_number_cache(self, df: pd.DataFrame):
        """保存股东人数缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'holder_number.csv'


# 全局客户端实例
_holder_number_client: Optional[HolderNumberClient] = None


def get_holder_number_client(use_mock: bool = False) -> HolderNumberClient:
    """获取全局股东人数客户端"""
    global _holder_number_client
    if _holder_number_client is None:
        _holder_number_client = HolderNumberClient(use_mock=use_mock)
    return _holder_number_client


def reset_holder_number_client():
    """重置客户端"""
    global _holder_number_client
    _holder_number_client = None
