"""
深入测试市值数据 - 验证单位
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

# 只获取最近一天的数据
df = pro.daily_basic(ts_code='300274.SZ', start_date='20260213', end_date='20260213')
print("2026-02-13的数据:")
row = df.iloc[0]
print(f"收盘价: {row['close']}")
print(f"流通股(万股): {row['free_share']}")
print(f"总市值: {row['total_mv']}")
print(f"流通市值: {row['circ_mv']}")

# 验证单位
price = row['close']
free_share = row['free_share']  # 万股
total_mv = row['total_mv']

# 计算：股价 × 流通股数
calculated = price * free_share * 10000  # 转换为股
print(f"\n验证计算:")
print(f"股价 × 流通股 = {price} × {free_share} × 10000 = {calculated}")

# 看看total_mv和这个值的关系
print(f"\ntotal_mv / calculated = {total_mv / calculated}")
print(f"total_mv / 100000000 = {total_mv / 100000000}")
print(f"total_mv / 10000 = {total_mv / 10000}")
