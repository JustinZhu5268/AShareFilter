"""
主营业务数据获取模块
功能：
1. 获取主营业务数据 (fina_mainbz)
2. 支持缓存机制
3. 提供主营业务关键词匹配功能
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


class MainBusinessClient:
    """主营业务数据客户端"""

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

    def get_main_business(self, ts_code: str) -> Dict[str, Any]:
        """
        获取主营业务描述

        Args:
            ts_code: 股票代码 (如 '300274.SZ')

        Returns:
            {
                'ts_code': str,
                'end_date': str,
                'businesses': list,  # 主营业务列表 [{'type': '1', 'bz_type': '类型', 'bz_item': '项目'}, ...]
                'main_business': str,  # 合并后的主营业务描述
            }
        """
        cache_key = f"main_business_{ts_code}"

        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        # 从缓存获取
        df = self._load_main_business_cache()

        if df is not None and not df.empty:
            filtered = df[df['ts_code'] == ts_code]
            if not filtered.empty:
                result = self._parse_main_business_df(filtered)
                self._runtime_cache[cache_key] = result
                return result

        # 从API获取
        df = self._fetch_main_business(ts_code)

        if df is not None and not df.empty:
            result = self._parse_main_business_df(df)
        else:
            result = {
                'ts_code': ts_code,
                'end_date': '',
                'businesses': [],
                'main_business': '',
            }

        self._runtime_cache[cache_key] = result
        return result

    def _parse_main_business_df(self, df: pd.DataFrame) -> Dict[str, Any]:
        """解析主营业务DataFrame"""
        # 按日期排序，取最新数据
        if 'end_date' in df.columns:
            df = df.sort_values('end_date', ascending=False)

        # 获取最新日期
        end_date = df.iloc[0]['end_date'] if not df.empty else ''

        # 提取业务列表
        businesses = []
        main_business_parts = []

        for _, row in df.iterrows():
            bz_item = row.get('bz_item', '')
            bz_type = row.get('bz_type', '')

            if bz_item:
                businesses.append({
                    'type': row.get('type', ''),
                    'bz_type': bz_type,
                    'bz_item': bz_item,
                })
                main_business_parts.append(bz_item)

        # 合并主营业务描述
        main_business = '；'.join(main_business_parts)

        return {
            'ts_code': df.iloc[0]['ts_code'] if not df.empty else '',
            'end_date': str(end_date),
            'businesses': businesses,
            'main_business': main_business,
        }

    def check_business_match(self, ts_code: str, keywords: List[str]) -> Dict[str, Any]:
        """
        检查主营业务是否匹配关键词

        Args:
            ts_code: 股票代码
            keywords: 关键词列表

        Returns:
            {
                'matched': bool,        # 是否匹配任一关键词
                'matched_keywords': list,  # 匹配的关键词列表
                'main_business': str,   # 主营业务描述
                'match_details': list,  # 匹配详情
            }
        """
        business_data = self.get_main_business(ts_code)
        main_business = business_data.get('main_business', '')

        matched_keywords = []
        match_details = []

        # 转换为小写进行匹配（不区分大小写）
        main_business_lower = main_business.lower()

        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in main_business_lower:
                matched_keywords.append(keyword)
                # 找到关键词在文本中的位置
                idx = main_business_lower.find(keyword_lower)
                # 提取关键词及其周围上下文
                start = max(0, idx - 20)
                end = min(len(main_business), idx + len(keyword) + 20)
                context = main_business[start:end]
                match_details.append({
                    'keyword': keyword,
                    'context': f"...{context}...",
                })

        return {
            'matched': len(matched_keywords) > 0,
            'matched_keywords': matched_keywords,
            'main_business': main_business,
            'match_details': match_details,
        }

    def is_pure_industry_leader(self, ts_code: str, industry_keywords: List[str]) -> bool:
        """
        判断是否为主营业务明确的行业龙头

        Args:
            ts_code: 股票代码
            industry_keywords: 行业关键词列表

        Returns:
            True if main business matches industry keywords
        """
        match_result = self.check_business_match(ts_code, industry_keywords)
        return match_result['matched']

    def _fetch_main_business(self, ts_code: str) -> Optional[pd.DataFrame]:
        """从API获取主营业务数据"""
        if self.use_mock:
            return self._mock_client.fina_mainbz(ts_code)

        try:
            # fina_mainbz 接口字段说明:
            # ts_code, end_date, type, bz_type, bz_item
            return self._pro.fina_mainbz(
                ts_code=ts_code,
                fields='ts_code,end_date,type,bz_type,bz_item'
            )
        except Exception as e:
            print(f"    ⚠️ 获取主营业务失败 {ts_code}: {e}")
            return None

    def _load_main_business_cache(self) -> Optional[pd.DataFrame]:
        """加载主营业务缓存"""
        return load_cache('main_business')

    def _save_main_business_cache(self, df: pd.DataFrame):
        """保存主营业务缓存"""
        cache_path = self._get_cache_path()
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')

    def _get_cache_path(self):
        """获取缓存路径"""
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent / 'data_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / 'main_business.csv'


# 全局客户端实例
_main_business_client: Optional[MainBusinessClient] = None


def get_main_business_client(use_mock: bool = False) -> MainBusinessClient:
    """获取全局主营业务客户端"""
    global _main_business_client
    if _main_business_client is None:
        _main_business_client = MainBusinessClient(use_mock=use_mock)
    return _main_business_client


def reset_main_business_client():
    """重置客户端"""
    global _main_business_client
    _main_business_client = None
