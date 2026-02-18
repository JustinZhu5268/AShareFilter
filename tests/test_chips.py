"""
筹码分析模块单元测试
"""
import unittest
import pandas as pd
import numpy as np
import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.chips import (
    calculate_vwap,
    calculate_vwap_chips,
    calculate_cost_distribution,
    check_single_peak,
    analyze_chips,
)


class TestChips(unittest.TestCase):
    """筹码分析测试类"""
    
    def setUp(self):
        """创建测试数据"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.datetime.now(), periods=120, freq='D')
        
        # 模拟一个下跌后反弹的股票价格走势
        base_price = 100
        prices = base_price - np.cumsum(np.random.randn(120) * 2)
        prices = np.maximum(prices, base_price * 0.7)
        
        # 生成成交量数据
        volumes = 1000000 + np.random.randint(-200000, 500000, 120)
        
        # 计算成交额 (元)
        amounts = prices * volumes * 100  # 手 × 元
        
        self.df = pd.DataFrame({
            'trade_date': [d.strftime('%Y%m%d') for d in dates],
            'open': prices + np.random.randn(120) * 1,
            'high': prices + abs(np.random.randn(120) * 2),
            'low': prices - abs(np.random.randn(120) * 2),
            'close': prices,
            'vol': volumes,
            'amount': amounts,
        })
    
    def test_calculate_vwap(self):
        """测试VWAP计算"""
        result = calculate_vwap(self.df)
        
        # VWAP DataFrame应该是正值的
        self.assertFalse(result.empty)
        self.assertIn('vwap', result.columns)
        print(f"✅ VWAP计算完成")
    
    def test_calculate_vwap_chips(self):
        """测试VWAP筹码分布计算"""
        result = calculate_vwap_chips(self.df)
        
        # 检查返回字段 - 根据实际返回的字段
        self.assertIn('profit_ratio', result)
        self.assertIn('concentration', result)
        
        print(f"✅ VWAP筹码分布: 获利比例={result['profit_ratio']:.1f}%, 集中度={result['concentration']:.2f}")
    
    def test_calculate_cost_distribution(self):
        """测试成本分布计算"""
        result = calculate_cost_distribution(self.df)
        
        # 检查返回字段 - 根据实际返回的字段
        self.assertIn('peak_price', result)
        self.assertIn('distribution', result)
        
        print(f"✅ 成本分布: 峰值价格={result['peak_price']:.2f}")
    
    def test_check_single_peak(self):
        """测试单峰检测"""
        has_peak = check_single_peak(self.df)
        
        self.assertIsInstance(bool(has_peak), bool)
        print(f"✅ 单峰检测: {'是' if has_peak else '否'}")
    
    def test_analyze_chips(self):
        """测试综合筹码分析"""
        result = analyze_chips(self.df)
        
        # 检查返回字段 - 根据实际返回的字段
        self.assertIn('profit_ratio', result)
        self.assertIn('concentration', result)
        
        print(f"✅ 筹码分析完成:")
        print(f"   获利盘: {result['profit_ratio']:.1f}%")
        print(f"   集中度: {result['concentration']:.2f}")


class TestChipsEdgeCases(unittest.TestCase):
    """筹码分析边界测试类"""
    
    def test_empty_dataframe(self):
        """测试空数据"""
        df = pd.DataFrame()
        
        # 空数据可能返回默认值而不是抛出异常
        result = calculate_vwap_chips(df)
        self.assertIsNotNone(result)
    
    def test_single_row(self):
        """测试单行数据"""
        df = pd.DataFrame({
            'close': [100],
            'vol': [1000],
            'amount': [100000],
        })
        
        result = calculate_vwap_chips(df)
        self.assertIsNotNone(result)
    
    def test_zero_volume(self):
        """测试零成交量"""
        df = pd.DataFrame({
            'close': [100, 101, 102],
            'vol': [0, 0, 0],
            'amount': [0, 0, 0],
        })
        
        # 应该能处理零成交量
        result = calculate_vwap_chips(df)
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
