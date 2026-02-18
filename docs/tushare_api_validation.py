#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tushare API 验证脚本
验证各个接口的返回数据格式，并与官方文档对比
"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import tushare as ts

TUSHARE_TOKEN = "82e556132679ef72ee42217682fa809a68c2d32a8d50d0df9b87d0f37384"
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
pro._DataApi__token = TUSHARE_TOKEN
pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'

def test_stock_basic():
    """测试 stock_basic 接口"""
    print("="*60)
    print("1. stock_basic 接口测试")
    print("="*60)
    
    df = pro.stock_basic(exchange='', list_status='L', 
                         fields='ts_code,symbol,name,industry,list_date')
    print(f"\n返回字段: {df.columns.tolist()}")
    print(f"数据条数: {len(df)}")
    print(f"\n示例数据:")
    print(df.head(3))
    
    return df

def test_daily_basic():
    """测试 daily_basic 接口"""
    print("\n" + "="*60)
    print("2. daily_basic 接口测试")
    print("="*60)
    
    # 只获取最近5天
    df = pro.daily_basic(ts_code='300274.SZ', 
                         start_date='20260210', 
                         end_date='20260214')
    print(f"\n返回字段: {df.columns.tolist()}")
    print(f"数据条数: {len(df)}")
    print(f"\n详细数据:")
    print(df)
    
        # 验证单位
    if len(df) > 0:
        row = df.iloc[-1]  # 最新数据
        print(f"\n数据验证:")
        print(f"  收盘价: {row['close']} 元")
        print(f"  总市值(total_mv): {row['total_mv']}")
        print(f"  流通市值(circ_mv): {row['circ_mv']}")
        print(f"  流通股数(free_share): {row['free_share']} 万股")
        
        # 验证市值单位
        print(f"\n市值单位验证:")
        free_share = row['free_share']
        calculated = row['close'] * free_share * 10000  # 元 × 万股 = 元
        print(f"  股价 × 流通股 = {row['close']} × {free_share} × 10000 = {calculated}")
        print(f"  total_mv / calculated = {row['total_mv'] / calculated}")
        print(f"  circ_mv / calculated = {row['circ_mv'] / calculated}")
    
    return df

def test_fina_indicator():
    """测试 fina_indicator 接口"""
    print("\n" + "="*60)
    print("3. fina_indicator 接口测试")
    print("="*60)
    
    df = pro.fina_indicator(ts_code='300274.SZ')
    print(f"\n返回字段: {df.columns.tolist()}")
    print(f"数据条数: {len(df)}")
    print(f"\n最新数据:")
    if len(df) > 0:
        # 尝试按可能的日期字段排序
        date_cols = ['end_date', 'report_date', 'ann_date']
        for col in date_cols:
            if col in df.columns:
                df = df.sort_values(col, ascending=False)
                break
        print(df.head(3))
        print(f"\n字段说明:")
        print(f"  roe: 净资产收益率(%)")
        if 'net_profit' in df.columns:
            print(f"  net_profit: 净利润(元)")
        if 'revenue' in df.columns:
            print(f"  revenue: 营业收入(元)")
    
    return df

def test_adj_factor():
    """测试 adj_factor 接口"""
    print("\n" + "="*60)
    print("4. adj_factor 接口测试")
    print("="*60)
    
    df = pro.adj_factor(ts_code='300274.SZ')
    print(f"\n返回字段: {df.columns.tolist()}")
    print(f"数据条数: {len(df)}")
    print(f"\n最新数据:")
    if len(df) > 0:
        print(df.tail(3))
        print(f"\nadj_factor说明: 复权因子")
        print(f"  前复权价格 = 原始价格 × adj_factor")
    
    return df

def test_daily():
    """测试 daily 接口"""
    print("\n" + "="*60)
    print("5. daily 接口测试")
    print("="*60)
    
    df = pro.daily(ts_code='300274.SZ', 
                   start_date='20260210', 
                   end_date='20260214')
    print(f"\n返回字段: {df.columns.tolist()}")
    print(f"数据条数: {len(df)}")
    print(f"\n数据:")
    print(df)
    print(f"\n字段说明:")
    print(f"  open/high/low/close: 开盘/最高/最低/收盘价")
    print(f"  vol: 成交量(手)")
    print(f"  amount: 成交额(千元)")
    
    return df

def test_moneyflow_hsgt():
    """测试 moneyflow_hsgt 接口 (北向资金)"""
    print("\n" + "="*60)
    print("6. moneyflow_hsgt 接口测试 (北向资金)")
    print("="*60)
    
    try:
        df = pro.moneyflow_hsgt(ts_code='300274.SZ',
                                 start_date='20260201',
                                 end_date='20260214')
        print(f"\n返回字段: {df.columns.tolist()}")
        print(f"数据条数: {len(df)}")
        if len(df) > 0:
            print(f"\n数据:")
            print(df)
    except Exception as e:
        print(f"接口调用失败: {e}")
        print("注意: 该接口可能需要特别权限")
    
    return None

def test_moneyflow():
    """测试 moneyflow 接口 (主力资金)"""
    print("\n" + "="*60)
    print("7. moneyflow 接口测试 (主力资金)")
    print("="*60)
    
    try:
        df = pro.moneyflow(ts_code='300274.SZ',
                           start_date='20260201',
                           end_date='20260214')
        print(f"\n返回字段: {df.columns.tolist()}")
        print(f"数据条数: {len(df)}")
        if len(df) > 0:
            print(f"\n数据:")
            print(df)
    except Exception as e:
        print(f"接口调用失败: {e}")
        print("注意: 该接口可能需要特别权限")
    
    return None

def test_sw_index():
    """测试 sw_index 接口 (申万行业)"""
    print("\n" + "="*60)
    print("8. sw_index 接口测试 (申万行业)")
    print("="*60)
    
    try:
        df = pro.sw_index(level='1', src='SW')
        print(f"\n返回字段: {df.columns.tolist()}")
        print(f"数据条数: {len(df)}")
        print(f"\n前5个行业:")
        print(df.head(5))
    except Exception as e:
        print(f"接口调用失败: {e}")
        print("注意: 该接口可能需要特别权限或参数不正确")

def test_index_daily():
    """测试 index_daily 接口 (行业指数)"""
    print("\n" + "="*60)
    print("9. index_daily 接口测试 (行业指数)")
    print("="*60)
    
    try:
        # 获取电气设备行业指数
        df = pro.index_daily(index_code='801010.SI',
                             start_date='20260201',
                             end_date='20260214')
        print(f"\n返回字段: {df.columns.tolist()}")
        print(f"数据条数: {len(df)}")
        if len(df) > 0:
            print(f"\n数据:")
            print(df)
    except Exception as e:
        print(f"接口调用失败: {e}")
        print("注意: 该接口可能需要特别权限或指数代码不正确")

if __name__ == "__main__":
    print("Tushare API 验证测试")
    print("="*60)
    
    test_stock_basic()
    test_daily_basic()
    test_fina_indicator()
    test_adj_factor()
    test_daily()
    test_moneyflow_hsgt()
    test_moneyflow()
    test_sw_index()
    test_index_daily()
    
    print("\n" + "="*60)
    print("验证完成!")
    print("="*60)
