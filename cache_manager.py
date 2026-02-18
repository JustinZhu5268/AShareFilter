"""
缓存管理器 - 长效数据本地缓存系统
功能：
1. 市值数据缓存 (7天有效期)
2. 财务TTM数据缓存 (90天有效期)
3. 股票列表缓存 (1天有效期)
"""

import os
import pandas as pd
import datetime
import warnings
warnings.filterwarnings('ignore')

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data_cache')

# 缓存有效期 (天)
CACHE_EXPIRY = {
    'market_cap': 7,      # 市值7天
    'financial_ttm': 90,  # 财务90天
    'stock_list': 1,      # 股票列表1天
    'adj_factor': 30,    # 复权因子30天
}

def ensure_cache_dir():
    """确保缓存目录存在"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_path(cache_name):
    """获取缓存文件路径"""
    ensure_cache_dir()
    return os.path.join(CACHE_DIR, f"{cache_name}.csv")

def is_cache_valid(cache_name, max_age_days=None):
    """检查缓存是否有效"""
    if max_age_days is None:
        max_age_days = CACHE_EXPIRY.get(cache_name, 7)
    
    cache_path = get_cache_path(cache_name)
    if not os.path.exists(cache_path):
        return False
    
    # 检查文件修改时间
    file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(cache_path))
    age = datetime.datetime.now() - file_mtime
    
    return age.days < max_age_days

def load_cache(cache_name):
    """加载缓存数据"""
    cache_path = get_cache_path(cache_name)
    if os.path.exists(cache_path):
        try:
            df = pd.read_csv(cache_path, encoding='utf-8-sig')
            print(f"    [缓存] 加载 {cache_name}: {len(df)} 条记录")
            return df
        except Exception as e:
            print(f"    [缓存] 加载失败 {cache_name}: {e}")
    return None

def save_cache(cache_name, df):
    """保存缓存数据"""
    if df is None or df.empty:
        return
    
    cache_path = get_cache_path(cache_name)
    try:
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')
        print(f"    [缓存] 保存 {cache_name}: {len(df)} 条记录")
    except Exception as e:
        print(f"    [缓存] 保存失败 {cache_name}: {e}")

def get_cache_age(cache_name):
    """获取缓存年龄(天)"""
    cache_path = get_cache_path(cache_name)
    if not os.path.exists(cache_path):
        return None
    
    file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(cache_path))
    age = datetime.datetime.now() - file_mtime
    return age.days

# ==========================================
# 特定缓存操作
# ==========================================

def load_market_cap_cache():
    """加载市值缓存"""
    return load_cache('market_cap')

def save_market_cap_cache(df):
    """保存市值缓存"""
    save_cache('market_cap', df)

def load_financial_ttm_cache():
    """加载财务TTM缓存"""
    return load_cache('financial_ttm')

def save_financial_ttm_cache(df):
    """保存财务TTM缓存"""
    save_cache('financial_ttm', df)

def load_stock_list_cache():
    """加载股票列表缓存"""
    return load_cache('stock_list')

def save_stock_list_cache(df):
    """保存股票列表缓存"""
    save_cache('stock_list', df)

def load_adj_factor_cache():
    """加载复权因子缓存"""
    return load_cache('adj_factor')

def save_adj_factor_cache(df):
    """保存复权因子缓存"""
    save_cache('adj_factor', df)

def clear_all_cache():
    """清空所有缓存"""
    ensure_cache_dir()
    for file in os.listdir(CACHE_DIR):
        if file.endswith('.csv'):
            os.remove(os.path.join(CACHE_DIR, file))
    print("[缓存] 已清空所有缓存")

def print_cache_status():
    """打印缓存状态"""
    ensure_cache_dir()
    print("\n📁 缓存状态:")
    
    files = os.listdir(CACHE_DIR)
    if not files:
        print("  (无缓存文件)")
        return
    
    for file in files:
        if file.endswith('.csv'):
            path = os.path.join(CACHE_DIR, file)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            age = (datetime.datetime.now() - mtime).days
            max_age = CACHE_EXPIRY.get(file.replace('.csv', ''), 7)
            status = "✅" if age < max_age else "❌过期"
            print(f"  {file}: {age}天 {status}")

if __name__ == "__main__":
    print_cache_status()
