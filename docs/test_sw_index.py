#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试sw_index接口"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import tushare as ts
ts.set_token('82e556132679ef72ee42217682fa809a68c2d32a8d50d0df9b87d0f37384')
pro = ts.pro_api()
pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'

print("="*60)
print("测试sw_index接口 (申万行业)")
print("="*60)

try:
    df = pro.sw_index(level='1', src='SW')
    print(f"成功! 返回 {len(df)} 条")
    print(f"字段: {df.columns.tolist()}")
    print(df.head(10))
except Exception as e:
    print(f"失败: {e}")

print("\n" + "="*60)
print("测试index_daily接口 (行业指数)")
print("="*60)

# 尝试常见的行业指数代码
index_codes = [
    '801010.SI',  # 申万电气设备
    '801730.SI',  # 申万电力设备
    '000300.SH',  # 沪深300
    '399001.SZ',  # 深证成指
]

for code in index_codes:
    try:
        df = pro.index_daily(index_code=code, start_date='20260201', end_date='20260214')
        print(f"\n{code}: 成功! 返回 {len(df)} 条")
        if len(df) > 0:
            print(df.head(2))
    except Exception as e:
        print(f"\n{code}: 失败 - {e}")
