"""
机构持仓数据获取模块
功能：
1. 获取机构持仓数据 (inst_holder)
2. 支持缓存机制
3. 提供机构持股比例分析
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


class InstHolderClient:
    """机构持仓数据客户端"""

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

    def get_inst_holder(self, ts_code: str) -> Dict[str, Any]:
        """
        获取机构持仓数据

        Args:
            ts_code: 股票代码 (如 '300274.SZ')

        Returns:
            {
                'holder_num': int,           # 机构数量
                'hold_ratio': float,         # 持股比例(%)
                'change_ratio': float,       # 持股比例变化(%)
                'end_date': str,             # 统计截止日期
                'institutions': list,         # 机构详情列表
            }
        """
        cache_key = f"inst_holder_{ts_code}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 从缓存获取
        df = self._load_inst_holder_cache()

        if df is not None and not df.empty:
            filtered = df[df['ts_code'] == ts_code]
            if not filtered.empty:
                # 按日期排序，取最新数据
                filtered = filtered.sort_values('end_date', ascending=False)
                row = filtered.iloc[0]
                result = {
                    'holder_num': int(row.get('holder_num', 0)),
                    'hold_ratio': float(row.get('hold_ratio', 0.0)),
                    'change_ratio': float(row.get('change_ratio', 0.0)),
                    'end_date': str(row.get('end_date', '')),
                    'institutions': self._parse_institutions(filtered),
                }
                self._runtime_cache[cache_key] = result
                return result

        # 从API获取
        df = self._fetch_inst_holder(ts_code)

        if df is not None and not df.empty:
            df = df.sort_values('end_date', ascending=False)
            row = df.iloc[0]
            result = {
                'holder_num': int(row.get('holder_num', 0)),
                'hold_ratio': float(row.get('hold_ratio', 0.0)),
                'change_ratio': float(row.get('change_ratio', 0.0)),
                'end_date': str(row.get('end_date', '')),
                'institutions': self._parse_institutions(df.head(10)),
            }
        else:
            result = {
                'holder_num': 0,
                'hold_ratio': 0.0,
                'change_ratio': 0.0,
                'end_date': '',
                'institutions': [],
            }

        self._runtime_cache[cache_key] = result
        return result

    def get_inst_holder_ratio(self, ts_code: str) -> float:
        """
        获取机构持股比例

        Args:
            ts_code: 股票代码

        Returns:
            机构持股比例 (%)
        """
        data = self.get_inst_holder(ts_code)
        return data.get('hold_ratio', 0.0)

    def is_institution_holding(self, ts_code: str, threshold: float = 5.0) -> bool:
        """
        判断机构持股是否超过阈值

        Args:
            ts_code: 股票代码
            threshold: 阈值，默认5%

        Returns:
            True if institution holding ratio exceeds threshold
        """
        ratio = self.get_inst_holder_ratio(ts_code)
        return ratio >= threshold

    def get_inst_holder_trend(self, ts_code: str, periods: int = 4) -> Dict[str, Any]:
        """
        获取机构持仓变化趋势

        Args:
            ts_code: 股票代码
            periods: 获取期数，默认4期

        Returns:
            {
                'current_ratio': float,       # 当前持股比例
                'previous_ratio': float,      # 上期持股比例
                'change': float,             # 变化比例
                'trend': str,                 # 趋势: 'increasing'(增加)/'decreasing'(减少)/'stable'(稳定)
                'periods': list,              # 各期数据列表
            }
        """
        cache_key = f"inst_holder_trend_{ts_code}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 从API获取
        df = self._fetch_inst_holder(ts_code)

        if df is None or df.empty:
            result = {
                'current_ratio': 0.0,
                'previous_ratio': 0.0,
                'change': 0.0,
                'trend': 'stable',
                'periods': [],
            }
            self._runtime_cache[cache_key] = result
            return result

        # 按日期排序
        df = df.sort_values('end_date', ascending=False).head(periods)

        periods_data = []
        for _, row in df.iterrows():
            periods_data.append({
                'end_date': str(row.get('end_date', '')),
                'holder_num': int(row.get('holder_num', 0)),
                'hold_ratio': float(row.get('hold_ratio', 0.0)),
                'change_ratio': float(row.get('change_ratio', 0.0)),
            })

        # 计算趋势
        current_ratio = periods_data[0]['hold_ratio'] if periods_data else 0.0
        previous_ratio = periods_data[1]['hold_ratio'] if len(periods_data) > 1 else current_ratio
        change = current_ratio - previous_ratio

        # 判断趋势
        if change > 1.0:
            trend = 'increasing'
        elif change < -1.0:
            trend = 'decreasing'
        else:
            trend = 'stable'

        result = {
            'current_ratio': current_ratio,
            'previous_ratio': previous_ratio,
            'change': change,
            'trend': trend,
            'periods': periods_data,
        }

        self._runtime_cache[cache_key] = result
        return result

    def _parse_institutions(self, df: pd.DataFrame) -> List[Dict]:
        """解析机构详情"""
        institutions = []
        for _, row in df.iterrows():
            institutions.append({
                'holder_name': str(row.get('holder_name', '')),
                'hold_ratio': float(row.get('hold_ratio', 0.0)),
                'change_ratio': float(row.get('change_ratio', 0.0)),
            })
        return institutions

    def _fetch_inst_holder(self, ts_code: str) -> Optional[pd.DataFrame]:
        """从API获取机构持仓数据"""
        if self.use_mock:
            return self._mock_client.inst_holder(ts_code)

        try:
            # inst_holder 接口字段说明:
            # ts_code, end_date, holder_name, holder_num, hold_ratio, change_ratio
            return self._pro.inst_holder(
                ts_code=ts_code,
                fields='ts_code,end_date,holder_name,holder_num,hold_ratio,change_ratio'
            )
        except Exception as e:
            print(f"    ⚠️ 获取机构持仓失败 {ts_code}: {e}")
            return None

    def _load_inst_holder_cache(self) -> Optional[pd.DataFrame]:
        """加载机构持仓缓存"""
        return load_cache('inst_holder')

    def _save_inst_holder_cache(self, df: pd.DataFrame):
        """保存机构持仓缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'inst_holder.csv'


# 全局客户端实例
_inst_holder_client: Optional[InstHolderClient] = None


def get_inst_holder_client(use_mock: bool = False) -> InstHolderClient:
    """获取全局机构持仓客户端"""
    global _inst_holder_client
    if _inst_holder_client is None:
        _inst_holder_client = InstHolderClient(use_mock=use_mock)
    return _inst_holder_client


def reset_inst_holder_client():
    """重置客户端"""
    global _inst_holder_client
    _inst_holder_client = None
