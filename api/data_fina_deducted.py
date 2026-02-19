"""
扣非净利润数据获取模块
功能：
1. 获取扣非净利润(TTM)数据
2. 批量获取全市场扣非净利润
3. 支持缓存机制
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, Optional

# 导入配置
from config import config

# 导入缓存管理
from data.cache_manager import (
    is_cache_valid, load_cache, save_cache,
)

# 导入Mock数据
from data.mock_data import MockTushareClient


class FinaDataClient:
    """扣非净利润数据客户端"""

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

    def get_deducted_net_profit(self, ts_code: str) -> Dict[str, Any]:
        """
        获取单只股票的扣非净利润

        Args:
            ts_code: 股票代码 (如 '300274.SZ')

        Returns:
            {'deducted_net_profit': float, 'report_date': str}
        """
        cache_key = f"deducted_{ts_code}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 尝试从批量缓存获取
        df_cache = self._load_deducted_profit_cache()
        if df_cache is not None:
            cached = df_cache[df_cache['ts_code'] == ts_code]
            if not cached.empty:
                row = cached.iloc[0]
                result = {
                    'deducted_net_profit': float(row.get('deducted_net_profit', 0)),
                    'report_date': str(row.get('end_date', '')),
                }
                self._runtime_cache[cache_key] = result
                return result

        # 从API获取
        df = self._fetch_deducted_profit(ts_code)

        if df is not None and not df.empty:
            # 按日期排序，取最新数据
            df = df.sort_values('end_date', ascending=False)
            latest = df.iloc[0]

            result = {
                'deducted_net_profit': float(latest.get('deducted_net_profit', 0) or 0),
                'report_date': str(latest.get('end_date', '')),
            }
        else:
            result = {
                'deducted_net_profit': 0.0,
                'report_date': '',
            }

        self._runtime_cache[cache_key] = result
        return result

    def get_all_deducted_profits(self, stock_list: Optional[list] = None) -> pd.DataFrame:
        """
        批量获取扣非净利润数据

        Args:
            stock_list: 股票代码列表，None时获取全部

        Returns:
            DataFrame with ts_code, deducted_net_profit, end_date
        """
        # 尝试从缓存加载
        if is_cache_valid('deducted_profit', 90):
            df = self._load_deducted_profit_cache()
            if df is not None:
                print(f"    -> 使用扣非净利润缓存: {len(df)} 条")
                if stock_list:
                    df = df[df['ts_code'].isin(stock_list)]
                return df

        if self.use_mock:
            df = self._generate_mock_deducted_profits()
            self._save_deducted_profit_cache(df)
            return df

        # 从API批量获取
        results = []

        if stock_list is None:
            # 需要先获取股票列表
            from api.tushare_client import get_client
            client = get_client(use_mock=self.use_mock)
            stocks = client.get_stock_list()
            if stocks is not None:
                stock_list = stocks['ts_code'].tolist()

        if stock_list is None:
            return pd.DataFrame()

        print(f"    批量获取扣非净利润: {len(stock_list)} 只...")

        for i, code in enumerate(stock_list):
            df = self._fetch_deducted_profit(code)
            if df is not None and not df.empty:
                df = df.sort_values('end_date', ascending=False)
                latest = df.iloc[0]
                results.append({
                    'ts_code': code,
                    'deducted_net_profit': float(latest.get('deducted_net_profit', 0) or 0),
                    'end_date': latest.get('end_date', ''),
                })

            if (i + 1) % 100 == 0:
                print(f"      进度: {i + 1}/{len(stock_list)}")

        if results:
            df_result = pd.DataFrame(results)
            self._save_deducted_profit_cache(df_result)
            print(f"    -> 获取扣非净利润: {len(df_result)} 条")
            return df_result

        return pd.DataFrame()

    def _fetch_deducted_profit(self, ts_code: str) -> Optional[pd.DataFrame]:
        """从API获取扣非净利润数据"""
        if self.use_mock:
            return self._mock_client.fina_indicator(
                ts_code=ts_code,
                fields='ts_code,end_date,deducted_net_profit'
            )

        try:
            return self._pro.fina_indicator(
                ts_code=ts_code,
                fields='ts_code,end_date,deducted_net_profit'
            )
        except Exception as e:
            print(f"    ⚠️ 获取扣非净利润失败 {ts_code}: {e}")
            return None

    def _load_deducted_profit_cache(self) -> Optional[pd.DataFrame]:
        """加载扣非净利润缓存"""
        return load_cache('deducted_profit')

    def _save_deducted_profit_cache(self, df: pd.DataFrame):
        """保存扣非净利润缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False)

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'deducted_profit.csv'

    def _generate_mock_deducted_profits(self) -> pd.DataFrame:
        """生成Mock扣非净利润数据"""
        # 复用现有的股票列表生成逻辑
        from data.mock_data import generate_mock_stock_list
        stocks = generate_mock_stock_list()

        data = []
        for _, stock in stocks.iterrows():
            ts_code = stock['ts_code']

            # 生成随机的扣非净利润（与ROE相关）
            np.random.seed(hash(ts_code) % 10000)
            deducted_np = np.random.uniform(1e7, 50e7)  # 1000万到50亿

            # 生成报告日期（最近几个季度）
            now = datetime.datetime.now()
            end_dates = [
                (now - datetime.timedelta(days=i*90)).strftime('%Y%m%d')
                for i in range(4)
            ]

            for end_date in end_dates:
                data.append({
                    'ts_code': ts_code,
                    'deducted_net_profit': deducted_np,
                    'end_date': end_date,
                })

        df = pd.DataFrame(data)
        print(f"    -> 生成Mock扣非净利润: {len(df)} 条")
        return df


# 全局客户端实例
_deducted_client: Optional[FinaDataClient] = None


def get_deducted_client(use_mock: bool = False) -> FinaDataClient:
    """获取全局扣非净利润客户端"""
    global _deducted_client
    if _deducted_client is None:
        _deducted_client = FinaDataClient(use_mock=use_mock)
    return _deducted_client


def reset_deducted_client():
    """重置客户端"""
    global _deducted_client
    _deducted_client = None
