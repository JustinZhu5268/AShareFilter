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
        {'ts_code': '300274.SZ', 'symbol': '300274', 'name': '阳光电源', 'industry': '电气设备', 'list_date': '20110630', 'list_status': 'L'},
        {'ts_code': '000001.SZ', 'symbol': '000001', 'name': '平安银行', 'industry': '银行', 'list_date': '19910403', 'list_status': 'L'},
        {'ts_code': '600519.SH', 'symbol': '600519', 'name': '贵州茅台', 'industry': '白酒', 'list_date': '20010827', 'list_status': 'L'},
        {'ts_code': '000858.SZ', 'symbol': '000858', 'name': '五粮液', 'industry': '白酒', 'list_date': '19980427', 'list_status': 'L'},
        {'ts_code': '300750.SZ', 'symbol': '300750', 'name': '宁德时代', 'industry': '电池', 'list_date': '20180611', 'list_status': 'L'},
        {'ts_code': '002594.SZ', 'symbol': '002594', 'name': '比亚迪', 'industry': '汽车整车', 'list_date': '20110630', 'list_status': 'L'},
        {'ts_code': '600036.SH', 'symbol': '600036', 'name': '招商银行', 'industry': '银行', 'list_date': '20020409', 'list_status': 'L'},
        {'ts_code': '000333.SZ', 'symbol': '000333', 'name': '美的集团', 'industry': '家电', 'list_date': '20130918', 'list_status': 'L'},
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
        {'ts_code': '300274.SZ', 'ann_date': '20251029', 'end_date': '20250930', 'roe': 29.05, 'net_profit': 3500000000, 'revenue': 55000000000, 'deducted_net_profit': 3200000000},
        {'ts_code': '300274.SZ', 'ann_date': '20250826', 'end_date': '20250630', 'roe': 28.50, 'net_profit': 3200000000, 'revenue': 52000000000, 'deducted_net_profit': 2900000000},
        {'ts_code': '300274.SZ', 'ann_date': '20250426', 'end_date': '20250331', 'roe': 25.80, 'net_profit': 2800000000, 'revenue': 48000000000, 'deducted_net_profit': 2600000000},

        # 000001 平安银行
        {'ts_code': '000001.SZ', 'ann_date': '20251030', 'end_date': '20250930', 'roe': 12.45, 'net_profit': 45000000000, 'revenue': 120000000000, 'deducted_net_profit': 43000000000},
        {'ts_code': '000001.SZ', 'ann_date': '20250828', 'end_date': '20250630', 'roe': 11.90, 'net_profit': 42000000000, 'revenue': 115000000000, 'deducted_net_profit': 40000000000},

        # 600519 贵州茅台
        {'ts_code': '600519.SH', 'ann_date': '20251028', 'end_date': '20250930', 'roe': 32.80, 'net_profit': 85000000000, 'revenue': 180000000000, 'deducted_net_profit': 82000000000},
        {'ts_code': '600519.SH', 'ann_date': '20250826', 'end_date': '20250630', 'roe': 31.50, 'net_profit': 82000000000, 'revenue': 175000000000, 'deducted_net_profit': 80000000000},

        # 其他股票...
        {'ts_code': '000858.SZ', 'ann_date': '20251029', 'end_date': '20250930', 'roe': 28.50, 'net_profit': 25000000000, 'revenue': 90000000000, 'deducted_net_profit': 24000000000},
        {'ts_code': '300750.SZ', 'ann_date': '20251028', 'end_date': '20250930', 'roe': 24.50, 'net_profit': 55000000000, 'revenue': 320000000000, 'deducted_net_profit': 52000000000},
        {'ts_code': '002594.SZ', 'ann_date': '20251029', 'end_date': '20250930', 'roe': 18.90, 'net_profit': 45000000000, 'revenue': 280000000000, 'deducted_net_profit': 42000000000},
        {'ts_code': '600036.SH', 'ann_date': '20251030', 'end_date': '20250930', 'roe': 15.60, 'net_profit': 150000000000, 'revenue': 380000000000, 'deducted_net_profit': 145000000000},
        {'ts_code': '000333.SZ', 'ann_date': '20251028', 'end_date': '20250930', 'roe': 24.50, 'net_profit': 38000000000, 'revenue': 420000000000, 'deducted_net_profit': 36000000000},
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


def generate_mock_industry_rps(level: str = 'L1') -> pd.DataFrame:
    """生成模拟行业RPS数据
    
    Args:
        level: 行业级别，支持 'L1'(一级)、'L2'(二级)、'L3'(三级)
    """
    # 根据不同级别生成不同的行业数据
    if level == 'L1':
        data = [
            {'industry': '电气设备', 'industry_code': '801010.SI', 'rps': 8.5, 'level': 'L1'},
            {'industry': '电子', 'industry_code': '801080.SI', 'rps': 7.8, 'level': 'L1'},
            {'industry': '化工', 'industry_code': '801030.SI', 'rps': 7.2, 'level': 'L1'},
            {'industry': '有色金属', 'industry_code': '801050.SI', 'rps': 6.9, 'level': 'L1'},
            {'industry': '采掘', 'industry_code': '801020.SI', 'rps': 6.5, 'level': 'L1'},
            {'industry': '家用电器', 'industry_code': '801110.SI', 'rps': 6.2, 'level': 'L1'},
            {'industry': '食品饮料', 'industry_code': '801120.SI', 'rps': 5.8, 'level': 'L1'},
            {'industry': '钢铁', 'industry_code': '801040.SI', 'rps': 5.2, 'level': 'L1'},
        ]
    elif level == 'L2':
        data = [
            {'industry': '半导体', 'industry_code': '801080.SI', 'rps': 9.2, 'level': 'L2'},
            {'industry': '电源设备', 'industry_code': '801010.SI', 'rps': 8.7, 'level': 'L2'},
            {'industry': '元件', 'industry_code': '801080.SI', 'rps': 7.5, 'level': 'L2'},
            {'industry': '光学光电子', 'industry_code': '801080.SI', 'rps': 6.8, 'level': 'L2'},
            {'industry': '电机', 'industry_code': '801010.SI', 'rps': 6.3, 'level': 'L2'},
            {'industry': '电气自动化设备', 'industry_code': '801010.SI', 'rps': 5.9, 'level': 'L2'},
            {'industry': '消费电子', 'industry_code': '801080.SI', 'rps': 5.4, 'level': 'L2'},
            {'industry': '高低压设备', 'industry_code': '801010.SI', 'rps': 4.8, 'level': 'L2'},
        ]
    else:  # L3
        data = [
            {'industry': '集成电路', 'industry_code': '801080.SI', 'rps': 9.5, 'level': 'L3'},
            {'industry': '光伏设备', 'industry_code': '801010.SI', 'rps': 9.0, 'level': 'L3'},
            {'industry': '电池设备', 'industry_code': '801010.SI', 'rps': 8.3, 'level': 'L3'},
            {'industry': '风电设备', 'industry_code': '801010.SI', 'rps': 7.6, 'level': 'L3'},
            {'industry': '光学元件', 'industry_code': '801080.SI', 'rps': 6.9, 'level': 'L3'},
            {'industry': '分立器件', 'industry_code': '801080.SI', 'rps': 6.2, 'level': 'L3'},
            {'industry': '半导体材料', 'industry_code': '801080.SI', 'rps': 5.5, 'level': 'L3'},
            {'industry': '储能设备', 'industry_code': '801010.SI', 'rps': 4.8, 'level': 'L3'},
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


def generate_mock_holder_trade(ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    生成模拟股东增减持数据
    注意: Tushare stk_holdertrade接口返回字段
    """
    np.random.seed(hash(ts_code) % 10000)

    # 默认日期范围
    if end_date is None:
        end_date = datetime.datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y%m%d')

    # 生成随机日期
    dates = pd.date_range(start=start_date, end=end_date, periods=5)
    dates = [d.strftime('%Y%m%d') for d in dates]

    # 股东增减持数据
    # holder_type: C=增持, D=减持
    data = [
        {'ts_code': ts_code, 'ann_date': dates[0], 'holder_name': '阳光电源员工持股计划',
         'holder_type': 'C', 'holder_vol': 1500000, 'holder_ratio': 1.05,
         'after_share': 1500000, 'after_ratio': 1.05},
        {'ts_code': ts_code, 'ann_date': dates[1], 'holder_name': '某私募基金',
         'holder_type': 'D', 'holder_vol': -2000000, 'holder_ratio': -1.40,
         'after_share': 8000000, 'after_ratio': 5.60},
        {'ts_code': ts_code, 'ann_date': dates[2], 'holder_name': '阳光电源高管',
         'holder_type': 'C', 'holder_vol': 500000, 'holder_ratio': 0.35,
         'after_share': 9000000, 'after_ratio': 6.30},
        {'ts_code': ts_code, 'ann_date': dates[3], 'holder_name': '某券商资管',
         'holder_type': 'D', 'holder_vol': -1000000, 'holder_ratio': -0.70,
         'after_share': 7000000, 'after_ratio': 4.90},
        {'ts_code': ts_code, 'ann_date': dates[4], 'holder_name': '阳光电源实控人',
         'holder_type': 'C', 'holder_vol': 3000000, 'holder_ratio': 2.10,
         'after_share': 12000000, 'after_ratio': 8.40},
    ]

    return pd.DataFrame(data)


def generate_mock_holder_number(ts_code: str) -> pd.DataFrame:
    """
    生成模拟股东人数数据
    注意: Tushare stk_holdernumber接口返回字段
    """
    np.random.seed(hash(ts_code) % 10000)

    # 生成最近4个季度的固定日期数据
    now = datetime.datetime.now()
    dates = [
        now.strftime('%Y%m%d'),
        (now - datetime.timedelta(days=90)).strftime('%Y%m%d'),
        (now - datetime.timedelta(days=180)).strftime('%Y%m%d'),
        (now - datetime.timedelta(days=270)).strftime('%Y%m%d'),
    ]

    # 股东人数变化数据
    base_num = 50000
    data = [
        {'ts_code': ts_code, 'end_date': dates[0], 'holder_num': base_num, 'holder_num_change': 1200, 'holder_num_change_ratio': 2.46},
        {'ts_code': ts_code, 'end_date': dates[1], 'holder_num': base_num - 800, 'holder_num_change': -800, 'holder_num_change_ratio': -1.57},
        {'ts_code': ts_code, 'end_date': dates[2], 'holder_num': base_num - 2000, 'holder_num_change': -1200, 'holder_num_change_ratio': -2.30},
        {'ts_code': ts_code, 'end_date': dates[3], 'holder_num': base_num - 1500, 'holder_num_change': 500, 'holder_num_change_ratio': 1.01},
    ]

    return pd.DataFrame(data)


def generate_mock_main_business(ts_code: str) -> pd.DataFrame:
    """
    生成模拟主营业务数据
    注意: Tushare fina_mainbz接口返回字段
    """
    # 根据不同股票返回不同主营业务
    business_data = {
        '300274.SZ': [
            {'ts_code': '300274.SZ', 'end_date': '20250930', 'type': '1', 'bz_type': '太阳能发电', 'bz_item': '太阳能光伏发电业务'},
            {'ts_code': '300274.SZ', 'end_date': '20250930', 'type': '1', 'bz_type': '电站业务', 'bz_item': '光伏电站开发、建设及运营'},
            {'ts_code': '300274.SZ', 'end_date': '20250930', 'type': '1', 'bz_type': '储能业务', 'bz_item': '储能系统研发、生产与销售'},
        ],
        '600519.SH': [
            {'ts_code': '600519.SH', 'end_date': '20250930', 'type': '1', 'bz_type': '白酒生产', 'bz_item': '贵州茅台酒及系列酒的生产与销售'},
            {'ts_code': '600519.SH', 'end_date': '20250930', 'type': '1', 'bz_type': '酒类销售', 'bz_item': '酒类进出口业务'},
        ],
        '000001.SZ': [
            {'ts_code': '000001.SZ', 'end_date': '20250930', 'type': '1', 'bz_type': '银行业务', 'bz_item': '吸收公众存款、发放贷款等银行业务'},
        ],
    }

    # 默认返回阳光电源的数据
    return pd.DataFrame(business_data.get(ts_code, business_data['300274.SZ']))


def generate_mock_limit_list(ts_code: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    生成模拟涨跌停数据
    注意: Tushare stk_limitlist接口返回字段
    """
    # 默认日期范围
    if end_date is None:
        end_date = datetime.datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')

    # 生成模拟数据
    np.random.seed(42)

    stocks = ['300274.SZ', '600519.SH', '000001.SZ', '300750.SZ', '002594.SZ']
    if ts_code:
        stocks = [ts_code]

    data = []
    for stock in stocks:
        # 随机生成涨跌停记录
        for _ in range(3):
            trade_date = (datetime.datetime.now() - datetime.timedelta(days=np.random.randint(1, 30))).strftime('%Y%m%d')
            limit_type = np.random.choice(['U', 'D', ''], p=[0.1, 0.1, 0.8])
            pct_chg = float(np.random.choice([9.9, -9.9, 0.5, -0.5, 1.2, -1.2]))
            data.append({
                'ts_code': stock,
                'trade_date': trade_date,
                'limit': limit_type,
                'pct_chg': pct_chg,
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 104.0,
            })

    df = pd.DataFrame(data)
    if 'trade_date' in df.columns:
        df = df.sort_values('trade_date', ascending=False)
    return df


def generate_mock_stk_redeem(ts_code: str = None) -> pd.DataFrame:
    """
    生成模拟限售股解禁数据
    注意: Tushare stk_redeem接口返回字段
    """
    np.random.seed(hash(ts_code) % 10000 if ts_code else 42)

    stocks = ['300274.SZ', '600519.SH', '000001.SZ']
    if ts_code:
        stocks = [ts_code]

    data = []
    for stock in stocks:
        # 生成解禁数据
        for i in range(4):
            redeem_date = (datetime.datetime.now() + datetime.timedelta(days=90 * i)).strftime('%Y%m%d')
            data.append({
                'ts_code': stock,
                'redeem_date': redeem_date,
                'redeem_vol': np.random.randint(1000000, 50000000),
                'redeem_ratio': np.random.uniform(0.5, 5.0),
            })

    return pd.DataFrame(data)


def generate_mock_margin(ts_code: str = None) -> pd.DataFrame:
    """
    生成模拟融资融券数据
    注意: Tushare margin接口返回字段
    """
    np.random.seed(hash(ts_code) % 10000 if ts_code else 42)

    # 生成最近30天的融资融券数据
    dates = pd.date_range(end=datetime.datetime.now(), periods=30, freq='D')
    dates = [d.strftime('%Y%m%d') for d in dates]

    stock = ts_code or '300274.SZ'

    data = []
    for date in dates:
        data.append({
            'ts_code': stock,
            'trade_date': date,
            'rzye': np.random.randint(100000000, 500000000),  # 融资余额(元)
            'rzmre': np.random.randint(10000000, 50000000),   # 融资买入额(元)
            'rzche': np.random.randint(5000000, 20000000),    # 融资偿还额(元)
            'rqye': np.random.randint(50000000, 200000000),   # 融券余额(元)
            'rqmcl': np.random.randint(1000000, 5000000),     # 融券卖出量(股)
            'rqchl': np.random.randint(500000, 2000000),      # 融券偿还量(股)
        })

    return pd.DataFrame(data)


def generate_mock_inst_holder(ts_code: str = None) -> pd.DataFrame:
    """
    生成模拟机构持仓数据
    注意: Tushare inst_holder接口返回字段
    """
    np.random.seed(hash(ts_code) % 10000 if ts_code else 42)

    stock = ts_code or '300274.SZ'

    # 机构名称列表
    institutions = [
        '易方达基金', '华夏基金', '嘉实基金', '南方基金', '汇添富基金',
        '博时基金', '广发基金', '中信证券', '华泰证券', '招商证券',
        '高瓴资本', '红杉资本', '景林资产', '重阳投资', '高毅资产'
    ]

    # 生成最近4期的数据
    dates = pd.date_range(end=datetime.datetime.now(), periods=4, freq='QE')
    dates = [d.strftime('%Y%m%d') for d in dates]

    data = []
    for date in dates:
        # 每期随机选择3-8家机构
        num_institutions = np.random.randint(3, 9)
        selected_institutions = np.random.choice(institutions, num_institutions, replace=False)

        for inst in selected_institutions:
            hold_ratio = np.random.uniform(0.5, 8.0)
            change_ratio = np.random.uniform(-2.0, 2.0)

            data.append({
                'ts_code': stock,
                'end_date': date,
                'holder_name': inst,
                'holder_num': num_institutions,
                'hold_ratio': round(hold_ratio, 2),
                'change_ratio': round(change_ratio, 2),
            })

    return pd.DataFrame(data)


def generate_mock_longhu_bang(ts_code: str = None) -> pd.DataFrame:
    """
    生成模拟龙虎榜数据
    注意: Tushare daily_hsgt接口返回字段
    """
    np.random.seed(hash(ts_code) % 10000 if ts_code else 42)

    stock = ts_code or '300274.SZ'

    # 生成最近60天的数据，随机选择一些日期上榜
    dates = pd.date_range(end=datetime.datetime.now(), periods=60, freq='D')
    dates = [d.strftime('%Y%m%d') for d in dates]

    # 随机选择5-15天作为上榜日
    num_listed = np.random.randint(5, 16)
    listed_dates = np.random.choice(dates, num_listed, replace=False)

    data = []
    for date in listed_dates:
        buy = np.random.uniform(1000, 50000)  # 买入金额(万元)
        sell = np.random.uniform(1000, 50000)  # 卖出金额(万元)
        net_buy = buy - sell

        data.append({
            'ts_code': stock,
            'trade_date': date,
            'buy': round(buy, 2),
            'sell': round(sell, 2),
            'net_buy': round(net_buy, 2),
        })

    return pd.DataFrame(data)


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

    def stk_holdertrade(self, ts_code, start_date=None, end_date=None):
        """获取股东增减持数据"""
        return generate_mock_holder_trade(ts_code, start_date, end_date)

    def stk_holdernumber(self, ts_code):
        """获取股东人数数据"""
        return generate_mock_holder_number(ts_code)

    def fina_mainbz(self, ts_code):
        """获取主营业务数据"""
        return generate_mock_main_business(ts_code)

    def stk_limitlist(self, ts_code=None, start_date=None, end_date=None):
        """获取涨跌停数据"""
        return generate_mock_limit_list(ts_code, start_date, end_date)

    def stk_redeem(self, ts_code=None):
        """获取限售股解禁数据"""
        return generate_mock_stk_redeem(ts_code)

    def margin(self, ts_code=None, start_date=None, end_date=None):
        """获取融资融券数据"""
        return generate_mock_margin(ts_code)

    def inst_holder(self, ts_code=None, fields=None):
        """获取机构持仓数据"""
        df = generate_mock_inst_holder(ts_code)
        if fields:
            field_list = fields.split(',')
            for f in field_list:
                if f not in df.columns:
                    df[f] = 0
            return df[field_list]
        return df

    def daily_hsgt(self, ts_code=None, start_date=None, end_date=None):
        """获取龙虎榜数据"""
        return generate_mock_longhu_bang(ts_code)

    def index_classify(self, level: str = None):
        """获取行业分类 - 支持多级别
        
        Args:
            level: 行业级别，支持 'L1'(一级)、'L2'(二级)、'L3'(三级)，None表示返回所有级别
        """
        # 定义完整的申万行业分类数据（示例）
        data = [
            # L1: 一级行业
            {'index_code': '801010.SI', 'industry_name': '电气设备', 'level': 'L1', 'industry_code': '801010', 'src': 'SW2014'},
            {'index_code': '801020.SI', 'industry_name': '采掘', 'level': 'L1', 'industry_code': '801020', 'src': 'SW2014'},
            {'index_code': '801030.SI', 'industry_name': '化工', 'level': 'L1', 'industry_code': '801030', 'src': 'SW2014'},
            {'index_code': '801040.SI', 'industry_name': '钢铁', 'level': 'L1', 'industry_code': '801040', 'src': 'SW2014'},
            {'index_code': '801050.SI', 'industry_name': '有色金属', 'level': 'L1', 'industry_code': '801050', 'src': 'SW2014'},
            {'index_code': '801080.SI', 'industry_name': '电子', 'level': 'L1', 'industry_code': '801080', 'src': 'SW2014'},
            {'index_code': '801110.SI', 'industry_name': '家用电器', 'level': 'L1', 'industry_code': '801110', 'src': 'SW2014'},
            {'index_code': '801120.SI', 'industry_name': '食品饮料', 'level': 'L1', 'industry_code': '801120', 'src': 'SW2014'},
            {'index_code': '801150.SI', 'industry_name': '纺织服装', 'level': 'L1', 'industry_code': '801150', 'src': 'SW2014'},
            {'index_code': '801210.SI', 'industry_name': '轻工制造', 'level': 'L1', 'industry_code': '801210', 'src': 'SW2014'},
            
            # L2: 二级行业（属于电子L1）
            {'index_code': '801080.SI', 'industry_name': '半导体', 'level': 'L2', 'industry_code': '801080', 'src': 'SW2014'},
            {'index_code': '801080.SI', 'industry_name': '元件', 'level': 'L2', 'industry_code': '801080', 'src': 'SW2014'},
            {'index_code': '801080.SI', 'industry_name': '光学光电子', 'level': 'L2', 'industry_code': '801080', 'src': 'SW2014'},
            {'index_code': '801080.SI', 'industry_name': '消费电子', 'level': 'L2', 'industry_code': '801080', 'src': 'SW2014'},
            
            # L2: 二级行业（属于电气设备L1）
            {'index_code': '801010.SI', 'industry_name': '电机', 'level': 'L2', 'industry_code': '801010', 'src': 'SW2014'},
            {'index_code': '801010.SI', 'industry_name': '电气自动化设备', 'level': 'L2', 'industry_code': '801010', 'src': 'SW2014'},
            {'index_code': '801010.SI', 'industry_name': '电源设备', 'level': 'L2', 'industry_code': '801010', 'src': 'SW2014'},
            {'index_code': '801010.SI', 'industry_name': '高低压设备', 'level': 'L2', 'industry_code': '801010', 'src': 'SW2014'},
            
            # L3: 三级行业（属于半导体L2/电子L1）
            {'index_code': '801080.SI', 'industry_name': '集成电路', 'level': 'L3', 'industry_code': '801080', 'src': 'SW2014'},
            {'index_code': '801080.SI', 'industry_name': '分立器件', 'level': 'L3', 'industry_code': '801080', 'src': 'SW2014'},
            {'index_code': '801080.SI', 'industry_name': '半导体材料', 'level': 'L3', 'industry_code': '801080', 'src': 'SW2014'},
            {'index_code': '801080.SI', 'industry_name': '光学元件', 'level': 'L3', 'industry_code': '801080', 'src': 'SW2014'},
            
            # L3: 三级行业（属于电源设备L2/电气设备L1）
            {'index_code': '801010.SI', 'industry_name': '风电设备', 'level': 'L3', 'industry_code': '801010', 'src': 'SW2014'},
            {'index_code': '801010.SI', 'industry_name': '光伏设备', 'level': 'L3', 'industry_code': '801010', 'src': 'SW2014'},
            {'index_code': '801010.SI', 'industry_name': '电池设备', 'level': 'L3', 'industry_code': '801010', 'src': 'SW2014'},
            {'index_code': '801010.SI', 'industry_name': '储能设备', 'level': 'L3', 'industry_code': '801010', 'src': 'SW2014'},
        ]
        
        df = pd.DataFrame(data)
        
        # 根据level参数筛选
        if level:
            df = df[df['level'] == level]
        
        return df
    
    def sw_daily(self, index_code, start_date):
        """获取申万行业日线数据"""
        return generate_mock_daily_data(index_code, 30)
    
    def index_daily(self, ts_code, start_date, end_date):
        """获取指数日线数据 - 兼容旧接口"""
        return generate_mock_daily_data(ts_code, 30)
