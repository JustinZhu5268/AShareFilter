"""
技术指标单元测试
"""

import unittest
import pandas as pd
import numpy as np
import datetime

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.technical import (
    calculate_kdj,
    calculate_macd,
    calculate_ma,
    calculate_bollinger_bands,
    calculate_ma_bias,
    calculate_volume_ratio,
    check_kdj_golden_cross,
    check_macd_divergence,
)


class TestTechnicalIndicators(unittest.TestCase):
    """技术指标测试类"""
    
    def setUp(self):
        """创建测试数据"""
        # 创建120天的测试数据
        np.random.seed(42)
        dates = pd.date_range(end=datetime.datetime.now(), periods=120, freq='D')
        
        # 模拟一个下跌后反弹的股票价格走势
        base_price = 100
        prices = base_price - np.cumsum(np.random.randn(120) * 2)
        prices = np.maximum(prices, base_price * 0.7)
        
        self.df = pd.DataFrame({
            'trade_date': [d.strftime('%Y%m%d') for d in dates],
            'open': prices + np.random.randn(120) * 1,
            'high': prices + abs(np.random.randn(120) * 2),
            'low': prices - abs(np.random.randn(120) * 2),
            'close': prices,
            'vol': 1000000 + np.random.randint(-200000, 500000, 120),
        })
    
    def test_calculate_kdj(self):
        """测试KDJ计算"""
        df = calculate_kdj(self.df.copy())
        
        self.assertIn('K', df.columns)
        self.assertIn('D', df.columns)
        self.assertIn('J', df.columns)
        
        # 检查K、D值在0-100之间
        self.assertTrue((df['K'].dropna() >= 0).all())
        self.assertTrue((df['K'].dropna() <= 100).all())
    
    def test_calculate_macd(self):
        """测试MACD计算"""
        df = calculate_macd(self.df.copy())
        
        self.assertIn('macd', df.columns)
        self.assertIn('macd_signal', df.columns)
        self.assertIn('macd_hist', df.columns)
    
    def test_calculate_ma(self):
        """测试均线计算"""
        df = calculate_ma(self.df.copy())
        
        self.assertIn('ma5', df.columns)
        self.assertIn('ma10', df.columns)
        self.assertIn('ma20', df.columns)
        self.assertIn('ma60', df.columns)
    
    def test_calculate_bollinger_bands(self):
        """测试布林带计算"""
        df = calculate_bollinger_bands(self.df.copy())
        
        self.assertIn('bb_upper', df.columns)
        self.assertIn('bb_middle', df.columns)
        self.assertIn('bb_lower', df.columns)
        
        # 验证布林带关系
        valid = df.dropna()
        self.assertTrue((valid['bb_lower'] <= valid['bb_middle']).all())
        self.assertTrue((valid['bb_middle'] <= valid['bb_upper']).all())
    
    def test_calculate_ma_bias(self):
        """测试乖离率计算"""
        df = calculate_ma(self.df.copy())
        bias = calculate_ma_bias(df)
        
        # 乖离率应该是合理的数值
        self.assertIsInstance(bias, float)
        self.assertFalse(np.isnan(bias))
    
    def test_calculate_volume_ratio(self):
        """测试量比计算"""
        ratio = calculate_volume_ratio(self.df)
        
        self.assertIsInstance(ratio, float)
        self.assertGreater(ratio, 0)
    
    def test_check_kdj_golden_cross(self):
        """测试KDJ金叉检测"""
        df = calculate_kdj(self.df.copy())
        
        # 测试金叉函数不会报错
        result = check_kdj_golden_cross(df)
        self.assertIsInstance(result, bool)
    
    def test_check_macd_divergence(self):
        """测试MACD背离检测"""
        df = calculate_macd(self.df.copy())
        
        result = check_macd_divergence(df)
        
        self.assertIn('bullish', result)
        self.assertIn('bearish', result)
        self.assertIsInstance(result['bullish'], bool)
        self.assertIsInstance(result['bearish'], bool)


if __name__ == '__main__':
    unittest.main()
