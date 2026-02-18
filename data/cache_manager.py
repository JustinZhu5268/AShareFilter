"""
缓存管理器 - 长效数据本地缓存系统
功能：
1. 市值数据缓存 (7天有效期)
2. 财务TTM数据缓存 (90天有效期)
3. 股票列表缓存 (1天有效期)
4. 复权因子缓存 (30天有效期)
5. 行业RPS缓存 (1天有效期)
"""

import os
import pandas as pd
import datetime
import warnings
import json
from pathlib import Path

warnings.filterwarnings('ignore')

# 缓存目录
CACHE_DIR = Path(__file__).parent.parent / "data_cache"

# 缓存有效期 (天)
CACHE_EXPIRY = {
    'market_cap': 7,
    'financial_ttm': 90,
    'stock_list': 1,
    'adj_factor': 30,
    'industry_rps': 1,
    'daily_data': 1,
}


def ensure_cache_dir():
    """确保缓存目录存在"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cache_path(cache_name: str) -> Path:
    """获取缓存文件路径"""
    ensure_cache_dir()
    return CACHE_DIR / f"{cache_name}.csv"


def is_cache_valid(cache_name: str, max_age_days: int = None) -> bool:
    """检查缓存是否有效"""
    if max_age_days is None:
        max_age_days = CACHE_EXPIRY.get(cache_name, 7)

    cache_path = get_cache_path(cache_name)
    if not cache_path.exists():
        return False

    # 检查文件修改时间
    file_mtime = datetime.datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.datetime.now() - file_mtime

    return age.days < max_age_days


def load_cache(cache_name: str) -> pd.DataFrame | None:
    """加载缓存数据"""
    cache_path = get_cache_path(cache_name)
    if cache_path.exists():
        try:
            df = pd.read_csv(cache_path, encoding='utf-8-sig')
            return df
        except Exception as e:
            print(f"    [缓存] 加载失败 {cache_name}: {e}")
    return None


def save_cache(cache_name: str, df: pd.DataFrame | None):
    """保存缓存数据"""
    if df is None or df.empty:
        return

    cache_path = get_cache_path(cache_name)
    try:
        df.to_csv(cache_path, index=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"    [缓存] 保存失败 {cache_name}: {e}")


def get_cache_age(cache_name: str) -> int | None:
    """获取缓存年龄(天)"""
    cache_path = get_cache_path(cache_name)
    if not cache_path.exists():
        return None

    file_mtime = datetime.datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.datetime.now() - file_mtime
    return age.days


# ==========================================
# 特定缓存操作
# ==========================================

def load_market_cap_cache() -> pd.DataFrame | None:
    """加载市值缓存"""
    return load_cache('market_cap')


def save_market_cap_cache(df: pd.DataFrame | None):
    """保存市值缓存"""
    save_cache('market_cap', df)


def load_financial_ttm_cache() -> pd.DataFrame | None:
    """加载财务TTM缓存"""
    return load_cache('financial_ttm')


def save_financial_ttm_cache(df: pd.DataFrame | None):
    """保存财务TTM缓存"""
    save_cache('financial_ttm', df)


def load_stock_list_cache() -> pd.DataFrame | None:
    """加载股票列表缓存"""
    return load_cache('stock_list')


def save_stock_list_cache(df: pd.DataFrame | None):
    """保存股票列表缓存"""
    save_cache('stock_list', df)


def load_adj_factor_cache() -> pd.DataFrame | None:
    """加载复权因子缓存"""
    return load_cache('adj_factor')


def save_adj_factor_cache(df: pd.DataFrame | None):
    """保存复权因子缓存"""
    save_cache('adj_factor', df)


def load_industry_rps_cache() -> pd.DataFrame | None:
    """加载行业RPS缓存"""
    return load_cache('industry_rps')


def save_industry_rps_cache(df: pd.DataFrame | None):
    """保存行业RPS缓存"""
    save_cache('industry_rps', df)


def load_daily_cache(ts_code: str) -> pd.DataFrame | None:
    """加载日线数据缓存"""
    cache_name = f"daily_{ts_code.replace('.', '_')}"
    return load_cache(cache_name)


def save_daily_cache(ts_code: str, df: pd.DataFrame | None):
    """保存日线数据缓存"""
    cache_name = f"daily_{ts_code.replace('.', '_')}"
    save_cache(cache_name, df)


def clear_all_cache():
    """清空所有缓存"""
    ensure_cache_dir()
    for file in CACHE_DIR.glob("*.csv"):
        file.unlink()
    print("[缓存] 已清空所有缓存")


def clear_cache_by_name(cache_name: str):
    """清空指定缓存"""
    cache_path = get_cache_path(cache_name)
    if cache_path.exists():
        cache_path.unlink()
        print(f"[缓存] 已清空 {cache_name}")


def print_cache_status():
    """打印缓存状态"""
    try:
        ensure_cache_dir()
        print("[Cache Status]")
    except (ValueError, IOError):
        # stdout可能已关闭，忽略
        pass

    files = list(CACHE_DIR.glob("*.csv"))
    if not files:
        print("  (no cache files)")
        return

    for file in files:
        cache_name = file.stem
        mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
        age = (datetime.datetime.now() - mtime).days
        max_age = CACHE_EXPIRY.get(cache_name, 7)
        status = "OK" if age < max_age else "EXPIRED"
        print(f"  {file.name}: {age}days {status}")


if __name__ == "__main__":
    print_cache_status()
