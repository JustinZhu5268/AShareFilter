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

def get_stock_weekly_data(stock_code, days=500):
    """获取周线数据"""
    try:
        if stock_code.startswith('6'):
            ts_code = f"{stock_code}.SH"
        else:
            ts_code = f"{stock_code}.SZ"
        
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days*2)).strftime('%Y%m%d')
        
        df = pro.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
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
        
        # 获取利润表数据
        df_inc = pro.income(ts_code=ts_code)
        if df_inc is not None and not df_inc.empty:
            latest = df_inc.iloc[0]
            # Tushare的income表：total_revenue是营收，n_income是净利润
            return {
                'revenue': float(latest.get('total_revenue', 0)) if latest.get('total_revenue') else 0,
                'net_profit': float(latest.get('n_income', 0)) if latest.get('n_income') else 0  # 净利润是n_income
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
            # 营收>0 且 净利润>0 (剔除亏损公司)
            if fin and fin.get('revenue', 0) > 0 and fin.get('net_profit', 0) > 0:
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
    
# ==========================================
# 报告生成
# ==========================================

def generate_report(top_industries, candidate_stocks, all_results, config):
    """生成Markdown选股报告"""
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 收集所有结果的行业分布
    industry_stats = {}
    for r in candidate_stocks:
        ind = r.get('industry', '未知')
        if ind not in industry_stats:
            industry_stats[ind] = 0
        industry_stats[ind] += 1
    
    # 计算利润率
    for r in candidate_stocks:
        r['profit_margin'] = (r['net_profit'] / r['revenue'] * 100) if r['revenue'] > 0 else 0
    
    report = f"""# 📊 热门行业龙头超跌反弹策略 - 选股报告

**生成时间**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 一、为什么选择这些行业？

### 1.1 行业选择逻辑

本策略采用**热门行业龙头策略**，选择依据如下：

| 选择标准 | 说明 |
|---------|------|
| 行业覆盖 | 纳入全部{len(top_industries)}个热门行业（按股票数量排序） |
| 龙头效应 | 在各细分行业中选取营收排名前5的龙头公司 |
| ST排除 | 剔除ST/*ST股票 |

### 1.2 入选的行业板块

本策略覆盖 **{len(top_industries)}** 个行业板块，按股票数量排序：

"""
    
    for i, ind in enumerate(top_industries, 1):
        cnt = industry_stats.get(ind, 0)
        report += f"{i}. **{ind}** ({cnt}只)\n"
    
    report += f"""
> 说明：Tushare行业分类共{len(top_industries)}个，已全部纳入。

## 二、为什么选择这些公司？

### 2.1 公司筛选标准

| 筛选条件 | 标准说明 |
|---------|---------|
| 营收Top5 | 在各行业中营收排名前5 |
| 净利润>0 | 剔除亏损公司，保证盈利能力 |
| 获利盘≤X% | 获利盘比例低于设定阈值（超跌信号） |
| 量能活跃 | 量比≥0.8 且 换手率≥1%（资金关注） |

### 2.2 候选公司统计

- **候选股票总数**: {len(candidate_stocks)} 只
- **行业覆盖**: {len(industry_stats)} 个

## 三、各阈值筛选结果

"""
    
    # 多阈值结果
    thresholds = [50.0, 40.0, 30.0, 20.0, 10.0]
    threshold_results = {}
    
    for thresh in thresholds:
        filtered = [r for r in candidate_stocks if r.get('profit_ratio', 100) <= thresh]
        threshold_results[thresh] = filtered
        
        report += f"""
### 3.{thresholds.index(thresh)+1} 获利盘 ≤ {thresh:.1f}%

**符合条件**: {len(filtered)} 只

| 代码 | 名称 | 行业 | 营收(亿) | 净利润(亿) | 利润率 | 现价 | 获利盘 | 日KDJ | 周KDJ | 量比 | 换手率 |
|------|------|------|----------|------------|--------|------|--------|-------|------|--------|
"""
        if filtered:
            for r in filtered[:10]:  # 最多显示10只
                code = r.get('code', '')
                name = r.get('name', '')
                industry = r.get('industry', '')[:8]
                revenue = r.get('revenue', 0) / 1e8
                net_profit = r.get('net_profit', 0) / 1e8
                profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
                price = r.get('price', 0)
                profit_ratio = r.get('profit_ratio', 0)
                kdj = r.get('kdj_signal', '无')
                week_kdj = r.get('week_kdj_signal', '无')
                vol_ratio = r.get('vol_ratio', 0)
                turnover = r.get('turnover', 0)
                
                report += f"| {code} | {name} | {industry} | {revenue:.1f} | {net_profit:.1f} | {profit_margin:.1f}% | {price:.2f} | {profit_ratio:.1f}% | {kdj} | {week_kdj} | {vol_ratio:.2f} | {turnover:.1f}% |\n"
        else:
            report += "| - | - | - | - | - | - | - | - | - | - | - | - |\n"
    
    # 详细分析TOP10
    report += """
## 四、候选股票详细分析

以下是按营收排序的前10只候选股票：

| 排名 | 代码 | 名称 | 行业 | 营收(亿) | 净利润(亿) | 利润率 | 现价 | 获利盘 | 量比 | 换手率 | KDJ |
|------|------|------|------|----------|------------|--------|------|--------|------|--------|-----|
"""
    
    # 按营收排序
    sorted_stocks = sorted(candidate_stocks, key=lambda x: x.get('revenue', 0), reverse=True)
    
    for i, r in enumerate(sorted_stocks[:10], 1):
        code = r.get('code', '')
        name = r.get('name', '')
        industry = r.get('industry', '')[:8]
        revenue = r.get('revenue', 0) / 1e8
        net_profit = r.get('net_profit', 0) / 1e8
        profit_margin = r.get('profit_margin', 0)
        price = r.get('price', 0)
        profit_ratio = r.get('profit_ratio', 0)
        vol_ratio = r.get('vol_ratio', 0)
        turnover = r.get('turnover', 0)
        kdj = r.get('kdj_signal', '无')
        
        report += f"| {i} | {code} | {name} | {industry} | {revenue:.1f} | {net_profit:.1f} | {profit_margin:.1f}% | {price:.2f} | {profit_ratio:.1f}% | {vol_ratio:.2f} | {turnover:.1f}% | {kdj} |\n"
    
    # 保存报告
    report_file = f"选股报告_{timestamp}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 报告已保存: {report_file}")
    
    return report_file


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
    top_industries = []
    for i, (ind, cnt) in enumerate(industry_counts.head(CONFIG['TOP_N_PRIMARY']).items()):
        print(f"   {i+1}. {ind}: {cnt}只")
        top_industries.append(ind)
    
    # Step 2: 筛选每个行业的龙头股
    print("\n📊 Step 2: 筛选行业龙头 (营收Top5)...")
    
    candidate_stocks = []
    
    for industry_name in top_industries:
        # 获取该行业的所有股票
        industry_stocks = stocks[stocks['industry'] == industry_name]
        
        # 获取每只股票的财务数据
        stock_list = []
        for _, stock in industry_stocks.iterrows():
            ts_code = stock['ts_code']
            stock_code = ts_code.replace('.SH', '').replace('.SZ', '')
            
            fin = get_stock_financial_data(stock_code)
            # 营收>0 且 净利润>0 (剔除亏损公司)
            if fin and fin.get('revenue', 0) > 0 and fin.get('net_profit', 0) > 0:
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
        
        # 计算日KDJ
        df = calculate_kdj(df)
        
        # 获取周线数据并计算周KDJ
        df_weekly = get_stock_weekly_data(code)
        week_kdj_signal = "无"
        if df_weekly is not None and len(df_weekly) >= 10:
            df_weekly = calculate_kdj(df_weekly)
            latest_week = df_weekly.iloc[-1]
            week_k = latest_week.get('K', 0)
            week_d = latest_week.get('D', 0)
            if week_k > week_d:
                week_kdj_signal = "金叉"
            elif week_d - week_k < CONFIG['KDJ_APPROACHING_DIFF']:
                week_kdj_signal = "接近"
        
        # 最新数据
        latest = df.iloc[-1]
        
        # 计算量比
        avg_vol = df['成交量'].tail(20).mean()
        vol_ratio = latest['成交量'] / avg_vol if avg_vol > 0 else 0
        
        # 计算换手率 (估算)
        turnover = (latest['成交量'] / 1000000) * 100  # 简化估算
        
        # 日KDJ信号
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
        
        # 添加到结果（带技术指标）
        stock['profit_ratio'] = profit_ratio
        stock['vol_ratio'] = vol_ratio
        stock['turnover'] = turnover
        stock['kdj_signal'] = kdj_signal
        stock['week_kdj_signal'] = week_kdj_signal  # 添加周KDJ
        stock['price'] = latest['收盘']
        
        if profit_ratio <= CONFIG['MAX_PROFIT_RATIO'] and volume_ok:
            results.append(stock)
    
    print(f"\n✅ 最终筛选: 符合条件 {len(results)} 只 / 候选 {len(candidate_stocks)} 只")
    
    # 输出结果
    if results:
        print("\n" + "="*60)
        print("📋 筛选结果:")
        print("="*60)
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['code']} {r['name']} | {r['industry']}")
            print(f"   营收: {r['revenue']/1e8:.1f}亿 | 获利盘: {r['profit_ratio']:.1f}% | 量比: {r['vol_ratio']:.2f} | 换手: {r['turnover']:.1f}%")
    else:
        print("\n😔 未找到符合所有条件的股票")
        
        # 显示候选股票信息
        print("\n📊 候选股票概览 (前10只):")
        for s in candidate_stocks[:10]:
            print(f"   {s['code']} {s['name']} | 营收: {s['revenue']/1e8:.1f}亿")
    
    # Step 4: 生成报告
    print("\n📊 Step 4: 生成报告...")
    generate_report(top_industries, candidate_stocks, results, CONFIG)

if __name__ == "__main__":
    main_strategy()
