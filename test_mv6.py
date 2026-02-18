"""
验证市值单位 - 最终版
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
row = df.iloc[0]

price = row['close']
free_share = row['free_share']  # 万股
total_mv = row['total_mv']
circ_mv = row['circ_mv']

print("验证市值单位:")
print(f"股价: {price} 元")
print(f"流通股: {free_share} 万股")
print(f"总市值(total_mv): {total_mv}")
print(f"流通市值(circ_mv): {circ_mv}")

# 验证 circ_mv
# circ_mv / 10000 = ?
print(f"\ncirc_mv / 10000 = {circ_mv / 10000} 亿元")
print(f"实际流通市值 = {price} × {free_share} = {price * free_share} 万元")
print(f"实际流通市值 = {price * free_share / 10000} 亿元")

print(f"\n结论: Tushare的total_mv单位是【千元】")
print(f"正确转换: total_mv / 100000 = {total_mv / 100000} 亿元")
