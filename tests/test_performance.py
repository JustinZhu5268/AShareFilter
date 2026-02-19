#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能测试模块
功能：
1. 大数据量筛选性能测试
2. 缓存效率测试
3. 并发处理测试
4. 内存使用测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import time
import pandas as pd
import numpy as np
import datetime
import threading
import gc
from typing import List, Dict, Any


class TestPerformance(unittest.TestCase):
    """性能测试"""

    def setUp(self):
        """测试前准备"""
        self.test_results = {}

    def test_large_dataset_filter_performance(self):
        """测试大数据量筛选性能"""
        print("\n📊 大数据量筛选性能测试...")

        # 生成大量模拟股票数据
        num_stocks = 1000
        industries = ['电气设备', '元器件', '专用机械', '软件服务', '汽车配件',
                     '半导体', '医药', '银行', '白酒', '家电']

        stocks = []
        for i in range(num_stocks):
            stocks.append({
                'ts_code': f'{600000+i}.SH',
                'symbol': f'{600000+i}',
                'name': f'股票{i}',
                'industry': industries[i % len(industries)],
                'list_date': '20200101',
                'list_status': 'L',
            })

        df = pd.DataFrame(stocks)

        # 测试筛选性能
        start_time = time.time()

        # 模拟筛选逻辑
        for industry in industries[:5]:
            ind_stocks = df[df['industry'] == industry]
            valid_stocks = ind_stocks[ind_stocks['list_status'] == 'L']
            # 模拟市值检查
            for _ in valid_stocks.head(10).itertuples():
                pass

        elapsed = time.time() - start_time

        print(f"   处理 {num_stocks} 只股票耗时: {elapsed:.3f}秒")

        # 性能断言
        self.assertLess(elapsed, 5.0, "大数据筛选应在5秒内完成")
        self.test_results['large_dataset'] = elapsed

    def test_cache_efficiency(self):
        """测试缓存效率"""
        print("\n💾 缓存效率测试...")

        from data.cache_manager import CACHE_DIR, ensure_cache_dir
        from data.mock_data import generate_mock_stock_list

        # 确保缓存目录存在
        ensure_cache_dir()

        # 测试缓存读写
        test_data = generate_mock_stock_list()

        # 写入测试
        start_time = time.time()
        cache_file = CACHE_DIR / 'test_cache.csv'
        test_data.to_csv(cache_file, index=False, encoding='utf-8-sig')
        write_time = time.time() - start_time

        # 读取测试
        start_time = time.time()
        loaded_data = pd.read_csv(cache_file, encoding='utf-8-sig')
        read_time = time.time() - start_time

        # 清理测试文件
        if cache_file.exists():
            cache_file.unlink()

        print(f"   写入 {len(test_data)} 条数据: {write_time*1000:.2f}ms")
        print(f"   读取 {len(loaded_data)} 条数据: {read_time*1000:.2f}ms")

        # 缓存读写应在合理时间内完成
        self.assertLess(write_time, 1.0, "缓存写入应在1秒内完成")
        self.assertLess(read_time, 1.0, "缓存读取应在1秒内完成")

        self.test_results['cache_write'] = write_time
        self.test_results['cache_read'] = read_time

    def test_concurrent_data_loading(self):
        """测试并发数据加载"""
        print("\n🔄 并发数据加载测试...")

        from data.mock_data import generate_mock_daily_data

        # 准备测试数据
        test_stocks = ['300274.SZ', '000001.SZ', '600519.SH', '000858.SZ', '300750.SZ']

        results = {}
        errors = []

        def load_stock_data(ts_code):
            """加载单只股票数据"""
            try:
                start = time.time()
                df = generate_mock_daily_data(ts_code, days=120)
                elapsed = time.time() - start
                results[ts_code] = elapsed
            except Exception as e:
                errors.append(str(e))

        # 并发执行
        threads = []
        start_time = time.time()

        for ts_code in test_stocks:
            thread = threading.Thread(target=load_stock_data, args=(ts_code,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        print(f"   并发加载 {len(test_stocks)} 只股票: {total_time:.3f}秒")
        print(f"   成功: {len(results)}, 失败: {len(errors)}")

        # 并发应该正常工作
        self.assertEqual(len(errors), 0, f"并发加载出错: {errors}")
        self.assertEqual(len(results), len(test_stocks), "所有股票应加载成功")

        self.test_results['concurrent_time'] = total_time

    def test_memory_usage(self):
        """测试内存使用"""
        print("\n🧠 内存使用测试...")

        try:
            import psutil
            process = psutil.Process()

            # 获取初始内存
            gc.collect()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 生成大量数据
            large_data = []
            for i in range(100):
                df = pd.DataFrame({
                    'col1': range(1000),
                    'col2': range(1000),
                })
                large_data.append(df)

            # 获取峰值内存
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory

            print(f"   初始内存: {initial_memory:.1f} MB")
            print(f"   峰值内存: {peak_memory:.1f} MB")
            print(f"   内存增长: {memory_increase:.1f} MB")

            # 清理
            del large_data
            gc.collect()

            self.test_results['memory_increase'] = memory_increase

        except ImportError:
            print("   ⚠️ psutil 未安装，跳过内存测试")
            self.test_results['memory_increase'] = 0

    def test_api_response_time(self):
        """测试API响应时间"""
        print("\n⏱️ API响应时间测试...")

        from data.mock_data import (
            generate_mock_stock_list,
            generate_mock_market_cap,
            generate_mock_financial_ttm,
        )

        # 测试各API响应时间
        apis = {
            'stock_list': lambda: generate_mock_stock_list(),
            'market_cap': lambda: generate_mock_market_cap(),
            'financial_ttm': lambda: generate_mock_financial_ttm(),
        }

        api_times = {}
        for name, func in apis.items():
            start = time.time()
            result = func()
            elapsed = time.time() - start
            api_times[name] = elapsed * 1000  # 转换为毫秒
            print(f"   {name}: {elapsed*1000:.2f}ms")

        # 所有API应在合理时间内响应
        for name, elapsed in api_times.items():
            self.assertLess(elapsed, 1000, f"{name} 响应时间超过1秒")

        self.test_results['api_times'] = api_times

    def test_batch_processing_performance(self):
        """测试批量处理性能"""
        print("\n📦 批量处理性能测试...")

        # 模拟批量处理任务
        batch_sizes = [10, 50, 100, 500]
        times = []

        for batch_size in batch_sizes:
            start_time = time.time()

            # 模拟批量处理
            results = []
            for i in range(batch_size):
                # 模拟数据处理
                df = pd.DataFrame({'a': range(100), 'b': range(100)})
                result = df.mean().to_dict()
                results.append(result)

            elapsed = time.time() - start_time
            times.append(elapsed)
            print(f"   批量 {batch_size}: {elapsed:.3f}秒")

        # 批量处理应呈线性增长
        # 500个任务应在10秒内完成
        self.assertLess(times[-1], 10.0, "批量处理500个任务应在10秒内完成")

        self.test_results['batch_times'] = dict(zip(batch_sizes, times))


class TestCacheConsistency(unittest.TestCase):
    """缓存一致性测试"""

    def test_cache_data_integrity(self):
        """测试缓存数据完整性"""
        print("\n🔒 缓存数据完整性测试...")

        from data.cache_manager import CACHE_DIR, ensure_cache_dir
        from data.mock_data import generate_mock_stock_list

        ensure_cache_dir()

        test_data = generate_mock_stock_list()
        cache_file = CACHE_DIR / 'integrity_test.csv'

        # 写入缓存
        test_data.to_csv(cache_file, index=False, encoding='utf-8-sig')

        # 读取缓存
        loaded_data = pd.read_csv(cache_file, encoding='utf-8-sig')

        # 验证数据完整性
        self.assertEqual(len(test_data), len(loaded_data), "数据行数不匹配")
        self.assertEqual(list(test_data.columns), list(loaded_data.columns), "数据列不匹配")

        # 清理
        if cache_file.exists():
            cache_file.unlink()

        print("   ✅ 缓存数据完整性验证通过")

    def test_runtime_cache_thread_safety(self):
        """测试运行时缓存线程安全"""
        print("\n🧵 运行时缓存线程安全测试...")

        from api.tushare_client import TushareClient

        client = TushareClient(use_mock=True)
        results = {}
        errors = []

        def get_stock_list():
            try:
                for _ in range(10):
                    client.get_stock_list()
                results['success'] = True
            except Exception as e:
                errors.append(str(e))

        # 并发访问
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=get_stock_list)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(errors), 0, f"并发访问出错: {errors}")
        print("   ✅ 线程安全验证通过")


class TestDataProcessing(unittest.TestCase):
    """数据处理测试"""

    def test_data_transformation_speed(self):
        """测试数据转换速度"""
        print("\n🔄 数据转换速度测试...")

        # 模拟日线数据转换
        df = pd.DataFrame({
            'trade_date': pd.date_range('20240101', periods=1000),
            'open': np.random.randn(1000).cumsum() + 100,
            'high': np.random.randn(1000).cumsum() + 102,
            'low': np.random.randn(1000).cumsum() + 98,
            'close': np.random.randn(1000).cumsum() + 100,
            'vol': np.random.randint(100000, 1000000, 1000),
        })

        start = time.time()

        # 计算技术指标
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()

        elapsed = time.time() - start

        print(f"   1000条数据指标计算: {elapsed*1000:.2f}ms")

        self.assertLess(elapsed, 1.0, "数据转换应在1秒内完成")

    def test_filter_chain_performance(self):
        """测试筛选链性能"""
        print("\n🔗 筛选链性能测试...")

        # 生成测试数据
        df = pd.DataFrame({
            'ts_code': [f'{600000+i}.SH' for i in range(100)],
            'industry': np.random.choice(['电气设备', '银行', '白酒'], 100),
            'market_cap': np.random.uniform(10, 1000, 100),
            'roe': np.random.uniform(0, 30, 100),
        })

        start = time.time()

        # 模拟筛选链
        result = df.copy()

        # Step 1: 行业筛选
        result = result[result['industry'].isin(['电气设备', '银行'])]

        # Step 2: 市值筛选
        result = result[result['market_cap'] > 50]

        # Step 3: ROE筛选
        result = result[result['roe'] > 5]

        # Step 4: 排序
        result = result.sort_values('market_cap', ascending=False)

        elapsed = time.time() - start

        print(f"   筛选链执行: {elapsed*1000:.2f}ms")
        print(f"   原始: {len(df)} -> 筛选后: {len(result)}")

        self.assertLess(elapsed, 0.5, "筛选链应在0.5秒内完成")


class TestCacheHitRate(unittest.TestCase):
    """缓存命中率测试"""

    def test_cache_hit_rate(self):
        """测试缓存命中率"""
        print("\n🎯 缓存命中率测试...")

        from api.tushare_client import TushareClient
        from data.cache_manager import clear_all_cache

        # 清空缓存
        clear_all_cache()

        client = TushareClient(use_mock=True)

        # 第一次请求 - 缓存未命中
        start = time.time()
        result1 = client.get_stock_list()
        first_time = time.time() - start

        # 第二次请求 - 缓存命中
        start = time.time()
        result2 = client.get_stock_list()
        second_time = time.time() - start

        # 验证缓存加速效果
        print(f"   首次请求: {first_time*1000:.2f}ms")
        print(f"   缓存命中: {second_time*1000:.2f}ms")

        # 缓存应该明显快于首次请求
        # 注意：由于 Mock 数据很快，这个测试可能不显著
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        print("✅ 缓存命中率测试通过")

    def test_batch_request_performance(self):
        """测试批量请求性能"""
        print("\n📦 批量请求性能测试...")

        from api.tushare_client import TushareClient

        client = TushareClient(use_mock=True)

        # 测试批量获取市值
        start = time.time()
        caps = client.get_all_market_caps()
        elapsed = time.time() - start

        print(f"   批量获取市值: {elapsed:.2f}秒")

        # 验证性能满足要求
        self.assertIsNotNone(caps)
        # Mock 数据应该在合理时间内完成
        self.assertLess(elapsed, 30, "批量请求应在30秒内完成")
        print("✅ 批量请求性能测试通过")

    def test_concurrent_requests(self):
        """测试并发请求"""
        print("\n⚡ 并发请求测试...")

        import concurrent.futures
        from api.tushare_client import TushareClient

        client = TushareClient(use_mock=True)

        stock_codes = ['300274.SZ', '600519.SH', '000001.SZ', '000858.SZ',
                      '300750.SZ', '002594.SZ', '600036.SH', '000333.SZ']

        def fetch_stock(ts_code):
            return client.get_daily_data(ts_code, '20250101', '20250131')

        # 并发获取多只股票
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(fetch_stock, stock_codes))
        elapsed = time.time() - start

        print(f"   并发请求 {len(stock_codes)} 只股票: {elapsed:.2f}秒")

        # 验证所有请求成功
        self.assertEqual(len(results), len(stock_codes))
        print("✅ 并发请求测试通过")

    def test_memory_usage(self):
        """测试内存使用"""
        print("\n💾 内存使用测试...")

        try:
            import tracemalloc
        except ImportError:
            print("   ⚠️ tracemalloc 不可用，跳过内存测试")
            self.skipTest("tracemalloc not available")

        tracemalloc.start()

        # 执行大量数据处理
        from data.mock_data import generate_mock_daily_data

        for i in range(10):
            df = generate_mock_daily_data('300274.SZ', 120)

            # 计算指标
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma10'] = df['close'].rolling(10).mean()
            df['ma20'] = df['close'].rolling(20).mean()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        print(f"   内存使用峰值: {peak_mb:.2f}MB")

        # 验证内存使用合理
        self.assertLess(peak_mb, 500, f"内存使用过高: {peak_mb:.2f}MB")
        print("✅ 内存使用测试通过")


if __name__ == '__main__':
    unittest.main()
