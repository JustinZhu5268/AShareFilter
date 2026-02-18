"""
测试Tushare API返回的市值数据 - 调试版
"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import tushare as ts

TUSHARE_TOKEN = "82e556132679ef72ee42217682fa809a68c2d32a8d50d0df9b87d0f37384"
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
pro._DataApi__token = TUSHARE_TOKEN
pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'

# 测试获取市值
df = pro.daily_basic(ts_code='300274.SZ', fields='ts_code,total_mv,trade_date')

print("原始数据 (前5行):")
print(df.head())

print("\n按trade_date排序后:")
df = df.sort_values('trade_date', ascending=False)
print(df.head())

print(f"\n最新一条 (iloc[-1]):")
print(f"total_mv: {df.iloc[-1]['total_mv']}")
print(f"转换为亿元: {float(df.iloc[-1]['total_mv']) / 10000} 亿")

print(f"\n第一行 (iloc[0]):")
print(f"total_mv: {df.iloc[0]['total_mv']}")
print(f"转换为亿元: {float(df.iloc[0]['total_mv']) / 10000} 亿")
