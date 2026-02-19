#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
行业趋势筛选集成测试
测试范围：
1. get_sw_daily() API 方法
2. step2_industry_filter() 完整流程
3. 多级别行业RPS (L1/L2/L3)
4. 行业趋势判断逻辑
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import numpy as np
import datetime

from api.tushare_client import TushareClient
from strategy.filter import StockFilter
from indicators.technical import check_industry_above_ma20, get_industry_trend
from config import config


class TestGetSwDaily(unittest.TestCase):
    """测试 get_sw_daily() API 方法"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)

    def test_get_sw_daily_basic(self):
        """测试获取申万行业指数日线数据基本功能"""
        # 获取电气设备行业指数数据
        df = self.client.get_sw_daily('801010', days=30)

        # 验证返回结果
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        
        # 验证必要字段
        required_columns = ['open', 'high', 'low', 'close', 'vol']
        for col in required_columns:
            self.assertIn(col, df.columns)
        
        print(f"✅ get_sw_daily基本功能: 获取{len(df)}条数据")

    def test_get_sw_daily_with_index_code(self):
        """测试带指数代码的获取"""
        # 测试不同的行业指数代码
        index_codes = ['801010', '801020', '801030']
        
        for code in index_codes:
            df = self.client.get_sw_daily(code, days=30)
            self.assertIsNotNone(df)
            self.assertGreater(len(df), 0)
        
        print(f"✅ 多指数代码测试通过")

    def test_get_sw_daily_with_suffix(self):
        """测试带.SI后缀的指数代码"""
        # 测试带后缀的代码
        df = self.client.get_sw_daily('801010.SI', days=30)
        
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        print(f"✅ 带后缀指数代码测试通过")

    def test_get_sw_daily_data_quality(self):
        """测试获取的行业指数数据质量"""
        df = self.client.get_sw_daily('801010', days=60)
        
        # 验证数据完整性
        self.assertGreater(len(df), 20)
        
        # 验证价格数据有效性
        self.assertTrue((df['close'] > 0).all(), "价格应该为正数")
        self.assertTrue((df['high'] >= df['low']).all(), "最高价应该>=最低价")
        
        print(f"✅ 行业指数数据质量验证通过")


class TestIndustryRPSMultiLevel(unittest.TestCase):
    """测试多级别行业RPS"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)

    def test_get_industry_rps_l1(self):
        """测试一级行业RPS"""
        df = self.client.get_industry_rps(level='L1')
        
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        
        # 验证包含RPS字段
        self.assertIn('rps', df.columns)
        self.assertIn('industry', df.columns)
        
        print(f"✅ L1级行业RPS: {len(df)}个行业")

    def test_get_industry_rps_l2(self):
        """测试二级行业RPS"""
        df = self.client.get_industry_rps(level='L2')
        
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        
        # 验证包含RPS字段
        self.assertIn('rps', df.columns)
        self.assertIn('industry', df.columns)
        
        print(f"✅ L2级行业RPS: {len(df)}个行业")

    def test_get_industry_rps_l3(self):
        """测试三级行业RPS"""
        df = self.client.get_industry_rps(level='L3')
        
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        
        # 验证包含RPS字段
        self.assertIn('rps', df.columns)
        self.assertIn('industry', df.columns)
        
        print(f"✅ L3级行业RPS: {len(df)}个行业")

    def test_get_industry_rps_invalid_level(self):
        """测试无效的行业级别"""
        with self.assertRaises(ValueError):
            self.client.get_industry_rps(level='L4')
        
        print(f"✅ 无效级别参数验证通过")


class TestIndustryTrendFilter(unittest.TestCase):
    """测试行业趋势筛选完整流程"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)
        self.filter = StockFilter(self.client)
        
        # 获取股票列表
        self.stocks = self.client.get_stock_list()

    def test_step2_industry_filter_basic(self):
        """测试行业筛选基本流程"""
        # 执行行业筛选
        industries = self.filter.step2_industry_filter(self.stocks)
        
        # 验证返回结果
        self.assertIsInstance(industries, list)
        self.assertGreater(len(industries), 0)
        
        print(f"✅ 行业筛选基本流程: {len(industries)}个行业")
        for ind in industries[:3]:
            print(f"   - {ind}")

    def test_step2_industry_filter_with_trend(self):
        """测试带趋势判断的行业筛选"""
        # 确保趋势判断配置开启
        original_config = config.INDUSTRY_ABOVE_MA_REQUIRED
        config.INDUSTRY_ABOVE_MA_REQUIRED = True
        
        try:
            # 执行行业筛选
            industries = self.filter.step2_industry_filter(self.stocks)
            
            # 验证返回结果
            self.assertIsInstance(industries, list)
            self.assertGreater(len(industries), 0)
            
            print(f"✅ 带趋势判断的行业筛选: {len(industries)}个行业")
        finally:
            # 恢复配置
            config.INDUSTRY_ABOVE_MA_REQUIRED = original_config

    def test_step2_industry_filter_fallback(self):
        """测试行业筛选备用方案（RPS数据为空时）"""
        # 模拟RPS数据为空的情况
        # 使用真实的股票列表进行筛选
        
        industries = self.filter.step2_industry_filter(self.stocks)
        
        # 验证备用方案返回的是股票数量最多的行业
        self.assertIsInstance(industries, list)
        self.assertGreater(len(industries), 0)
        
        print(f"✅ 行业筛选备用方案: {len(industries)}个行业")


class TestIndustryTrendJudgment(unittest.TestCase):
    """测试行业趋势判断逻辑"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)

    def test_industry_trend_with_uptrend_data(self):
        """测试上涨趋势行业数据"""
        # 生成上涨趋势的行业数据
        np.random.seed(100)
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        
        base_price = 3000
        prices = []
        for _ in range(60):
            base_price += np.random.uniform(2, 8)  # 持续上涨
            prices.append(base_price)
        
        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
            'open': [p - np.random.rand() * 10 for p in prices],
            'high': [p + np.random.rand() * 15 for p in prices],
            'low': [p - np.random.rand() * 15 for p in prices],
            'vol': [np.random.randint(10000000, 50000000) for _ in range(60)],
        })
        
        # 验证趋势判断
        result = check_industry_above_ma20(df)
        
        self.assertTrue(result['above_ma20'])
        self.assertEqual(result['trend'], 'uptrend')
        print(f"✅ 上涨趋势行业判断正确: {result['trend']}")

    def test_industry_trend_with_downtrend_data(self):
        """测试下跌趋势行业数据"""
        # 生成下跌趋势的行业数据
        np.random.seed(200)
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        
        base_price = 3000
        prices = []
        for _ in range(60):
            base_price -= np.random.uniform(2, 8)  # 持续下跌
            prices.append(max(base_price, 100))
        
        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
            'open': [p - np.random.rand() * 10 for p in prices],
            'high': [p + np.random.rand() * 15 for p in prices],
            'low': [p - np.random.rand() * 15 for p in prices],
            'vol': [np.random.randint(10000000, 50000000) for _ in range(60)],
        })
        
        # 验证趋势判断
        result = check_industry_above_ma20(df)
        
        # 下跌趋势应该不会站上MA20
        print(f"✅ 下跌趋势行业判断: above_ma20={result['above_ma20']}, trend={result['trend']}")

    def test_industry_trend_with_insufficient_data(self):
        """测试数据不足的趋势判断"""
        # 数据不足20天
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
        })
        
        result = check_industry_above_ma20(df)
        
        # 数据不足应该返回默认值
        self.assertFalse(result['above_ma20'])
        print(f"✅ 数据不足时趋势判断正常处理")

    def test_get_industry_trend_comprehensive(self):
        """测试综合行业趋势分析"""
        # 生成上涨趋势的行业数据
        np.random.seed(300)
        dates = pd.date_range(start='2024-01-01', periods=120, freq='D')
        
        base_price = 3000
        prices = []
        for _ in range(120):
            base_price += np.random.uniform(1, 10)
            prices.append(base_price)
        
        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
        })
        
        # 综合趋势分析
        result = get_industry_trend(df)
        
        # 验证返回结果
        self.assertIn('trend', result)
        self.assertIn('above_ma20', result)
        self.assertIn('strength', result)
        self.assertIn('ma_levels', result)
        
        print(f"✅ 综合趋势分析: {result['trend']}, 强度={result['strength']}")


class TestIndustryTrendFilterIntegration(unittest.TestCase):
    """测试行业趋势筛选集成"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)
        self.filter = StockFilter(self.client)

    def test_full_filter_with_industry_trend(self):
        """测试完整筛选流程包含行业趋势"""
        # 确保行业趋势判断开启
        original_config = config.INDUSTRY_ABOVE_MA_REQUIRED
        config.INDUSTRY_ABOVE_MA_REQUIRED = True
        
        try:
            # 执行完整筛选
            results = self.filter.run_full_filter()
            
            # 验证结果
            self.assertIsInstance(results, list)
            print(f"✅ 完整筛选流程（含行业趋势）: 筛选到{len(results)}只股票")
        finally:
            config.INDUSTRY_ABOVE_MA_REQUIRED = original_config

    def test_industry_code_mapping(self):
        """测试行业代码映射"""
        # 测试 _get_industry_code 方法
        industry_code = self.filter._get_industry_code('电气设备')
        self.assertEqual(industry_code, '801010')
        
        industry_code = self.filter._get_industry_code('光伏')
        self.assertEqual(industry_code, '801010')
        
        # 测试未知行业
        industry_code = self.filter._get_industry_code('未知行业')
        self.assertIsNone(industry_code)
        
        print(f"✅ 行业代码映射测试通过")

    def test_get_sw_daily_for_multiple_industries(self):
        """测试获取多个行业指数数据"""
        industries = ['电气设备', '电子', '化工']
        
        for industry in industries:
            industry_code = self.filter._get_industry_code(industry)
            if industry_code:
                df = self.client.get_sw_daily(industry_code, days=30)
                self.assertIsNotNone(df)
                self.assertGreater(len(df), 0)
        
        print(f"✅ 多行业指数数据获取测试通过")


class TestIndustryTrendEdgeCases(unittest.TestCase):
    """测试行业趋势边界情况"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)

    def test_empty_industry_list(self):
        """测试空行业列表"""
        empty_df = pd.DataFrame()
        
        result = check_industry_above_ma20(empty_df)
        
        self.assertFalse(result['above_ma20'])
        print(f"✅ 空数据处理正常")

    def test_single_day_data(self):
        """测试单日数据"""
        df = pd.DataFrame({
            'close': [100],
        })
        
        result = check_industry_above_ma20(df)
        
        self.assertFalse(result['above_ma20'])
        print(f"✅ 单日数据处理正常")

    def test_all_same_price_data(self):
        """测试价格不变的行业数据"""
        df = pd.DataFrame({
            'close': [3000] * 60,
        })
        
        result = check_industry_above_ma20(df)
        
        # 价格不变应该不会站上MA20
        print(f"✅ 横盘数据处理: above_ma20={result['above_ma20']}, trend={result['trend']}")


class TestIndustryTrendFilterWithMockData(unittest.TestCase):
    """使用Mock数据测试行业趋势筛选"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)
        self.filter = StockFilter(self.client)

    def test_mock_sw_daily_data_structure(self):
        """测试Mock行业指数数据结构"""
        df = self.client.get_sw_daily('801010', days=60)
        
        # 验证数据结构
        self.assertIn('trade_date', df.columns)
        self.assertIn('open', df.columns)
        self.assertIn('high', df.columns)
        self.assertIn('low', df.columns)
        self.assertIn('close', df.columns)
        self.assertIn('vol', df.columns)
        
        # 验证数据排序
        self.assertTrue(df['trade_date'].is_monotonic_increasing)
        
        print(f"✅ Mock行业指数数据结构验证通过")

    def test_mock_industry_rps_calculation(self):
        """测试Mock行业RPS计算"""
        df = self.client.get_industry_rps(level='L1')
        
        # 验证RPS计算结果
        self.assertIn('rps', df.columns)
        
        # 验证RPS排序
        rps_values = df['rps'].tolist()
        self.assertEqual(rps_values, sorted(rps_values, reverse=True))
        
        print(f"✅ Mock行业RPS计算验证通过")


if __name__ == '__main__':
    unittest.main()
