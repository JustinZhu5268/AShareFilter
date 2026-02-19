#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
支撑位共振判断单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import numpy as np
from indicators.technical import (
    check_support_at_ma60,
    check_support_at_bollinger,
    check_support_resonance,
    analyze_support_level,
    calculate_ma,
    calculate_bollinger_bands,
)


class TestSupportResonance(unittest.TestCase):
    """支撑位共振判断测试"""

    def setUp(self):
        """测试前准备 - 生成模拟数据"""
        # 生成120天的模拟数据
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=120, freq='D')

        # 创建上涨趋势的数据
        base_price = 100
        prices = []
        for i in range(120):
            # 添加一些波动
            change = np.random.randn() * 2
            base_price = base_price + change
            prices.append(base_price)

        self.df = pd.DataFrame({
            'trade_date': dates,
            'open': prices,
            'high': [p + np.random.rand() * 2 for p in prices],
            'low': [p - np.random.rand() * 2 for p in prices],
            'close': prices,
            'vol': [np.random.randint(1000000, 10000000) for _ in range(120)],
        })

    def test_check_support_at_ma60(self):
        """测试MA60支撑位判断"""
        # 先计算均线
        df_with_ma = calculate_ma(self.df.copy(), periods=[60])

        result = check_support_at_ma60(df_with_ma)

        self.assertIn('at_ma60', result)
        self.assertIn('distance', result)
        self.assertIn('close', result)
        self.assertIn('ma60', result)

        print(f"✅ MA60支撑检测: at_ma60={result['at_ma60']}, distance={result['distance']:.2%}")

    def test_check_support_at_ma60_no_data(self):
        """测试数据不足的情况"""
        # 数据不足60天
        df_short = self.df.head(30)

        result = check_support_at_ma60(df_short)

        self.assertFalse(result['at_ma60'])
        print(f"✅ 数据不足时返回False")

    def test_check_support_at_bollinger(self):
        """测试布林下轨支撑位判断"""
        # 先计算布林带
        df_with_bb = calculate_bollinger_bands(self.df.copy())

        result = check_support_at_bollinger(df_with_bb)

        self.assertIn('at_bollinger', result)
        self.assertIn('distance', result)
        self.assertIn('close', result)
        self.assertIn('bb_lower', result)

        print(f"✅ 布林下轨支撑检测: at_bollinger={result['at_bollinger']}, distance={result['distance']:.2%}")

    def test_check_support_resonance(self):
        """测试支撑共振判断"""
        result = check_support_resonance(self.df)

        self.assertIn('resonance', result)
        self.assertIn('at_ma60', result)
        self.assertIn('at_bollinger', result)
        self.assertIn('support_level', result)
        self.assertIn('ma60_info', result)
        self.assertIn('bollinger_info', result)

        print(f"✅ 支撑共振: resonance={result['resonance']}, level={result['support_level']}")

    def test_check_support_resonance_strong(self):
        """测试强共振 - 价格接近MA60和布林下轨"""
        # 创建一个价格接近布林下轨和MA60的数据
        df = self.df.copy()
        df = calculate_ma(df, periods=[60])
        df = calculate_bollinger_bands(df)

        # 设置收盘价接近布林下轨（支撑位）
        last_idx = len(df) - 1
        bb_lower = df['bb_lower'].iloc[last_idx]
        ma60 = df['ma60'].iloc[last_idx]

        # 让价格同时接近两者
        df.iloc[last_idx, df.columns.get_loc('close')] = (bb_lower + ma60) / 2

        result = check_support_resonance(df)

        print(f"✅ 强共振测试: level={result['support_level']}, at_ma60={result['at_ma60']}, at_bollinger={result['at_bollinger']}")

    def test_check_support_resonance_empty_data(self):
        """测试空数据"""
        df_empty = pd.DataFrame()

        result = check_support_resonance(df_empty)

        self.assertFalse(result['resonance'])
        self.assertEqual(result['support_level'], 'none')
        print(f"✅ 空数据返回none")

    def test_analyze_support_level(self):
        """测试综合支撑位获取"""
        result = analyze_support_level(self.df)

        self.assertIn('resonance', result)
        self.assertIn('support_level', result)
        print(f"✅ 支撑级别: {result['support_level']}")

    def test_support_with_tolerance(self):
        """测试容差参数"""
        # 使用较大容差
        result_loose = check_support_resonance(self.df, ma60_tolerance=0.1, bollinger_tolerance=0.1)

        # 使用较小容差
        result_tight = check_support_resonance(self.df, ma60_tolerance=0.01, bollinger_tolerance=0.01)

        print(f"✅ 容差测试: loose_level={result_loose['support_level']}, tight_level={result_tight['support_level']}")


class TestSupportResonanceEdgeCases(unittest.TestCase):
    """支撑位共振边界测试"""

    def test_single_row_data(self):
        """测试单行数据"""
        df = pd.DataFrame({
            'close': [100],
            'open': [100],
            'high': [101],
            'low': [99],
            'vol': [1000000],
        })

        result = check_support_resonance(df)

        # 数据不足应该返回none
        self.assertEqual(result['support_level'], 'none')
        print(f"✅ 单行数据返回none")

    def test_zero_values(self):
        """测试零值处理"""
        df = pd.DataFrame({
            'close': [0, 0, 0],
            'open': [0, 0, 0],
            'high': [0, 0, 0],
            'low': [0, 0, 0],
            'vol': [1000000, 1000000, 1000000],
        })

        result = check_support_resonance(df)

        self.assertIn('support_level', result)
        print(f"✅ 零值处理正常")

    def test_negative_values(self):
        """测试负值处理"""
        df = pd.DataFrame({
            'close': [-100, -99, -98],
            'open': [-100, -99, -98],
            'high': [-99, -98, -97],
            'low': [-101, -100, -99],
            'vol': [1000000, 1000000, 1000000],
        })

        result = check_support_resonance(df)

        self.assertIn('support_level', result)
        print(f"✅ 负值处理正常")


class TestSupportResonanceIntegration(unittest.TestCase):
    """支撑位共振集成测试"""

    def setUp(self):
        """测试前准备 - 生成模拟数据"""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=120, freq='D')

        base_price = 100
        prices = []
        for i in range(120):
            change = np.random.randn() * 2
            base_price = base_price + change
            prices.append(base_price)

        self.df = pd.DataFrame({
            'trade_date': dates,
            'open': prices,
            'high': [p + np.random.rand() * 2 for p in prices],
            'low': [p - np.random.rand() * 2 for p in prices],
            'close': prices,
            'vol': [np.random.randint(1000000, 10000000) for _ in range(120)],
        })

    def test_support_resonance_medium_level(self):
        """测试中等支撑级别"""
        # 创建一个只在MA60附近的价格
        df = self.df.copy()
        df = calculate_ma(df, periods=[60])

        # 设置收盘价接近MA60但远离布林下轨
        last_idx = len(df) - 1
        ma60 = df['ma60'].iloc[last_idx]
        df.iloc[last_idx, df.columns.get_loc('close')] = ma60 * 1.02  # 略高于MA60 2%

        result = check_support_resonance(df)

        # 应该是中等支撑
        self.assertEqual(result['support_level'], 'medium')
        self.assertTrue(result['at_ma60'])
        self.assertFalse(result['at_bollinger'])

        print(f"✅ 中等支撑: level={result['support_level']}")

    def test_support_resonance_weak_level(self):
        """测试弱支撑级别"""
        # 创建一个既不在MA60也不在布林下轨的价格
        df = self.df.copy()
        df = calculate_ma(df, periods=[60])
        df = calculate_bollinger_bands(df)

        # 设置收盘价远离两个支撑位
        last_idx = len(df) - 1
        ma60 = df['ma60'].iloc[last_idx]
        bb_lower = df['bb_lower'].iloc[last_idx]

        # 放在中间位置
        df.iloc[last_idx, df.columns.get_loc('close')] = (ma60 + bb_lower) / 2 + (ma60 - bb_lower)

        result = check_support_resonance(df)

        # 应该是无支撑
        self.assertEqual(result['support_level'], 'none')
        self.assertFalse(result['at_ma60'])
        self.assertFalse(result['at_bollinger'])

        print(f"✅ 弱支撑: level={result['support_level']}")

    def test_support_at_ma60_tolerance(self):
        """测试MA60支撑不同容差"""
        df = self.df.copy()

        # 计算MA60
        df = calculate_ma(df, periods=[60])

        # 设置收盘价在MA60上方2%
        last_idx = len(df) - 1
        ma60 = df['ma60'].iloc[last_idx]
        df.iloc[last_idx, df.columns.get_loc('close')] = ma60 * 1.02  # 略高于MA60 2%

        # 3%容差应该能检测到
        result_3 = check_support_at_ma60(df, tolerance=0.03)

        # 1%容差应该检测不到
        result_1 = check_support_at_ma60(df, tolerance=0.01)

        self.assertTrue(result_3['at_ma60'])
        self.assertFalse(result_1['at_ma60'])

        print(f"✅ 容差测试: 3%={result_3['at_ma60']}, 1%={result_1['at_ma60']}")

    def test_support_at_bollinger_tolerance(self):
        """测试布林下轨支撑不同容差"""
        df = self.df.copy()

        # 计算布林带
        df = calculate_bollinger_bands(df)

        # 设置收盘价在布林下轨上方3%
        last_idx = len(df) - 1
        bb_lower = df['bb_lower'].iloc[last_idx]
        df.iloc[last_idx, df.columns.get_loc('close')] = bb_lower * 1.03

        # 3%容差应该刚好在边界
        result_3 = check_support_at_bollinger(df, tolerance=0.03)

        # 2%容差应该不在范围内
        result_2 = check_support_at_bollinger(df, tolerance=0.02)

        self.assertTrue(result_3['at_bollinger'])
        self.assertFalse(result_2['at_bollinger'])

        print(f"✅ 布林容差测试: 3%={result_3['at_bollinger']}, 2%={result_2['at_bollinger']}")

    def test_analyze_support_level_comprehensive(self):
        """测试综合支撑位获取"""
        result = analyze_support_level(self.df)

        # 验证返回结构完整
        self.assertIn('resonance', result)
        self.assertIn('support_level', result)
        self.assertIn('at_ma60', result)
        self.assertIn('at_bollinger', result)
        self.assertIn('ma60_info', result)
        self.assertIn('bollinger_info', result)

        # 验证级别有效性
        self.assertIn(result['support_level'], ['strong', 'medium', 'weak', 'none'])

        print(f"✅ 综合支撑: {result['support_level']}")


class TestSupportResonanceRealWorld(unittest.TestCase):
    """支撑共振真实场景测试"""

    def test_strong_support_at_bottom(self):
        """测试价格在底部的强支撑"""
        np.random.seed(500)
        dates = pd.date_range(start='2024-01-01', periods=120, freq='D')

        # 创建先上涨后下跌的走势，形成支撑位
        base = 100
        prices = []
        for i in range(80):
            base += np.random.uniform(-2, 3)  # 上涨趋势
            prices.append(base)

        # 在底部盘整
        bottom = prices[-1]
        for _ in range(40):
            prices.append(bottom + np.random.uniform(-1, 1))

        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
            'open': [p - np.random.rand() for p in prices],
            'high': [p + np.random.rand() * 2 for p in prices],
            'low': [p - np.random.rand() * 2 for p in prices],
            'vol': [np.random.randint(1000000, 10000000) for _ in range(120)],
        })

        result = check_support_resonance(df)

        # 验证支撑检测工作
        self.assertIn('support_level', result)
        print(f"✅ 底部支撑: level={result['support_level']}")

    def test_resistance_at_high(self):
        """测试阻力位检测"""
        np.random.seed(600)
        dates = pd.date_range(start='2024-01-01', periods=120, freq='D')

        # 创建持续上涨后高位的走势
        base = 80
        prices = []
        for i in range(120):
            base += np.random.uniform(0, 3)  # 持续上涨
            prices.append(base)

        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
        })

        result = check_support_resonance(df)

        # 高位应该没有支撑
        self.assertIn(result['support_level'], ['none', 'medium'])
        print(f"✅ 高位阻力: level={result['support_level']}")


class TestSupportResonancePerformance(unittest.TestCase):
    """支撑共振性能测试"""

    def test_large_dataset_performance(self):
        """测试大数据集性能"""
        # 创建大数据集
        np.random.seed(42)
        dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')

        base = 100
        prices = []
        for _ in range(1000):
            base += np.random.randn() * 2
            prices.append(base)

        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices,
            'open': [p - np.random.rand() for p in prices],
            'high': [p + np.random.rand() * 2 for p in prices],
            'low': [p - np.random.rand() * 2 for p in prices],
            'vol': [np.random.randint(1000000, 10000000) for _ in range(1000)],
        })

        # 测量执行时间
        import time
        start = time.time()

        result = check_support_resonance(df)
        result2 = check_support_at_ma60(df)
        result3 = check_support_at_bollinger(df)

        elapsed = time.time() - start

        # 验证结果正确性
        self.assertIn('support_level', result)
        self.assertIn('at_ma60', result2)
        self.assertIn('at_bollinger', result3)

        # 性能应该在合理范围内
        self.assertLess(elapsed, 2.0)  # 应该在2秒内完成

        print(f"✅ 大数据集(1000行)性能: {elapsed:.3f}s")


if __name__ == '__main__':
    unittest.main()
