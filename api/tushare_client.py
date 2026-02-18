"""
Tushare API 客户端
功能：
1. 统一的API调用接口
2. 自动重试机制
3. 错误处理和日志记录
4. 支持Mock数据模式
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
import datetime
import time
import warnings
from typing import Dict, Any, Optional

# 导入配置
from config import config

# 导入缓存
from data.cache_manager import (
    is_cache_valid, load_cache, save_cache,
    load_market_cap_cache, save_market_cap_cache,
    load_financial_ttm_cache, save_financial_ttm_cache,
    load_stock_list_cache, save_stock_list_cache,
    load_adj_factor_cache, save_adj_factor_cache,
    load_industry_rps_cache, save_industry_rps_cache,
    load_daily_cache, save_daily_cache,
)

# 导入Mock数据
from data.mock_data import (
    MockTushareClient,
    generate_mock_stock_list,
    generate_mock_market_cap,
    generate_mock_financial_ttm,
    generate_mock_adj_factor,
    generate_mock_daily_data,
    generate_mock_industry_rps,
    generate_mock_northbound_funds,
    generate_mock_main_funds,
)

warnings.filterwarnings('ignore')


class TushareClient:
    """Tushare API 客户端"""
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock or config.USE_MOCK_DATA
        self._pro = None
        self._init_client()
        
        # 运行时缓存
        self._runtime_cache: Dict[str, Any] = {}
    
    def _init_client(self):
        """初始化客户端"""
        if self.use_mock:
            print("🔧 使用 Mock 数据模式")
            self._mock_client = MockTushareClient()
            return
        
        # 真实API初始化
        try:
            import tushare as ts
            ts.set_token(config.TUSHARE_TOKEN)
            self._pro = ts.pro_api(config.TUSHARE_TOKEN)
            self._pro._DataApi__http_url = config.TUSHARE_API_URL
            print("✅ Tushare API 初始化成功")
        except Exception as e:
            print(f"⚠️ Tushare API 初始化失败: {e}")
            print("🔧 自动切换到 Mock 数据模式")
            self.use_mock = True
            self._mock_client = MockTushareClient()
    
    def _call_with_retry(self, func, *args, **kwargs) -> Any:
        """带重试的API调用"""
        if self.use_mock:
            return func(*args, **kwargs)
        
        for attempt in range(config.API_RETRY_TIMES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < config.API_RETRY_TIMES - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"    ⚠️ API调用失败，{wait_time}秒后重试... ({attempt + 1}/{config.API_RETRY_TIMES})")
                    time.sleep(wait_time)
                else:
                    print(f"    ❌ API调用失败: {e}")
                    return None
        return None
    
    # ==========================================
    # 股票列表相关
    # ==========================================
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表 - 带缓存"""
        # 尝试从缓存加载
        if is_cache_valid('stock_list', 1):
            df = load_stock_list_cache()
            if df is not None and not df.empty:
                print(f"    -> 使用股票列表缓存: {len(df)} 只")
                return df
        
        # 从API获取
        def _fetch():
            if self.use_mock:
                return self._mock_client.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name,industry,list_date,list_status'
                )
            return self._call_with_retry(
                self._pro.stock_basic,
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,industry,list_date,list_status'
            )
        
        df = _fetch()
        
        if df is not None and not df.empty:
            save_stock_list_cache(df)
            print(f"    -> API获取股票列表: {len(df)} 只")
        
        return df
    
    # ==========================================
    # 市值相关
    # ==========================================
    
    def get_market_cap(self, ts_code: str) -> float:
        """
        获取单只股票市值 (亿元)
        """
        cache_key = f"mv_{ts_code}"
        
        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]
        
        # 尝试从缓存批量获取
        df_cache = load_market_cap_cache()
        if df_cache is not None:
            cached = df_cache[df_cache['ts_code'] == ts_code]
            if not cached.empty:
                # Tushare返回千元，除以100000得到亿元
                mv = float(cached.iloc[0]['total_mv']) / 100000
                self._runtime_cache[cache_key] = mv
                return mv
        
        # 从API获取
        def _fetch():
            if self.use_mock:
                return self._mock_client.daily_basic(ts_code=ts_code, fields='total_mv')
            return self._call_with_retry(
                self._pro.daily_basic,
                ts_code=ts_code,
                fields='total_mv'
            )
        
        df = _fetch()
        if df is not None and not df.empty:
            # 注意：API返回所有历史数据，需要取最新的一条
            # 按trade_date排序后取最后一行
            if 'trade_date' in df.columns:
                df = df.sort_values('trade_date', ascending=False)
            # Tushare返回千元，除以100000得到亿元
            mv = float(df.iloc[0]['total_mv']) / 100000
            self._runtime_cache[cache_key] = mv
            return mv
        
        return 0.0
    
    def get_all_market_caps(self) -> pd.DataFrame:
        """批量获取所有股票市值"""
        # 尝试从缓存加载
        if is_cache_valid('market_cap', 7):
            df = load_market_cap_cache()
            if df is not None:
                print(f"    -> 使用市值缓存: {len(df)} 条")
                return df
        
        if self.use_mock:
            df = generate_mock_market_cap()
            save_market_cap_cache(df)
            return df
        
        # 从API批量获取
        stocks = self.get_stock_list()
        if stocks is None:
            return None
        
        market_caps = []
        codes = stocks['ts_code'].tolist()
        
        print(f"    批量获取市值: {len(codes)} 只...")
        
        for i in range(0, len(codes), 100):
            batch = codes[i:i+100]
            def _fetch_batch():
                return self._pro.daily_basic(
                    ts_code=','.join(batch),
                    fields='ts_code,total_mv'
                )
            
            df = self._call_with_retry(_fetch_batch)
            if df is not None and not df.empty:
                market_caps.append(df)
            
            if (i // 100) % 5 == 0:
                print(f"      进度: {min(i + 100, len(codes))}/{len(codes)}")
        
        if market_caps:
            df_result = pd.concat(market_caps, ignore_index=True)
            save_market_cap_cache(df_result)
            print(f"    -> 获取市值: {len(df_result)} 条")
            return df_result
        
        return None
    
    # ==========================================
    # 财务数据相关
    # ==========================================
    
    def get_financial_ttm(self, ts_code: str) -> Dict[str, Any]:
        """
        获取TTM财务数据
        返回: {'roe_ttm': float, 'net_profit_ttm': float, 'revenue_ttm': float}
        """
        cache_key = f"fin_{ts_code}"
        
        # 检查运行时缓存
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]
        
        # 尝试从缓存批量获取
        df_cache = load_financial_ttm_cache()
        if df_cache is not None:
            cached = df_cache[df_cache['ts_code'] == ts_code]
            if not cached.empty:
                row = cached.iloc[0]
                result = {
                    'roe_ttm': float(row.get('roe', 0)),
                    'net_profit_ttm': float(row.get('net_profit', 0)),
                    'revenue_ttm': float(row.get('revenue', 0)),
                }
                self._runtime_cache[cache_key] = result
                return result
        
        # 从API获取
        def _fetch():
            if self.use_mock:
                return self._mock_client.fina_indicator(
                    ts_code=ts_code,
                    fields='ts_code,report_date,roe,net_profit,revenue'
                )
            return self._pro.fina_indicator(
                ts_code=ts_code,
                fields='ts_code,report_date,roe,net_profit,revenue'
            )
        
        df = self._call_with_retry(_fetch)
        
        if df is not None and not df.empty:
            # 按日期排序，取最新数据
            date_col = 'report_date'
            if date_col in df.columns:
                df = df.sort_values(date_col, ascending=False)
            
            latest = df.iloc[0]
            result = {
                'roe_ttm': float(latest.get('roe', 0) or 0),
                'net_profit_ttm': float(latest.get('net_profit', 0) or 0),
                'revenue_ttm': float(latest.get('revenue', 0) or 0),
            }
            self._runtime_cache[cache_key] = result
            return result
        
        # 返回默认值
        result = {
            'roe_ttm': 0.0,
            'net_profit_ttm': 0.0,
            'revenue_ttm': 0.0,
        }
        self._runtime_cache[cache_key] = result
        return result
    
    def get_all_financial_ttm(self) -> pd.DataFrame:
        """批量获取所有股票财务数据"""
        # 尝试从缓存加载
        if is_cache_valid('financial_ttm', 90):
            df = load_financial_ttm_cache()
            if df is not None:
                print(f"    -> 使用财务TTM缓存: {len(df)} 条")
                return df
        
        if self.use_mock:
            df = generate_mock_financial_ttm()
            save_financial_ttm_cache(df)
            return df
        
        stocks = self.get_stock_list()
        if stocks is None:
            return None
        
        financial_data = []
        codes = stocks['ts_code'].tolist()
        
        print(f"    批量获取财务数据: {len(codes)} 只...")
        
        for i, code in enumerate(codes):
            def _fetch():
                if self.use_mock:
                    return self._mock_client.fina_indicator(
                        ts_code=code,
                        fields='ts_code,report_date,roe,net_profit,revenue'
                    )
                return self._pro.fina_indicator(
                    ts_code=code,
                    fields='ts_code,report_date,roe,net_profit,revenue'
                )
            
            df = self._call_with_retry(_fetch)
            if df is not None and not df.empty:
                df = df.sort_values('report_date', ascending=False)
                financial_data.append(df.iloc[0])
            
            if (i + 1) % 100 == 0:
                print(f"      进度: {i + 1}/{len(codes)}")
        
        if financial_data:
            df_result = pd.concat(financial_data, ignore_index=True)
            save_financial_ttm_cache(df_result)
            print(f"    -> 获取财务数据: {len(df_result)} 条")
            return df_result
        
        return None
    
    # ==========================================
    # 复权因子相关
    # ==========================================
    
    def get_adj_factor(self, ts_code: str) -> float:
        """获取复权因子"""
        cache_key = f"adj_{ts_code}"
        
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]
        
        # 尝试从缓存批量获取
        df_cache = load_adj_factor_cache()
        if df_cache is not None:
            cached = df_cache[df_cache['ts_code'] == ts_code]
            if not cached.empty:
                factor = float(cached.iloc[0]['adj_factor'])
                self._runtime_cache[cache_key] = factor
                return factor
        
        # 从API获取
        def _fetch():
            if self.use_mock:
                return self._mock_client.adj_factor(ts_code=ts_code)
            return self._pro.adj_factor(ts_code=ts_code)
        
        df = self._call_with_retry(_fetch)
        if df is not None and not df.empty:
            factor = float(df.iloc[-1]['adj_factor'])
            self._runtime_cache[cache_key] = factor
            return factor
        
        self._runtime_cache[cache_key] = 1.0
        return 1.0
    
    # ==========================================
    # 日线数据相关
    # ==========================================
    
    def get_daily_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取日线数据 - 带缓存
        
        Args:
            ts_code: 股票代码 (如 '300274.SZ')
            start_date: 开始日期 (如 '20250101')
            end_date: 结束日期 (如 '20260218')
        
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"daily_{ts_code}_{start_date}_{end_date}"
        
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]
        
        # 尝试从缓存加载
        df_cache = load_daily_cache(ts_code)
        if df_cache is not None and not df_cache.empty:
            # 简单检查日期范围
            if 'trade_date' in df_cache.columns:
                # 转换日期格式
                if df_cache['trade_date'].dtype != object:
                    df_cache['trade_date'] = df_cache['trade_date'].astype(str)
                df_cache = df_cache[
                    (df_cache['trade_date'] >= start_date) & 
                    (df_cache['trade_date'] <= end_date)
                ]
                # 如果缓存数据足够，直接返回
                if len(df_cache) >= 60:
                    self._runtime_cache[cache_key] = df_cache
                    return df_cache
        
        # 缓存数据不足，从API获取
        if self.use_mock:
            days = (datetime.datetime.strptime(end_date, '%Y%m%d') - 
                    datetime.datetime.strptime(start_date, '%Y%m%d')).days
            df = generate_mock_daily_data(ts_code, min(days, 120))
            save_daily_cache(ts_code, df)
            self._runtime_cache[cache_key] = df
            return df
        
        def _fetch():
            return self._pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
        
        df = self._call_with_retry(_fetch)
        if df is not None and not df.empty:
            self._runtime_cache[cache_key] = df
            # 缓存全部数据
            save_daily_cache(ts_code, df)
        else:
            df = pd.DataFrame()
        
        return df
    
    # ==========================================
    # 行业RPS相关
    # ==========================================
    
    def get_industry_rps(self) -> pd.DataFrame:
        """获取行业RPS数据"""
        # 尝试从缓存加载
        if is_cache_valid('industry_rps', 1):
            df = load_industry_rps_cache()
            if df is not None and not df.empty:
                print(f"    -> 使用行业RPS缓存")
                return df
        
        if self.use_mock:
            df = generate_mock_industry_rps()
            save_industry_rps_cache(df)
            return df
        
        # 从API获取申万行业列表 - 使用 index_classify
        def _fetch_sw():
            if self.use_mock:
                return self._mock_client.index_classify()
            return self._pro.index_classify()
        
        industry_list = self._call_with_retry(_fetch_sw)
        if industry_list is None or industry_list.empty:
            return None
        
        industry_rps = []
        
        # 计算每个行业的RPS
        for _, ind in industry_list.iterrows():
            index_code = ind['index_code']
            industry_name = ind['industry_name']
            
            # 只处理一级行业
            if ind.get('level') != 'L1':
                continue
            
            # 获取行业指数数据 - 使用 sw_daily 接口
            start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y%m%d')
            
            def _fetch_idx():
                if self.use_mock:
                    return self._mock_client.sw_daily(index_code=index_code, start_date=start_date)
                return self._pro.sw_daily(index_code=index_code, start_date=start_date)
            
            df_ind = self._call_with_retry(_fetch_idx)
            
            if df_ind is not None and len(df_ind) >= config.RPS_DAYS:
                df_ind = df_ind.sort_values('trade_date')
                recent = df_ind.tail(config.RPS_DAYS)
                if len(recent) >= 2:
                    rps = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / recent['close'].iloc[0] * 100
                    industry_rps.append({
                        'industry': industry_name,
                        'rps': rps,
                        'code': index_code
                    })
        
        if industry_rps:
            df_rps = pd.DataFrame(industry_rps)
            df_rps = df_rps.sort_values('rps', ascending=False).reset_index(drop=True)
            save_industry_rps_cache(df_rps)
            return df_rps
        
        return None
    
    # ==========================================
    # 资金流向相关
    # ==========================================
    
    def get_northbound_funds(self, ts_code: str) -> Dict[str, Any]:
        """获取北向资金数据"""
        if self.use_mock:
            return generate_mock_northbound_funds(ts_code)
        
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y%m%d')
        
        def _fetch():
            return self._pro.moneyflow_hsgt(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
        
        df = self._call_with_retry(_fetch)
        
        if df is not None and not df.empty:
            # 计算5日净流入
            net_inflow = df.tail(5)['net_inflow'].sum() if 'net_inflow' in df.columns else 0
            return {
                'total_net_inflow': float(net_inflow) if not pd.isna(net_inflow) else 0,
                'consecutive_days': self._count_consecutive_days(df),
            }
        
        return {'total_net_inflow': 0, 'consecutive_days': 0}
    
    def _count_consecutive_days(self, df: pd.DataFrame) -> int:
        """计算北向资金连续净买入天数"""
        if 'net_inflow' not in df.columns:
            return 0
        
        consecutive = 0
        for _, row in df.tail(5).iterrows():
            if row['net_inflow'] > 0:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    def get_main_funds(self, ts_code: str) -> Dict[str, Any]:
        """获取主力资金数据"""
        if self.use_mock:
            return generate_mock_main_funds(ts_code)
        
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime('%Y%m%d')
        
        def _fetch():
            return self._pro.moneyflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
        
        df = self._call_with_retry(_fetch)
        
        if df is not None and not df.empty:
            net_inflow = df['net_inflow'].sum() if 'net_inflow' in df.columns else 0
            return {
                'net_inflow_5d': float(net_inflow) if not pd.isna(net_inflow) else 0,
            }
        
        return {'net_inflow_5d': 0}


# 全局客户端实例
_client: Optional[TushareClient] = None


def get_client(use_mock: bool = False) -> TushareClient:
    """获取全局API客户端"""
    global _client
    if _client is None:
        _client = TushareClient(use_mock=use_mock)
    return _client


def reset_client():
    """重置客户端"""
    global _client
    _client = None
