"""
测试Tushare API返回的市值数据
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
df = pro.daily_basic(ts_code='300274.SZ', fields='ts_code,total_mv')
print("API返回的市值数据:")
print(df)
print(f"\ntotal_mv类型: {df['total_mv'].dtype}")
print(f"total_mv值: {df['total_mv'].iloc[0]}")
print(f"转换为亿元: {float(df['total_mv'].iloc[0]) / 10000} 亿")
