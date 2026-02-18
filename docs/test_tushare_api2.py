#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试申万行业和指数接口"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import tushare as ts
ts.set_token('82e556132679ef72ee42217682fa809a68c2d32a8d50d0df9b87d0f37384')
pro = ts.pro_api()
pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'

print("="*60)
print("1. 测试 sw_daily (申万日线行情)")
print("="*60)

# 尝试不同的接口名
interfaces_to_try = [
    ('sw_daily', {'index_code': '801010.SI'}),
    ('sw_index', {'level': '1'}),
    ('index_classify', {}),
    ('index_basic', {'market': 'SW'}),
]

for name, params in interfaces_to_try:
    try:
        df = pro.query(name, **params)
        print(f"\n{name}: 成功! 返回 {len(df)} 条")
        print(f"字段: {df.columns.tolist()}")
        if len(df) > 0:
            print(df.head(3))
    except Exception as e:
        print(f"\n{name}: 失败 - {str(e)[:50]}")

print("\n" + "="*60)
print("2. 测试常用指数代码")
print("="*60)

# 尝试常用指数
indices = [
    ('000001.SH', '上证指数'),
    ('399001.SZ', '深证成指'),
    ('000300.SH', '沪深300'),
    ('399006.SZ', '创业板指'),
    ('000016.SH', '上证50'),
    ('000905.SH', '中证500'),
]

for code, name in indices:
    try:
        df = pro.index_daily(ts_code=code, start_date='20260210', end_date='20260214')
        print(f"\n{code} ({name}): 成功! 返回 {len(df)} 条")
        if len(df) > 0:
            print(df[['ts_code', 'trade_date', 'close', 'vol']].tail(2))
    except Exception as e:
        print(f"\n{code} ({name}): 失败 - {str(e)[:50]}")

print("\n" + "="*60)
print("3. 测试 stock_basic 行业字段")
print("="*60)

try:
    df = pro.stock_basic(fields='ts_code,name,industry,list_status')
    print(f"成功! 返回 {len(df)} 条")
    print("行业分布:")
    print(df['industry'].value_counts().head(10))
except Exception as e:
    print(f"失败: {e}")
