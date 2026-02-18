"""
缓存管理模块单元测试
"""
import unittest
import pandas as pd
import numpy as np
import datetime
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 临时替换缓存目录
from pathlib import Path
import data.cache_manager as cache_mgr


class TestCacheManager(unittest.TestCase):
    """缓存管理测试类"""
    
    def setUp(self):
        """创建临时缓存目录"""
        self.test_cache_dir = Path(tempfile.mkdtemp())
        self.original_cache_dir = cache_mgr.CACHE_DIR
        
        # 临时替换缓存目录
        cache_mgr.CACHE_DIR = self.test_cache_dir
        cache_mgr.ensure_cache_dir()
    
    def tearDown(self):
        """清理临时缓存目录"""
        cache_mgr.CACHE_DIR = self.original_cache_dir
        shutil.rmtree(self.test_cache_dir, ignore_errors=True)
    
    def test_ensure_cache_dir(self):
        """测试缓存目录创建"""
        self.assertTrue(self.test_cache_dir.exists())
        self.assertTrue(self.test_cache_dir.is_dir())
    
    def test_get_cache_path(self):
        """测试缓存路径获取"""
        path = cache_mgr.get_cache_path('test_cache')
        self.assertEqual(path.name, 'test_cache.csv')
        self.assertEqual(path.parent, self.test_cache_dir)
    
    def test_save_and_load_cache(self):
        """测试缓存保存和加载"""
        # 创建测试数据
        test_data = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c'],
        })
        
        # 保存缓存
        cache_mgr.save_cache('test_data', test_data)
        
        # 加载缓存
        loaded_data = cache_mgr.load_cache('test_data')
        
        # 验证
        self.assertFalse(loaded_data.empty)
        self.assertEqual(len(loaded_data), 3)
        self.assertListEqual(list(loaded_data.columns), ['col1', 'col2'])
    
    def test_cache_expiry(self):
        """测试缓存过期"""
        # 创建过期的缓存文件
        old_date = datetime.datetime.now() - datetime.timedelta(days=10)
        cache_path = self.test_cache_dir / 'old_cache.csv'
        
        df = pd.DataFrame({'a': [1, 2, 3]})
        df.to_csv(cache_path, index=False)
        
        # 修改文件时间戳
        os.utime(cache_path, (old_date.timestamp(), old_date.timestamp()))
        
        # 检查缓存是否过期
        is_valid = cache_mgr.is_cache_valid('old_cache', max_age_days=7)
        self.assertFalse(is_valid)
    
    def test_cache_valid(self):
        """测试有效缓存"""
        # 创建新的缓存文件
        cache_mgr.save_cache('fresh_cache', pd.DataFrame({'a': [1]}))
        
        # 检查缓存是否有效
        is_valid = cache_mgr.is_cache_valid('fresh_cache', max_age_days=1)
        self.assertTrue(is_valid)
    
    def test_nonexistent_cache(self):
        """测试不存在的缓存"""
        data = cache_mgr.load_cache('nonexistent_cache')
        self.assertIsNone(data)
    
    def test_market_cap_cache(self):
        """测试市值缓存"""
        test_data = pd.DataFrame({
            'ts_code': ['300274.SZ'],
            'total_mv': [3000000],
        })
        
        cache_mgr.save_market_cap_cache(test_data)
        loaded = cache_mgr.load_market_cap_cache()
        
        self.assertFalse(loaded.empty)
    
    def test_stock_list_cache(self):
        """测试股票列表缓存"""
        test_data = pd.DataFrame({
            'ts_code': ['300274.SZ', '000001.SZ'],
            'name': ['阳光电源', '平安银行'],
        })
        
        cache_mgr.save_stock_list_cache(test_data)
        loaded = cache_mgr.load_stock_list_cache()
        
        self.assertFalse(loaded.empty)
    
    def test_financial_ttm_cache(self):
        """测试财务TTM缓存"""
        test_data = pd.DataFrame({
            'ts_code': ['300274.SZ'],
            'roe': [25.5],
        })
        
        cache_mgr.save_financial_ttm_cache(test_data)
        loaded = cache_mgr.load_financial_ttm_cache()
        
        self.assertFalse(loaded.empty)
    
    def test_adj_factor_cache(self):
        """测试复权因子缓存"""
        test_data = pd.DataFrame({
            'ts_code': ['300274.SZ'],
            'adj_factor': [1.5],
        })
        
        cache_mgr.save_adj_factor_cache(test_data)
        loaded = cache_mgr.load_adj_factor_cache()
        
        self.assertFalse(loaded.empty)
    
    def test_daily_cache(self):
        """测试日线数据缓存"""
        test_data = pd.DataFrame({
            'ts_code': ['300274.SZ'],
            'close': [150.0],
        })
        
        cache_mgr.save_daily_cache('300274.SZ', test_data)
        loaded = cache_mgr.load_daily_cache('300274.SZ')
        
        self.assertFalse(loaded.empty)
    
    def test_industry_rps_cache(self):
        """测试行业RPS缓存"""
        test_data = pd.DataFrame({
            'industry': ['电气设备'],
            'rps': [8.5],
        })
        
        cache_mgr.save_industry_rps_cache(test_data)
        loaded = cache_mgr.load_industry_rps_cache()
        
        self.assertFalse(loaded.empty)


class TestCacheEdgeCases(unittest.TestCase):
    """缓存管理边界测试类"""
    
    def setUp(self):
        """创建临时缓存目录"""
        self.test_cache_dir = Path(tempfile.mkdtemp())
        self.original_cache_dir = cache_mgr.CACHE_DIR
        cache_mgr.CACHE_DIR = self.test_cache_dir
    
    def tearDown(self):
        """清理临时缓存目录"""
        cache_mgr.CACHE_DIR = self.original_cache_dir
        shutil.rmtree(self.test_cache_dir, ignore_errors=True)
    
    def test_save_empty_dataframe(self):
        """测试保存空DataFrame"""
        df = pd.DataFrame()
        cache_mgr.save_cache('empty_cache', df)
        
        # 加载空缓存应该返回None
        loaded = cache_mgr.load_cache('empty_cache')
        # 空DataFrame应该被处理
    
    def test_save_corrupted_cache(self):
        """测试保存损坏的缓存"""
        cache_path = self.test_cache_dir / 'corrupted.csv'
        with open(cache_path, 'w') as f:
            f.write('invalid csv content')
        
        # 加载损坏的缓存应该返回None或抛出异常
        try:
            loaded = cache_mgr.load_cache('corrupted')
        except:
            pass
    
    def test_concurrent_access(self):
        """测试并发访问 - 使用线程锁保护"""
        import threading
        
        results = []
        errors = []
        
        def save_load():
            try:
                for i in range(10):
                    cache_mgr.save_cache('thread_cache', pd.DataFrame({'val': [i]}))
                    loaded = cache_mgr.load_cache('thread_cache')
                    results.append(loaded is not None and not loaded.empty)
            except Exception as e:
                errors.append(str(e))
        
        threads = [threading.Thread(target=save_load) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 所有操作应该成功，没有错误
        self.assertEqual(len(errors), 0, f"并发错误: {errors}")
        self.assertTrue(len(results) > 0)
        print(f"✅ 并发测试通过: {len(results)} 次操作")


if __name__ == '__main__':
    unittest.main()
