"""
测试Tushare API - 检查原始数据格式
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

# 测试获取市值 - 只获取最近一天
df = pro.daily_basic(ts_code='300274.SZ', fields='ts_code,total_mv,trade_date')

# 只取最后5条
print("最近5条数据:")
print(df.tail())

print(f"\n最后一条 (最新的):")
latest = df.iloc[-1]
print(f"日期: {latest['trade_date']}")
print(f"total_mv: {latest['total_mv']}")
print(f"转换为亿元: {float(latest['total_mv']) / 10000} 亿")

# 尝试不同的单位转换
print(f"\n尝试不同的转换:")
print(f"除以1000000: {float(latest['total_mv']) / 1000000} 亿")
print(f"除以100000: {float(latest['total_mv']) / 100000} 亿")
