#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
行业趋势判断单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import numpy as np
from indicators.technical import (
    check_industry_above_ma20,
    get_industry_trend,
    check_industry_momentum,
)


class TestIndustryTrend(unittest.TestCase):
    """行业趋势判断测试"""

    def setUp(self):
        """测试前准备 - 生成模拟行业指数数据"""
        # 生成120天的模拟行业指数数据
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=120, freq='D')

        # 创建上涨趋势的数据
        base_price = 3000
        prices = []
        for i in range(120):
            # 上涨趋势
            change = np.random.randn() * 30 + 5
            base_price = base_price + change
            prices.append(base_price)

        self.industry_df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
            'open': [p - np.random.rand() * 20 for p in prices],
            'high': [p + np.random.rand() * 30 for p in prices],
            'low': [p - np.random.rand() * 30 for p in prices],
            'vol': [np.random.randint(10000000, 100000000) for _ in range(120)],
        })

    def test_check_industry_above_ma20(self):
        """测试行业指数是否站上20日均线"""
        result = check_industry_above_ma20(self.industry_df)

        self.assertIn('above_ma20', result)
        self.assertIn('close', result)
        self.assertIn('ma20', result)
        self.assertIn('distance', result)
        self.assertIn('trend', result)

        print(f"✅ 行业站上20日均线: above={result['above_ma20']}, trend={result['trend']}")

    def test_check_industry_above_ma20_downtrend(self):
        """测试下跌趋势的行业"""
        # 创建下跌趋势的数据
        np.random.seed(123)
        base_price = 3000
        prices = []
        for i in range(120):
            change = np.random.randn() * 30 - 5
            base_price = base_price + change
            prices.append(max(base_price, 100))

        df_down = pd.DataFrame({
            'trade_date': pd.date_range(start='2024-01-01', periods=120, freq='D'),
            'close': prices,
        })

        result = check_industry_above_ma20(df_down)

        print(f"✅ 下跌趋势行业: above={result['above_ma20']}, trend={result['trend']}")

    def test_check_industry_above_ma20_insufficient_data(self):
        """测试数据不足的情况"""
        # 数据不足20天
        df_short = self.industry_df.head(10)

        result = check_industry_above_ma20(df_short)

        self.assertFalse(result['above_ma20'])
        print(f"✅ 数据不足时返回False")

    def test_check_industry_above_ma20_empty_data(self):
        """测试空数据"""
        df_empty = pd.DataFrame()

        result = check_industry_above_ma20(df_empty)

        self.assertFalse(result['above_ma20'])
        self.assertEqual(result['trend'], 'sideways')
        print(f"✅ 空数据返回sideways")

    def test_get_industry_trend(self):
        """测试行业趋势综合分析"""
        result = get_industry_trend(self.industry_df)

        self.assertIn('trend', result)
        self.assertIn('above_ma20', result)
        self.assertIn('above_ma60', result)
        self.assertIn('strength', result)
        self.assertIn('ma_levels', result)

        print(f"✅ 行业趋势: {result['trend']}, 强度={result['strength']}")

    def test_get_industry_trend_custom_periods(self):
        """测试自定义均线周期"""
        result = get_industry_trend(self.industry_df, ma_periods=[5, 10, 20])

        self.assertIn('ma_levels', result)
        self.assertIn('ma5', result['ma_levels'])
        self.assertIn('ma10', result['ma_levels'])
        self.assertIn('ma20', result['ma_levels'])
        print(f"✅ 自定义周期测试通过")

    def test_check_industry_momentum(self):
        """测试行业动量"""
        result = check_industry_momentum(self.industry_df)

        self.assertIn('short_term', result)
        self.assertIn('mid_term', result)
        self.assertIn('long_term', result)
        self.assertIn('momentum_score', result)

        print(f"✅ 行业动量: short={result['short_term']}, mid={result['mid_term']}, long={result['long_term']}, score={result['momentum_score']}")

    def test_check_industry_momentum_insufficient_data(self):
        """测试数据不足时的动量"""
        df_short = self.industry_df.head(10)

        result = check_industry_momentum(df_short)

        self.assertIn('momentum_score', result)
        print(f"✅ 动量计算处理数据不足")

    def test_industry_trend_sideways(self):
        """测试横盘趋势"""
        # 创建横盘数据
        np.random.seed(999)
        prices = [3000 + np.random.randn() * 50 for _ in range(120)]

        df_sideways = pd.DataFrame({
            'trade_date': pd.date_range(start='2024-01-01', periods=120, freq='D'),
            'close': prices,
        })

        result = get_industry_trend(df_sideways)

        print(f"✅ 横盘趋势: {result['trend']}, strength={result['strength']}")


class TestIndustryTrendEdgeCases(unittest.TestCase):
    """行业趋势边界测试"""

    def test_zero_prices(self):
        """测试零值价格"""
        df = pd.DataFrame({
            'close': [0, 0, 0],
            'open': [0, 0, 0],
            'high': [0, 0, 0],
            'low': [0, 0, 0],
        })

        result = check_industry_above_ma20(df)

        self.assertIn('trend', result)
        print(f"✅ 零值处理正常")

    def test_negative_prices(self):
        """测试负值价格"""
        df = pd.DataFrame({
            'close': [-100, -99, -98],
            'open': [-100, -99, -98],
            'high': [-99, -98, -97],
            'low': [-101, -100, -99],
        })

        result = check_industry_above_ma20(df)

        self.assertIn('trend', result)
        print(f"✅ 负值处理正常")

    def test_single_row(self):
        """测试单行数据"""
        df = pd.DataFrame({
            'close': [3000],
        })

        result = check_industry_above_ma20(df)

        # 数据不足应该返回默认值
        self.assertFalse(result['above_ma20'])
        print(f"✅ 单行数据处理正常")


class TestIndustryTrendIntegration(unittest.TestCase):
    """行业趋势集成测试"""

    def setUp(self):
        """测试前准备 - 生成模拟行业指数数据"""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=120, freq='D')

        # 创建上涨趋势的数据
        base_price = 3000
        prices = []
        for i in range(120):
            change = np.random.randn() * 30 + 5
            base_price = base_price + change
            prices.append(base_price)

        self.industry_df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
            'open': [p - np.random.rand() * 20 for p in prices],
            'high': [p + np.random.rand() * 30 for p in prices],
            'low': [p - np.random.rand() * 30 for p in prices],
            'vol': [np.random.randint(10000000, 100000000) for _ in range(120)],
        })

    def test_industry_trend_multi_ma_levels(self):
        """测试多周期均线分析"""
        result = get_industry_trend(self.industry_df, ma_periods=[5, 10, 20, 60, 120])

        # 验证多周期均线数据
        self.assertIn('ma5', result['ma_levels'])
        self.assertIn('ma10', result['ma_levels'])
        self.assertIn('ma20', result['ma_levels'])
        self.assertIn('ma60', result['ma_levels'])
        self.assertIn('ma120', result['ma_levels'])

        print(f"✅ 多周期均线: {result['ma_levels'].keys()}")

    def test_industry_momentum_comprehensive(self):
        """测试综合动量分析"""
        # 测试不同周期的动量
        result = check_industry_momentum(self.industry_df, periods=[5, 10, 20, 60])

        # 验证所有周期 - 返回的是 short_term, mid_term, long_term
        self.assertIn('short_term', result)
        self.assertIn('mid_term', result)
        self.assertIn('long_term', result)

        # 验证动量得分
        self.assertIn('momentum_score', result)
        self.assertGreaterEqual(result['momentum_score'], 0)
        self.assertLessEqual(result['momentum_score'], 100)

        print(f"✅ 综合动量: score={result['momentum_score']}")

    def test_industry_trend_with_insufficient_ma_periods(self):
        """测试均线周期不足的情况"""
        # 只提供部分均线周期
        result = get_industry_trend(self.industry_df, ma_periods=[5, 10])

        # 应该返回部分数据
        self.assertIn('ma_levels', result)
        self.assertIn('ma5', result['ma_levels'])
        self.assertIn('ma10', result['ma_levels'])

        print(f"✅ 周期不足测试通过")

    def test_industry_above_ma20_distance_calculation(self):
        """测试距离MA20计算"""
        result = check_industry_above_ma20(self.industry_df)

        # 验证距离计算
        self.assertIn('distance', result)
        self.assertIsInstance(result['distance'], float)

        # 距离应该在合理范围内
        if result['above_ma20']:
            self.assertGreater(result['distance'], 0)
        else:
            self.assertLess(result['distance'], 0)

        print(f"✅ 距离计算: {result['distance']:.2%}")

    def test_industry_momentum_edge_cases(self):
        """测试动量边界情况"""
        # 测试非常小的数据
        df_small = pd.DataFrame({'close': [100, 101, 102]})
        result = check_industry_momentum(df_small)

        self.assertIn('momentum_score', result)
        print(f"✅ 小数据集动量: {result['momentum_score']}")


class TestIndustryTrendRealWorld(unittest.TestCase):
    """行业趋势真实场景测试"""

    def test_uptrend_industry(self):
        """测试上涨趋势行业"""
        # 模拟持续上涨的行业
        np.random.seed(100)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

        base = 3000
        prices = []
        for _ in range(100):
            base += np.random.uniform(5, 15)  # 持续上涨
            prices.append(base)

        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
        })

        result = get_industry_trend(df)

        self.assertEqual(result['trend'], 'uptrend')
        self.assertTrue(result['above_ma20'])
        self.assertGreater(result['strength'], 50)

        print(f"✅ 上涨趋势行业: trend={result['trend']}, strength={result['strength']}")

    def test_downtrend_industry(self):
        """测试下跌趋势行业"""
        # 模拟持续下跌的行业
        np.random.seed(200)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

        base = 3000
        prices = []
        for _ in range(100):
            base -= np.random.uniform(5, 15)  # 持续下跌
            prices.append(max(base, 100))  # 防止负值

        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
        })

        result = get_industry_trend(df)

        self.assertEqual(result['trend'], 'downtrend')
        self.assertLess(result['strength'], 50)

        print(f"✅ 下跌趋势行业: trend={result['trend']}, strength={result['strength']}")

    def test_volatile_industry(self):
        """测试震荡行业"""
        # 模拟震荡的行情
        np.random.seed(300)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

        base = 3000
        prices = []
        for i in range(100):
            change = np.random.uniform(-20, 20)
            base += change
            prices.append(base)

        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
        })

        result = get_industry_trend(df)

        # 震荡市场可能是任何趋势
        self.assertIn(result['trend'], ['uptrend', 'downtrend', 'sideways'])
        print(f"✅ 震荡行业: trend={result['trend']}, strength={result['strength']}")


class TestIndustryTrendPerformance(unittest.TestCase):
    """行业趋势性能测试"""

    def test_large_dataset_performance(self):
        """测试大数据集性能"""
        # 创建大数据集
        np.random.seed(42)
        dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')

        base = 3000
        prices = []
        for _ in range(1000):
            base += np.random.randn() * 20
            prices.append(base)

        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
        })

        # 测量执行时间
        import time
        start = time.time()

        result = get_industry_trend(df)
        result2 = check_industry_above_ma20(df)
        result3 = check_industry_momentum(df)

        elapsed = time.time() - start

        # 验证结果正确性
        self.assertIn('trend', result)
        self.assertIn('above_ma20', result2)
        self.assertIn('momentum_score', result3)

        # 性能应该在合理范围内
        self.assertLess(elapsed, 1.0)  # 应该在1秒内完成

        print(f"✅ 大数据集(1000行)性能: {elapsed:.3f}s")


if __name__ == '__main__':
    unittest.main()
