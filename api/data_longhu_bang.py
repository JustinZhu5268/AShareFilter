"""
龙虎榜数据获取模块
功能：
1. 获取龙虎榜数据 (daily_hsgt)
2. 支持缓存机制
3. 提供龙虎榜上榜分析
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


class LongHuBangClient:
    """龙虎榜数据客户端"""

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

    def get_longhu_bang(self, ts_code: str, days: int = 60) -> Dict[str, Any]:
        """
        获取龙虎榜数据

        Args:
            ts_code: 股票代码 (如 '300274.SZ')
            days: 查询天数，默认60天

        Returns:
            {
                'total_count': int,          # 上榜总次数
                'buy_count': int,            # 买入次数
                'sell_count': int,           # 卖出次数
                'net_buy': float,            # 净买入(万元)
                'recent_trades': list,       # 最近交易列表
            }
        """
        cache_key = f"longhu_bang_{ts_code}_{days}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 从缓存获取
        df = self._load_longhu_bang_cache()

        if df is not None and not df.empty:
            # 过滤股票和时间
            end_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')

            filtered = df[(df['ts_code'] == ts_code) &
                         (df['trade_date'] >= start_date) &
                         (df['trade_date'] <= end_date)]

            if not filtered.empty:
                result = self._parse_longhu_data(filtered)
                self._runtime_cache[cache_key] = result
                return result

        # 从API获取
        df = self._fetch_longhu_bang(ts_code, days)

        if df is not None and not df.empty:
            result = self._parse_longhu_data(df)
        else:
            result = {
                'total_count': 0,
                'buy_count': 0,
                'sell_count': 0,
                'net_buy': 0.0,
                'recent_trades': [],
            }

        self._runtime_cache[cache_key] = result
        return result

    def get_longhu_count(self, ts_code: str, days: int = 60) -> int:
        """
        获取上榜次数

        Args:
            ts_code: 股票代码
            days: 查询天数

        Returns:
            上榜次数
        """
        data = self.get_longhu_bang(ts_code, days)
        return data.get('total_count', 0)

    def is_longhu_stock(self, ts_code: str, days: int = 30, min_count: int = 1) -> bool:
        """
        判断是否近期上过龙虎榜

        Args:
            ts_code: 股票代码
            days: 查询天数
            min_count: 最小上榜次数

        Returns:
            True if stock appeared on 龙虎榜
        """
        count = self.get_longhu_count(ts_code, days)
        return count >= min_count

    def get_longhu_heatmap(self, ts_codes: List[str], days: int = 60) -> pd.DataFrame:
        """
        获取多只股票的龙虎榜热度

        Args:
            ts_codes: 股票代码列表
            days: 查询天数

        Returns:
            包含上榜次数的DataFrame
        """
        results = []
        for ts_code in ts_codes:
            count = self.get_longhu_count(ts_code, days)
            results.append({
                'ts_code': ts_code,
                'longhu_count': count,
            })

        return pd.DataFrame(results).sort_values('longhu_count', ascending=False)

    def _parse_longhu_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """解析龙虎榜数据"""
        if df is None or df.empty:
            return {
                'total_count': 0,
                'buy_count': 0,
                'sell_count': 0,
                'net_buy': 0.0,
                'recent_trades': [],
            }

        # 计算买卖次数
        buy_count = len(df[df['buy'] > 0]) if 'buy' in df.columns else 0
        sell_count = len(df[df['sell'] > 0]) if 'sell' in df.columns else 0

        # 计算净买入
        net_buy = df['net_buy'].sum() if 'net_buy' in df.columns else 0.0

        # 获取最近交易
        recent_trades = []
        for _, row in df.head(10).iterrows():
            recent_trades.append({
                'trade_date': str(row.get('trade_date', '')),
                'buy': float(row.get('buy', 0)),
                'sell': float(row.get('sell', 0)),
                'net_buy': float(row.get('net_buy', 0)),
            })

        return {
            'total_count': len(df),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'net_buy': net_buy,
            'recent_trades': recent_trades,
        }

    def _fetch_longhu_bang(self, ts_code: str, days: int) -> Optional[pd.DataFrame]:
        """从API获取龙虎榜数据"""
        if self.use_mock:
            return self._mock_client.daily_hsgt(ts_code=ts_code, start_date=None, end_date=None)

        try:
            end_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')

            # daily_hsgt 接口字段说明:
            # ts_code, trade_date, buy, sell, net_buy
            return self._pro.daily_hsgt(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            print(f"    ⚠️ 获取龙虎榜失败 {ts_code}: {e}")
            return None

    def _load_longhu_bang_cache(self) -> Optional[pd.DataFrame]:
        """加载龙虎榜缓存"""
        return load_cache('longhu_bang')

    def _save_longhu_bang_cache(self, df: pd.DataFrame):
        """保存龙虎榜缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'longhu_bang.csv'


# 全局客户端实例
_longhu_bang_client: Optional[LongHuBangClient] = None


def get_longhu_bang_client(use_mock: bool = False) -> LongHuBangClient:
    """获取全局龙虎榜客户端"""
    global _longhu_bang_client
    if _longhu_bang_client is None:
        _longhu_bang_client = LongHuBangClient(use_mock=use_mock)
    return _longhu_bang_client


def reset_longhu_bang_client():
    """重置客户端"""
    global _longhu_bang_client
    _longhu_bang_client = None
