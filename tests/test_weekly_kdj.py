"""
周线KDJ指标单元测试
"""

import unittest
import pandas as pd
import numpy as np
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.weekly_kdj import (
    calculate_weekly_kdj,
    check_weekly_kdj_oversold,
    check_weekly_kdj_oversold_detailed,
    get_weekly_kdj_signal,
    analyze_weekly_tech,
    calculate_weekly_ma,
)
from config import config


def create_test_data(n=50):
    """创建测试数据辅助函数"""
    np.random.seed(42)
    
    # 模拟价格走势
    base_price = 100
    prices = base_price - np.cumsum(np.random.randn(n) * 2)
    prices = np.maximum(prices, base_price * 0.7)
    
    opens = (prices + np.random.randn(n) * 1).tolist()
    highs = (prices + abs(np.random.randn(n) * 2)).tolist()
    lows = (prices - abs(np.random.randn(n) * 2)).tolist()
    closes = prices.tolist()
    vols = (1000000 + np.random.randint(-200000, 500000, n)).tolist()
    amounts = (prices * 1000000).tolist()
    
    # 使用整数索引
    return pd.DataFrame({
        'trade_date': list(range(n)),
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'vol': vols,
        'amount': amounts,
    })


class TestWeeklyKDJ(unittest.TestCase):
    """周线KDJ测试类"""

    def setUp(self):
        """创建测试数据"""
        self.df = create_test_data(50)

    def test_calculate_weekly_kdj(self):
        """测试周线KDJ计算"""
        df = calculate_weekly_kdj(self.df.copy())

        self.assertIn('K', df.columns)
        self.assertIn('D', df.columns)
        self.assertIn('J', df.columns)

        # 检查K、D值在0-100之间
        valid = df.dropna()
        if not valid.empty:
            self.assertTrue((valid['K'] >= 0).all())
            self.assertTrue((valid['K'] <= 100).all())

        print(f"✅ 周线KDJ计算完成")

    def test_check_weekly_kdj_oversold_true(self):
        """测试J<50检测 - 应该是True"""
        # 创建J<50的数据
        df = self.df.copy()
        df['K'] = 30
        df['D'] = 35
        df['J'] = 20  # J < 50

        result = check_weekly_kdj_oversold(df)

        self.assertTrue(result)
        print(f"✅ J<50检测正确: {result}")

    def test_check_weekly_kdj_oversold_false(self):
        """测试J<50检测 - 应该是False"""
        # 创建J>=50的数据
        df = self.df.copy()
        df['K'] = 70
        df['D'] = 65
        df['J'] = 80  # J >= 50

        result = check_weekly_kdj_oversold(df)

        self.assertFalse(result)
        print(f"✅ J>=50检测正确: {result}")

    def test_check_weekly_kdj_oversold_detailed(self):
        """测试周线KDJ详细状态"""
        df = calculate_weekly_kdj(self.df.copy())
        result = check_weekly_kdj_oversold_detailed(df)

        self.assertIn('j_value', result)
        self.assertIn('k_value', result)
        self.assertIn('d_value', result)
        self.assertIn('is_oversold', result)
        self.assertIn('status', result)

        print(f"✅ 周线KDJ详细状态: J={result['j_value']:.1f}, 状态={result['status']}")

    def test_get_weekly_kdj_signal(self):
        """测试获取周线KDJ信号"""
        df = calculate_weekly_kdj(self.df.copy())
        signal = get_weekly_kdj_signal(df)

        self.assertIsInstance(signal, str)
        print(f"✅ 周线KDJ信号: {signal}")

    def test_analyze_weekly_tech(self):
        """测试综合分析周线技术"""
        df = calculate_weekly_kdj(self.df.copy())
        result = analyze_weekly_tech(df)

        self.assertIn('has_data', result)
        self.assertIn('kdj', result)
        self.assertIn('signal', result)
        self.assertIn('trend', result)

        print(f"✅ 周线技术分析: {result.get('trend')}, 信号: {result.get('signal')}")


class TestWeeklyKDJEdgeCases(unittest.TestCase):
    """周线KDJ边界测试类"""

    def test_empty_dataframe(self):
        """测试空数据"""
        df = pd.DataFrame()
        result = check_weekly_kdj_oversold(df)

        self.assertFalse(result)

    def test_insufficient_data(self):
        """测试数据不足"""
        # 创建少于KDJ周期的数据
        df = pd.DataFrame({
            'close': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [98, 99, 100],
        })

        result = calculate_weekly_kdj(df)

        # 数据不足时返回原数据，K列可能不存在
        # 验证不会崩溃即可
        self.assertIsNotNone(result)

    def test_nan_handling(self):
        """测试NaN处理"""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            'high': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
            'low': [98, 99, 100, 101, 102, 103, 104, 105, 106, 107],
        })

        df['K'] = [np.nan] * 10
        df['D'] = [np.nan] * 10
        df['J'] = [np.nan] * 10

        result = check_weekly_kdj_oversold(df)

        # NaN应该返回False
        self.assertFalse(result)


class TestWeeklyMA(unittest.TestCase):
    """周线均线测试类"""

    def setUp(self):
        """创建测试数据"""
        np.random.seed(42)
        n = 30
        prices = (100 + np.cumsum(np.random.randn(n))).tolist()

        self.df = pd.DataFrame({
            'trade_date': list(range(n)),
            'close': prices,
        })

    def test_calculate_weekly_ma(self):
        """测试周线均线计算"""
        df = calculate_weekly_ma(self.df)

        self.assertIn('ma5', df.columns)
        self.assertIn('ma10', df.columns)
        self.assertIn('ma20', df.columns)

        print(f"✅ 周线均线计算完成")


class TestWeeklyKDJConfig(unittest.TestCase):
    """配置测试类"""

    def test_weekly_kdj_config(self):
        """测试周线KDJ配置"""
        self.assertEqual(config.WEEKLY_KDJ_PERIOD, 9)
        self.assertEqual(config.WEEKLY_KDJ_THRESHOLD, 50)

        print(f"✅ 周线KDJ配置: 周期={config.WEEKLY_KDJ_PERIOD}, 阈值={config.WEEKLY_KDJ_THRESHOLD}")


if __name__ == '__main__':
    unittest.main()
