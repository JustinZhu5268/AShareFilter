"""
热门行业龙头超跌反弹策略 - 选股程序
数据源: Tushare
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
import datetime
import time
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# Tushare 配置
# ==========================================
TUSHARE_TOKEN = "82e556132679ef72ee42217682fa809a68c2d32a8d50d0df9b87d0f37384"

import tushare as ts
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
pro._DataApi__token = TUSHARE_TOKEN
pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'
print("✅ Tushare 初始化成功！")

# ==========================================
# 配置参数
# ==========================================
CONFIG = {
    'TOP_N_PRIMARY': 5,
    'TOP_N_SECONDARY_PER_PRIMARY': 5,
    'TOP_N_STOCKS_PER_SECTOR': 5,
    'MAX_PROFIT_RATIO': 10.0,
    'VOLUME_RATIO_MIN': 0.8,
    'TURNOVER_MIN': 1.0,
    'KDJ_APPROACHING_DIFF': 10,
}

# ==========================================
# 数据获取函数
# ==========================================

def get_stock_list():
    """获取全部股票列表和行业信息"""
    try:
        df = pro.stock_basic(exchange='SSE', list_status='L')
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
    return None

def get_stock_daily_data(stock_code, days=250):
    """获取日线数据"""
    try:
        if stock_code.startswith('6'):
            ts_code = f"{stock_code}.SH"
        else:
            ts_code = f"{stock_code}.SZ"
        
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days*2)).strftime('%Y%m%d')
        
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is not None and not df.empty:
            df = df.sort_values('trade_date')
            df = df.rename(columns={
                'trade_date': '日期',
                'open': '开盘',
                'high': '最高',
                'low': '最低',
                'close': '收盘',
                'vol': '成交量',
                'amount': '成交额'
            })
            return df
    except:
        pass
    return None

def get_stock_financial_data(stock_code):
    """获取财务数据"""
    try:
        if stock_code.startswith('6'):
            ts_code = f"{stock_code}.SH"
        else:
            ts_code = f"{stock_code}.SZ"
        
        df_inc = pro.income(ts_code=ts_code, fields='ts_code,report_date,total_revenue,net_profit')
        if df_inc is not None and not df_inc.empty:
            latest = df_inc.iloc[0]
            # Tushare返回单位是元
            return {
                'revenue': float(latest.get('total_revenue', 0)) if latest.get('total_revenue') else 0,
                'net_profit': float(latest.get('net_profit', 0)) if latest.get('net_profit') else 0
            }
    except:
        pass
    return None

# ==========================================
# KDJ计算
# ==========================================

def calculate_kdj(df, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    if df is None or len(df) < n:
        return df
    
    low_list = df['最低'].rolling(window=n, min_periods=1).min()
    high_list = df['最高'].rolling(window=n, min_periods=1).max()
    
    rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
    rsv = rsv.fillna(50)
    
    df['K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    return df

# ==========================================
# 主策略
# ==========================================

def main_strategy():
    print("\n" + "="*60)
    print("🚀 热门行业龙头超跌反弹策略 - 选股程序")
    print("="*60)
    
    # Step 1: 获取股票列表
    print("\n📊 Step 1: 获取股票列表...")
    
    stocks = get_stock_list()
    if stocks is None or stocks.empty:
        print("❌ 无法获取股票列表")
        return
    
    print(f"✅ 获取到 {len(stocks)} 只股票")
    
    # 获取行业分布并排序
    industry_counts = stocks['industry'].value_counts()
    print("\n🔥 热门行业 (按股票数量):")
    for i, (ind, cnt) in enumerate(industry_counts.head(CONFIG['TOP_N_PRIMARY']).items()):
        print(f"   {i+1}. {ind}: {cnt}只")
    
    # Step 2: 筛选每个行业的龙头股
    print("\n📊 Step 2: 筛选行业龙头 (营收Top5)...")
    
    candidate_stocks = []
    top_industries = industry_counts.head(CONFIG['TOP_N_PRIMARY']).index.tolist()
    
    for industry_name in top_industries:
        # 获取该行业的所有股票
        industry_stocks = stocks[stocks['industry'] == industry_name]
        
        # 获取每只股票的财务数据
        stock_list = []
        for _, stock in industry_stocks.iterrows():
            ts_code = stock['ts_code']
            stock_code = ts_code.replace('.SH', '').replace('.SZ', '')
            
            fin = get_stock_financial_data(stock_code)
            if fin and fin.get('revenue', 0) > 0:
                stock_list.append({
                    'code': stock_code,
                    'name': stock['name'],
                    'revenue': fin.get('revenue', 0),
                    'net_profit': fin.get('net_profit', 0),
                    'industry': industry_name
                })
        
        # 按营收排序，取Top5
        stock_list.sort(key=lambda x: x['revenue'], reverse=True)
        top_stocks = stock_list[:CONFIG['TOP_N_STOCKS_PER_SECTOR']]
        
        candidate_stocks.extend(top_stocks)
        print(f"  -> {industry_name}: 找到 {len(top_stocks)} 只龙头")
    
    if not candidate_stocks:
        print("\n❌ 未找到任何候选股票")
        return
    
    print(f"\n✅ 初步筛选出 {len(candidate_stocks)} 只龙头候选股")
    
    # Step 3: 技术分析筛选
    print("\n📊 Step 3: 技术分析筛选...")
    print("="*60)
    
    results = []
    
    for stock in candidate_stocks:
        code = stock['code']
        name = stock['name']
        
        # 获取日线数据
        df = get_stock_daily_data(code)
        if df is None or len(df) < 60:
            continue
        
        # 计算KDJ
        df = calculate_kdj(df)
        
        # 最新数据
        latest = df.iloc[-1]
        
        # 计算量比
        avg_vol = df['成交量'].tail(20).mean()
        vol_ratio = latest['成交量'] / avg_vol if avg_vol > 0 else 0
        
        # 计算换手率 (估算)
        turnover = (latest['成交量'] / 1000000) * 100  # 简化估算
        
        # KDJ信号
        k = latest.get('K', 0)
        d = latest.get('D', 0)
        
        kdj_signal = "未知"
        if k > d:
            kdj_signal = "金叉"
        elif d - k < CONFIG['KDJ_APPROACHING_DIFF']:
            kdj_signal = "接近"
        
        # 量比和换手率
        volume_ok = vol_ratio >= CONFIG['VOLUME_RATIO_MIN'] and turnover >= CONFIG['TURNOVER_MIN']
        
        # 获利盘 (简化：使用最近60天最低价以来的涨幅)
        low_60 = df['收盘'].tail(60).min()
        profit_ratio = (latest['收盘'] - low_60) / low_60 * 100 if low_60 > 0 else 0
        
        if profit_ratio <= CONFIG['MAX_PROFIT_RATIO'] and volume_ok:
            results.append({
                'code': code,
                'name': name,
                'industry': stock['industry'],
                'revenue': stock['revenue'] / 1e8,
                'profit_ratio': profit_ratio,
                'vol_ratio': vol_ratio,
                'turnover': turnover,
                'kdj_signal': kdj_signal,
                'price': latest['收盘']
            })
    
    print(f"\n✅ 最终筛选: 符合条件 {len(results)} 只 / 候选 {len(candidate_stocks)} 只")
    
    # 输出结果
    if results:
        print("\n" + "="*60)
        print("📋 筛选结果:")
        print("="*60)
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['code']} {r['name']} | {r['industry']}")
            print(f"   营收: {r['revenue']:.1f}亿 | 获利盘: {r['profit_ratio']:.1f}% | 量比: {r['vol_ratio']:.2f} | 换手: {r['turnover']:.1f}%")
    else:
        print("\n😔 未找到符合所有条件的股票")
        
        # 显示候选股票信息
        print("\n📊 候选股票概览 (前10只):")
        for s in candidate_stocks[:10]:
            print(f"   {s['code']} {s['name']} | 营收: {s['revenue']/1e8:.1f}亿")

if __name__ == "__main__":
    main_strategy()
