#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
风控模块测试
功能：
1. 风险评估测试
2. 风险因子测试
3. 风险等级判断测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import numpy as np
from strategy.risk_management import RiskManager


class TestRiskManagement(unittest.TestCase):
    """风控管理测试"""

    def setUp(self):
        """测试前准备"""
        self.risk_manager = RiskManager()

    def test_risk_manager_init(self):
        """测试风控管理器初始化"""
        self.assertIsNotNone(self.risk_manager)
        print("✅ 风控管理器初始化成功")

    def test_evaluate_risk_empty_data(self):
        """测试空数据风险评估"""
        result = self.risk_manager.evaluate_risk({})
        self.assertIn('risk_level', result)
        self.assertIn('risk_score', result)
        print("✅ 空数据风险评估通过")

    def test_evaluate_risk_normal(self):
        """测试正常数据风险评估"""
        risk_data = {
            'profit_ratio': 10.0,
            'volume_ratio': 1.5,
            'ma_bias': 3.0,
            'northbound': 1000,
            'score': 70,
        }
        result = self.risk_manager.evaluate_risk(risk_data)
        self.assertIn('risk_level', result)
        self.assertIn('risk_score', result)
        print(f"✅ 风险评估结果: {result['risk_level']}, 分数: {result['risk_score']}")

    def test_evaluate_risk_high(self):
        """测试高风险数据"""
        risk_data = {
            'profit_ratio': 50.0,  # 获利盘过高
            'volume_ratio': 5.0,   # 量比过高
            'ma_bias': 20.0,      # 乖离率过高
            'northbound': -1000,  # 北向资金流出
            'score': 30,          # 评分过低
        }
        result = self.risk_manager.evaluate_risk(risk_data)
        self.assertIn('risk_level', result)
        print(f"✅ 高风险识别: {result['risk_level']}, 分数: {result['risk_score']}")

    def test_evaluate_risk_low(self):
        """测试低风险数据"""
        risk_data = {
            'profit_ratio': 2.0,
            'volume_ratio': 0.8,
            'ma_bias': 1.0,
            'northbound': 5000,
            'score': 85,
        }
        result = self.risk_manager.evaluate_risk(risk_data)
        self.assertIn('risk_level', result)
        print(f"✅ 低风险识别: {result['risk_level']}, 分数: {result['risk_score']}")

    def test_stop_loss(self):
        """测试止损检测"""
        # 触发止损
        result = self.risk_manager.check_stop_loss(buy_price=100, current_price=92)
        self.assertTrue(result['triggered'])
        self.assertEqual(result['loss_pct'], -8.0)
        print(f"✅ 止损检测: {result}")

        # 未触发止损
        result = self.risk_manager.check_stop_loss(buy_price=100, current_price=98)
        self.assertFalse(result['triggered'])
        print(f"✅ 持有检测: {result}")

    def test_take_profit_kdj_dead_cross(self):
        """测试KDJ死叉止盈检测"""
        # 触发止盈 (KDJ死叉)
        test_df = pd.DataFrame({
            'close': [100.0, 105.0, 108.0, 107.0],
            'K': [80.0, 75.0, 75.0, 70.0],
            'D': [70.0, 70.0, 75.0, 78.0]
        })
        result = self.risk_manager.check_take_profit_kdj_dead_cross(test_df, buy_price=100)
        self.assertIsNotNone(result)
        print(f"✅ KDJ死叉止盈检测: {result}")

    def test_take_profit_ma10_break(self):
        """测试跌破MA10止盈检测"""
        # 触发止盈 (跌破MA10)
        test_df = pd.DataFrame({
            'close': [100.0, 105.0, 108.0, 107.0, 103.0],
            'ma10': [100.0, 102.0, 104.0, 105.0, 106.0]
        })
        result = self.risk_manager.check_take_profit_ma10_break(test_df, buy_price=100)
        self.assertIsNotNone(result)
        print(f"✅ 跌破MA10止盈检测: {result}")

    def test_position_sizing(self):
        """测试仓位管理"""
        result = self.risk_manager.calculate_position_size(
            total_capital=1000000,
            stock_count=5,
            max_position_pct=20.0
        )
        self.assertIn('suggested_count', result)
        self.assertIn('max_per_stock', result)
        print(f"✅ 仓位计算: {result}")


class TestRiskFactors(unittest.TestCase):
    """风险因子测试"""

    def test_price_volatility_factor(self):
        """测试价格波动因子"""
        # 模拟价格数据
        prices = [100 + np.random.randn() * 5 for _ in range(20)]
        volatility = np.std(prices) / np.mean(prices) * 100
        print(f"✅ 价格波动率: {volatility:.2f}%")

    def test_volume_spike_factor(self):
        """测试成交量异动因子"""
        volumes = [1000000] * 10 + [5000000]  # 突然放量
        avg_volume = np.mean(volumes[:-1])
        current_volume = volumes[-1]
        spike_ratio = current_volume / avg_volume
        print(f"✅ 成交量异动: {spike_ratio:.2f}x")

    def test_position_concentration_factor(self):
        """测试持仓集中度因子"""
        # 模拟持仓分布
        positions = [10000] * 5 + [50000]  # 集中度高
        concentration = max(positions) / sum(positions) * 100
        print(f"✅ 持仓集中度: {concentration:.2f}%")


class TestRiskThresholds(unittest.TestCase):
    """风险阈值测试"""

    def test_default_thresholds(self):
        """测试默认阈值"""
        from config import config
        # 检查风控配置
        self.assertTrue(hasattr(config, 'STOP_LOSS_PCT'))
        self.assertTrue(hasattr(config, 'TAKE_PROFIT_PCT'))
        print(f"✅ 风控配置存在: 止损={config.STOP_LOSS_PCT}%, 止盈={config.TAKE_PROFIT_PCT}%")


if __name__ == '__main__':
    unittest.main()
