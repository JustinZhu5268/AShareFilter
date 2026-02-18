"""
Mock数据生成器 - 与Tushare API实际返回数据格式一致
基于 docs/tushare_api_validation.py 的验证结果
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any


# ==================== Tushare API 数据格式验证结果 ====================
# 1. stock_basic: ts_code, symbol, name, industry, list_date
# 2. daily_basic: ts_code, trade_date, close, total_mv(万元), circ_mv(万元), free_share(万股)
# 3. fina_indicator: ts_code, ann_date, end_date, roe(%)
# 4. adj_factor: ts_code, trade_date, adj_factor
# 5. daily: ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol(手), amount(千元)
# 6. moneyflow_hsgt: trade_date, ggt_ss, ggt_sz, hgt, sgt, north_money, south_money
# 7. moneyflow: ts_code, trade_date, buy_sm_vol, ..., net_mf_vol, net_mf_amount


def generate_mock_stock_list() -> pd.DataFrame:
    """生成模拟股票列表"""
    stocks = [
        {'ts_code': '300274.SZ', 'symbol': '300274', 'name': '阳光电源', 'industry': '电气设备', 'list_date': '20110630'},
        {'ts_code': '000001.SZ', 'symbol': '000001', 'name': '平安银行', 'industry': '银行', 'list_date': '19910403'},
        {'ts_code': '600519.SH', 'symbol': '600519', 'name': '贵州茅台', 'industry': '白酒', 'list_date': '20010827'},
        {'ts_code': '000858.SZ', 'symbol': '000858', 'name': '五粮液', 'industry': '白酒', 'list_date': '19980427'},
        {'ts_code': '300750.SZ', 'symbol': '300750', 'name': '宁德时代', 'industry': '电池', 'list_date': '20180611'},
        {'ts_code': '002594.SZ', 'symbol': '002594', 'name': '比亚迪', 'industry': '汽车整车', 'list_date': '20110630'},
        {'ts_code': '600036.SH', 'symbol': '600036', 'name': '招商银行', 'industry': '银行', 'list_date': '20020409'},
        {'ts_code': '000333.SZ', 'symbol': '000333', 'name': '美的集团', 'industry': '家电', 'list_date': '20130918'},
    ]
    return pd.DataFrame(stocks)


def generate_mock_market_cap() -> pd.DataFrame:
    """
    生成模拟市值数据
    注意: Tushare返回的total_mv单位是万元!
    """
    # 300274阳光电源: 股价149.16元, 流通股143185.6649万股
    # 市值 = 149.16 × 143185.6649 × 10000 = 213575737765 元 ≈ 2135.76亿元 (万元单位)
    data = [
        {'ts_code': '300274.SZ', 'trade_date': '20260213', 'close': 149.16, 
         'total_mv': 32236364.43, 'circ_mv': 24718392.22, 'free_share': 143185.6649},
        {'ts_code': '000001.SZ', 'trade_date': '20260213', 'close': 12.34, 
         'total_mv': 23456700.00, 'circ_mv': 18234500.00, 'free_share': 1900000.00},
        {'ts_code': '600519.SH', 'trade_date': '20260213', 'close': 1850.00, 
         'total_mv': 2323450000.00, 'circ_mv': 2323450000.00, 'free_share': 125580.00},
        {'ts_code': '000858.SZ', 'trade_date': '20260213', 'close': 145.60, 
         'total_mv': 56789000.00, 'circ_mv': 38900000.00, 'free_share': 390000.00},
        {'ts_code': '300750.SZ', 'trade_date': '20260213', 'close': 185.50, 
         'total_mv': 82345600.00, 'circ_mv': 65432100.00, 'free_share': 443800.00},
        {'ts_code': '002594.SZ', 'trade_date': '20260213', 'close': 268.90, 
         'total_mv': 78234500.00, 'circ_mv': 71234500.00, 'free_share': 291000.00},
        {'ts_code': '600036.SH', 'trade_date': '20260213', 'close': 38.50, 
         'total_mv': 98765400.00, 'circ_mv': 87654300.00, 'free_share': 2522000.00},
        {'ts_code': '000333.SZ', 'trade_date': '20260213', 'close': 62.80, 
         'total_mv': 45678900.00, 'circ_mv': 42345600.00, 'free_share': 727300.00},
    ]
    return pd.DataFrame(data)


def generate_mock_financial_ttm() -> pd.DataFrame:
    """
    生成模拟财务TTM数据
    注意: Tushare返回ann_date和end_date，没有report_date
    """
    data = [
        # 300274 阳光电源 - 2025年三季报
        {'ts_code': '300274.SZ', 'ann_date': '20251029', 'end_date': '20250930', 'roe': 29.05},
        {'ts_code': '300274.SZ', 'ann_date': '20250826', 'end_date': '20250630', 'roe': 28.50},
        {'ts_code': '300274.SZ', 'ann_date': '20250426', 'end_date': '20250331', 'roe': 25.80},
        
        # 000001 平安银行
        {'ts_code': '000001.SZ', 'ann_date': '20251030', 'end_date': '20250930', 'roe': 12.45},
        {'ts_code': '000001.SZ', 'ann_date': '20250828', 'end_date': '20250630', 'roe': 11.90},
        
        # 600519 贵州茅台
        {'ts_code': '600519.SH', 'ann_date': '20251028', 'end_date': '20250930', 'roe': 32.80},
        {'ts_code': '600519.SH', 'ann_date': '20250826', 'end_date': '20250630', 'roe': 31.50},
        
        # 其他股票...
        {'ts_code': '000858.SZ', 'ann_date': '20251029', 'end_date': '20250930', 'roe': 28.50},
        {'ts_code': '300750.SZ', 'ann_date': '20251028', 'end_date': '20250930', 'roe': 24.50},
        {'ts_code': '002594.SZ', 'ann_date': '20251029', 'end_date': '20250930', 'roe': 18.90},
        {'ts_code': '600036.SH', 'ann_date': '20251030', 'end_date': '20250930', 'roe': 15.60},
        {'ts_code': '000333.SZ', 'ann_date': '20251028', 'end_date': '20250930', 'roe': 24.50},
    ]
    return pd.DataFrame(data)


def generate_mock_adj_factor() -> pd.DataFrame:
    """生成模拟复权因子"""
    data = [
        {'ts_code': '300274.SZ', 'trade_date': '20260213', 'adj_factor': 1.2345},
        {'ts_code': '300274.SZ', 'trade_date': '20111104', 'adj_factor': 1.0},
        {'ts_code': '000001.SZ', 'trade_date': '20260213', 'adj_factor': 2.3456},
        {'ts_code': '600519.SH', 'trade_date': '20260213', 'adj_factor': 5.6789},
    ]
    return pd.DataFrame(data)


def generate_mock_daily_data(ts_code: str, days: int = 120) -> pd.DataFrame:
    """
    生成模拟日线数据
    注意: vol单位是手, amount单位是千元
    """
    end_date = datetime.datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='D')
    
    # 根据股票代码生成不同的价格数据
    np.random.seed(hash(ts_code) % 10000)
    
    if ts_code == '300274.SZ':
        # 阳光电源 - 模拟接近底部的走势
        base_price = 150.0
        prices = base_price - np.cumsum(np.random.randn(days) * 2)
        prices = np.maximum(prices, base_price * 0.7)
    elif ts_code == '600519.SH':
        # 贵州茅台 - 高位震荡
        base_price = 1800.0
        prices = base_price + np.cumsum(np.random.randn(days) * 10)
    else:
        base_price = 50.0
        prices = base_price + np.cumsum(np.random.randn(days) * 1)
    
    # 生成OHLCV数据
    data = []
    prev_close = prices[0] * 0.98  # 初始前收盘
    
    for i, date in enumerate(dates):
        close = prices[i]
        open_price = close + np.random.randn() * 2
        high = max(open_price, close) + abs(np.random.randn() * 1.5)
        low = min(open_price, close) - abs(np.random.randn() * 1.5)
        volume = 500000 + np.random.randint(-200000, 500000)
        amount = volume * close * 1000 / 10000  # 转换为千元 (手*元/10000)
        
        change = close - prev_close
        pct_chg = (change / prev_close * 100) if prev_close > 0 else 0
        
        data.append({
            'ts_code': ts_code,
            'trade_date': date.strftime('%Y%m%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'pre_close': round(prev_close, 2),
            'change': round(change, 2),
            'pct_chg': round(pct_chg, 4),
            'vol': round(volume, 2),
            'amount': round(amount, 2),
        })
        
        prev_close = close
    
    df = pd.DataFrame(data)
    return df


def generate_mock_industry_rps() -> pd.DataFrame:
    """生成模拟行业RPS数据"""
    data = [
        {'industry': '电气设备', 'rps': 8.5, 'trend': 'up'},
        {'industry': '元器件', 'rps': 7.8, 'trend': 'up'},
        {'industry': '专用机械', 'rps': 7.2, 'trend': 'up'},
        {'industry': '软件服务', 'rps': 6.9, 'trend': 'up'},
        {'industry': '汽车配件', 'rps': 6.5, 'trend': 'up'},
        {'industry': '半导体', 'rps': 6.2, 'trend': 'up'},
        {'industry': '医药', 'rps': 5.8, 'trend': 'down'},
        {'industry': '银行', 'rps': 5.2, 'trend': 'down'},
    ]
    df = pd.DataFrame(data)
    return df.sort_values('rps', ascending=False).reset_index(drop=True)


def generate_mock_northbound_funds(ts_code: str) -> Dict[str, Any]:
    """
    生成模拟北向资金数据
    注意: Tushare返回north_money，没有直接的net_inflow字段
    """
    np.random.seed(hash(ts_code) % 10000)
    
    # 生成10天的数据
    dates = pd.date_range(end=datetime.datetime.now(), periods=10, freq='D')
    north_money = np.random.randint(200000, 400000, size=10).tolist()
    
    return {
        'trade_date': [d.strftime('%Y%m%d') for d in dates],
        'north_money': north_money,
    }


def generate_mock_main_funds(ts_code: str) -> Dict[str, Any]:
    """
    生成模拟主力资金数据
    注意: Tushare返回net_mf_amount，没有直接的net_inflow字段
    """
    np.random.seed(hash(ts_code) % 10000 + 1)
    
    # 生成10天的数据
    dates = pd.date_range(end=datetime.datetime.now(), periods=10, freq='D')
    net_mf_amount = np.random.randint(-50000, 20000, size=10).tolist()
    
    return {
        'ts_code': ts_code,
        'trade_date': [d.strftime('%Y%m%d') for d in dates],
        'net_mf_amount': net_mf_amount,
    }


class MockTushareClient:
    """Mock Tushare 客户端 - 与真实API返回格式一致"""
    
    def __init__(self):
        self._stock_list = generate_mock_stock_list()
        self._market_cap = generate_mock_market_cap()
        self._financial_ttm = generate_mock_financial_ttm()
        self._adj_factor = generate_mock_adj_factor()
    
    def stock_basic(self, exchange='', list_status='L', fields=None):
        """获取股票列表"""
        df = self._stock_list.copy()
        if list_status:
            # 简化处理，假设所有都是上市状态
            pass
        if fields:
            field_list = fields.split(',')
            return df[field_list]
        return df
    
    def daily_basic(self, ts_code=None, fields='total_mv'):
        """获取市值数据"""
        if ts_code:
            df = self._market_cap[self._market_cap['ts_code'] == ts_code]
            if fields:
                field_list = fields.split(',')
                # 确保包含需要的字段
                for f in field_list:
                    if f not in df.columns:
                        df[f] = 0
                return df[field_list]
            return df
        return self._market_cap
    
    def fina_indicator(self, ts_code, fields=None):
        """获取财务指标"""
        df = self._financial_ttm[self._financial_ttm['ts_code'] == ts_code].copy()
        df = df.sort_values('end_date', ascending=False)
        if fields:
            field_list = fields.split(',')
            for f in field_list:
                if f not in df.columns:
                    df[f] = 0
            return df[field_list]
        return df
    
    def adj_factor(self, ts_code):
        """获取复权因子"""
        return self._adj_factor[self._adj_factor['ts_code'] == ts_code]
    
    def daily(self, ts_code, start_date, end_date):
        """获取日线数据"""
        days = (datetime.datetime.strptime(end_date, '%Y%m%d') - 
                datetime.datetime.strptime(start_date, '%Y%m%d')).days + 1
        return generate_mock_daily_data(ts_code, min(days, 120))
    
    def moneyflow_hsgt(self, ts_code, start_date, end_date):
        """获取北向资金"""
        return pd.DataFrame(generate_mock_northbound_funds(ts_code))
    
    def moneyflow(self, ts_code, start_date, end_date):
        """获取主力资金"""
        return pd.DataFrame(generate_mock_main_funds(ts_code))
    
    def sw_index(self, level='1', src='SW'):
        """获取申万行业 - Mock返回空数据"""
        # 申万行业接口需要特殊权限，返回空DataFrame
        return pd.DataFrame(columns=['index_code', 'industry_name'])
    
    def index_daily(self, index_code, start_date):
        """获取行业指数数据"""
        return generate_mock_daily_data(index_code, 30)
