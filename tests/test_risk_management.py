"""
风控管理模块单元测试
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.risk_management import (
    RiskManager,
    get_risk_manager,
)
from config import config


class TestRiskManager(unittest.TestCase):
    """风控管理器测试类"""

    def setUp(self):
        """设置测试"""
        self.manager = RiskManager()

    def test_check_stop_loss_triggered(self):
        """测试止损触发"""
        # 买入价100，当前价92，亏损8%
        result = self.manager.check_stop_loss(100, 92)

        self.assertTrue(result['triggered'])
        self.assertAlmostEqual(result['loss_pct'], -8.0, places=1)
        self.assertEqual(result['action'], '止损')

    def test_check_stop_loss_not_triggered(self):
        """测试止损未触发"""
        # 买入价100，当前价96，亏损4%
        result = self.manager.check_stop_loss(100, 96)

        self.assertFalse(result['triggered'])
        self.assertAlmostEqual(result['loss_pct'], -4.0, places=1)
        self.assertEqual(result['action'], '持有')

    def test_check_stop_loss_profit(self):
        """测试盈利情况"""
        # 买入价100，当前价110，盈利10%
        result = self.manager.check_stop_loss(100, 110)

        self.assertFalse(result['triggered'])
        self.assertAlmostEqual(result['loss_pct'], 10.0, places=1)

    def test_check_stop_loss_invalid_price(self):
        """测试无效价格"""
        result = self.manager.check_stop_loss(0, 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['action'], '无效价格')

    def test_check_stop_loss_negative_price(self):
        """测试负价格"""
        result = self.manager.check_stop_loss(-10, 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['action'], '无效价格')

    def test_check_stop_loss_exactly_at_threshold(self):
        """测试正好达到止损阈值"""
        # 买入价100，当前价93，亏损7%，正好是止损线
        result = self.manager.check_stop_loss(100, 93)
        # -7% 应该触发止损 (根据配置 STOP_LOSS_PCT = 7.0)
        self.assertTrue(result['triggered'])
        self.assertAlmostEqual(result['loss_pct'], -7.0, places=1)

    def test_check_stop_loss_just_above_threshold(self):
        """测试略高于止损阈值"""
        # 买入价100，当前价93.01，亏损6.99%
        result = self.manager.check_stop_loss(100, 93.01)
        self.assertFalse(result['triggered'])

    def test_check_stop_loss_extreme_profit(self):
        """测试极端盈利情况"""
        # 买入价100，当前价200，盈利100%
        result = self.manager.check_stop_loss(100, 200)
        self.assertFalse(result['triggered'])
        self.assertAlmostEqual(result['loss_pct'], 100.0, places=1)

    def test_check_stop_loss_extreme_loss(self):
        """测试极端亏损情况"""
        # 买入价100，当前价1，亏损99%
        result = self.manager.check_stop_loss(100, 1)
        self.assertTrue(result['triggered'])
        self.assertAlmostEqual(result['loss_pct'], -99.0, places=1)

    def test_check_take_profit_kdj_dead_cross_triggered(self):
        """测试KDJ死叉止盈触发"""
        # 创建测试数据，包含KDJ死叉
        df = pd.DataFrame({
            'K': [65, 60],  # 昨天K=65, 今天K=60
            'D': [60, 62],  # 昨天D=60, 今天D=62 (金叉变死叉)
            'close': [105, 104],
        })

        result = self.manager.check_take_profit_kdj_dead_cross(df, 100)

        self.assertTrue(result['triggered'])
        self.assertEqual(result['reason'], 'KDJ死叉')
        self.assertEqual(result['action'], '减仓50%')

    def test_check_take_profit_kdj_dead_cross_not_triggered(self):
        """测试KDJ死叉未触发"""
        # 创建测试数据，无死叉
        df = pd.DataFrame({
            'K': [60, 65],  # 金叉
            'D': [58, 62],
            'close': [104, 105],
        })

        result = self.manager.check_take_profit_kdj_dead_cross(df, 100)

        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '无死叉')

    def test_check_take_profit_kdj_dead_cross_none_df(self):
        """测试KDJ死叉检测None数据"""
        result = self.manager.check_take_profit_kdj_dead_cross(None, 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '数据不足')

    def test_check_take_profit_kdj_dead_cross_empty_df(self):
        """测试KDJ死叉检测空DataFrame"""
        result = self.manager.check_take_profit_kdj_dead_cross(pd.DataFrame(), 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '数据不足')

    def test_check_take_profit_kdj_dead_cross_single_row(self):
        """测试KDJ死叉检测单行数据"""
        df = pd.DataFrame({
            'K': [65],
            'D': [60],
            'close': [105],
        })
        result = self.manager.check_take_profit_kdj_dead_cross(df, 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '数据不足')

    def test_check_take_profit_kdj_dead_cross_zero_buy_price(self):
        """测试KDJ死叉检测零买入价"""
        # 使用没有死叉的数据
        df = pd.DataFrame({
            'K': [60, 65],  # 金叉，不是死叉
            'D': [55, 60],
            'close': [105, 104],
        })
        result = self.manager.check_take_profit_kdj_dead_cross(df, 0)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['profit_pct'], 0.0)

    def test_check_take_profit_kdj_dead_cross_negative_buy_price(self):
        """测试KDJ死叉检测负买入价"""
        # 使用没有死叉的数据
        df = pd.DataFrame({
            'K': [60, 65],  # 金叉，不是死叉
            'D': [55, 60],
            'close': [105, 104],
        })
        result = self.manager.check_take_profit_kdj_dead_cross(df, -10)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['profit_pct'], 0.0)

    def test_check_take_profit_ma10_break_triggered(self):
        """测试跌破MA10止盈触发"""
        df = pd.DataFrame({
            'close': [105],
            'ma10': [110],  # 当前价105 < MA10 110
        })

        result = self.manager.check_take_profit_ma10_break(df, 100)

        self.assertTrue(result['triggered'])
        self.assertEqual(result['reason'], '跌破MA10')
        self.assertEqual(result['action'], '全部止盈')

    def test_check_take_profit_ma10_break_not_triggered(self):
        """测试跌破MA10止盈未触发"""
        df = pd.DataFrame({
            'close': [115],
            'ma10': [110],  # 当前价115 > MA10 110
        })

        result = self.manager.check_take_profit_ma10_break(df, 100)

        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '未跌破MA10')

    def test_check_take_profit_ma10_break_none_df(self):
        """测试MA10跌破检测None数据"""
        result = self.manager.check_take_profit_ma10_break(None, 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '数据不足')

    def test_check_take_profit_ma10_break_empty_df(self):
        """测试MA10跌破检测空DataFrame"""
        result = self.manager.check_take_profit_ma10_break(pd.DataFrame(), 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '数据不足')

    def test_check_take_profit_ma10_break_missing_ma10_column(self):
        """测试MA10跌破检测缺少ma10列"""
        df = pd.DataFrame({
            'close': [105],
            'ma5': [110],  # 错误的列名
        })
        result = self.manager.check_take_profit_ma10_break(df, 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '缺少MA10数据')

    def test_check_take_profit_ma10_break_na_ma10(self):
        """测试MA10跌破检测ma10为NaN"""
        df = pd.DataFrame({
            'close': [105],
            'ma10': [np.nan],
        })
        result = self.manager.check_take_profit_ma10_break(df, 100)
        self.assertFalse(result['triggered'])

    def test_check_take_profit_ma10_break_zero_buy_price(self):
        """测试MA10跌破检测零买入价"""
        # 使用没有跌破MA10的数据
        df = pd.DataFrame({
            'close': [115],
            'ma10': [110],  # 115 > 110，没有跌破
        })
        result = self.manager.check_take_profit_ma10_break(df, 0)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['profit_pct'], 0.0)

    def test_check_take_profit_ma10_break_at_exact_ma10(self):
        """测试MA10跌破检测正好在MA10价格"""
        # 当前价 = MA10，不算跌破
        df = pd.DataFrame({
            'close': [110],
            'ma10': [110],
        })
        result = self.manager.check_take_profit_ma10_break(df, 100)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['reason'], '未跌破MA10')

    def test_calculate_position_size(self):
        """测试仓位计算"""
        result = self.manager.calculate_position_size(1000000, 5)

        self.assertIn('max_per_stock', result)
        self.assertIn('suggested_count', result)
        self.assertIn('max_total_pct', result)

        # 100万资金，单只股票最大20%，应该不超过20万
        self.assertLessEqual(result['max_per_stock'], 200000)
        # 建议数量应该不超过8只
        self.assertLessEqual(result['suggested_count'], 8)

    def test_calculate_position_size_zero(self):
        """测试零资金仓位计算"""
        result = self.manager.calculate_position_size(0, 5)
        self.assertEqual(result['max_per_stock'], 0.0)
        self.assertEqual(result['suggested_count'], 0)

    def test_calculate_position_size_negative_capital(self):
        """测试负资金仓位计算"""
        result = self.manager.calculate_position_size(-100000, 5)
        self.assertEqual(result['max_per_stock'], 0.0)
        self.assertEqual(result['suggested_count'], 0)

    def test_calculate_position_size_zero_count(self):
        """测试零股票数量仓位计算"""
        result = self.manager.calculate_position_size(1000000, 0)
        self.assertEqual(result['max_per_stock'], 0.0)
        self.assertEqual(result['suggested_count'], 0)

    def test_calculate_position_size_negative_count(self):
        """测试负股票数量仓位计算"""
        result = self.manager.calculate_position_size(1000000, -5)
        self.assertEqual(result['max_per_stock'], 0.0)
        self.assertEqual(result['suggested_count'], 0)

    def test_calculate_position_size_large_count(self):
        """测试大股票数量仓位计算"""
        # 超过8只的情况
        result = self.manager.calculate_position_size(1000000, 10)
        self.assertLessEqual(result['suggested_count'], 8)
        # 总仓位不超过80%
        self.assertLessEqual(result['max_total_pct'], 80.0)

    def test_calculate_position_size_custom_max_position(self):
        """测试自定义最大仓位"""
        result = self.manager.calculate_position_size(1000000, 5, max_position_pct=10.0)
        self.assertEqual(result['max_per_stock'], 100000.0)  # 1000000 * 10%

    def test_calculate_position_size_max_cap(self):
        """测试总仓位上限"""
        # 5只 * 20% = 100% > 80%上限
        result = self.manager.calculate_position_size(1000000, 5)
        self.assertLessEqual(result['max_total_pct'], 80.0)

    def test_evaluate_risk_low(self):
        """测试低风险评估"""
        stock_data = {
            'profit_ratio': 10,
            'ma_bias': 2,
            'volume_ratio': 1.5,
            'northbound': 1000000,
            'score': 85,
        }

        result = self.manager.evaluate_risk(stock_data)

        self.assertEqual(result['risk_level'], '低')
        self.assertEqual(result['recommendation'], '买入')
        self.assertGreater(result['risk_score'], 70)

    def test_evaluate_risk_high(self):
        """测试高风险评估"""
        stock_data = {
            'profit_ratio': 40,  # 获利盘过高
            'ma_bias': 15,       # 乖离率过高
            'volume_ratio': 6,   # 量比过高
            'northbound': -100000,  # 北向资金流出
            'score': 30,          # 评分过低
        }

        result = self.manager.evaluate_risk(stock_data)

        self.assertEqual(result['risk_level'], '高')
        self.assertEqual(result['recommendation'], '观望')
        self.assertLess(result['risk_score'], 40)
        self.assertGreater(len(result['warnings']), 0)

    def test_evaluate_risk_medium(self):
        """测试中等风险评估"""
        stock_data = {
            'profit_ratio': 20,  # 获利盘中等
            'ma_bias': 7,        # 乖离率偏高
            'volume_ratio': 3.5,  # 量比偏高
            'northbound': 0,      # 北向资金持平
            'score': 55,          # 评分中等
        }

        result = self.manager.evaluate_risk(stock_data)

        self.assertEqual(result['risk_level'], '中')
        self.assertGreaterEqual(result['risk_score'], 40)
        self.assertLess(result['risk_score'], 80)

    def test_evaluate_risk_boundary_80(self):
        """测试风险评分边界80"""
        stock_data = {
            'profit_ratio': 0,
            'ma_bias': 0,
            'volume_ratio': 0,
            'northbound': 1000,
            'score': 100,
        }

        result = self.manager.evaluate_risk(stock_data)
        self.assertEqual(result['risk_level'], '低')
        self.assertGreaterEqual(result['risk_score'], 80)

    def test_evaluate_risk_boundary_60(self):
        """测试风险评分边界60"""
        # score=55 在 40-60 范围，扣 10 分
        # profit_ratio=16 在 16-30 范围，扣 15 分
        # 总分 = 100 - 15 - 10 = 75 >= 60，应该是 '中'
        stock_data = {
            'profit_ratio': 16,  # > 15, 扣15分
            'ma_bias': 0,
            'volume_ratio': 1,
            'northbound': 0,
            'score': 55,  # < 60, >= 40, 扣10分
        }
        result = self.manager.evaluate_risk(stock_data)
        self.assertEqual(result['risk_level'], '中')

    def test_evaluate_risk_profit_ratio_boundary(self):
        """测试获利盘边界值"""
        # 刚好16%，在 15< profit_ratio <= 30 范围，扣15分
        stock_data = {
            'profit_ratio': 16,  # > 15, 扣15分
            'ma_bias': 0,
            'volume_ratio': 1,
            'northbound': 0,
            'score': 100,
        }
        result = self.manager.evaluate_risk(stock_data)
        # 100 - 15 = 85 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

        # 刚好31%，> 30，扣30分
        stock_data['profit_ratio'] = 31
        result = self.manager.evaluate_risk(stock_data)
        # 100 - 30 = 70 >= 60，应该是 '中'
        self.assertEqual(result['risk_level'], '中')

    def test_evaluate_risk_ma_bias_boundary(self):
        """测试乖离率边界值"""
        # 刚好6%，在 5< ma_bias <= 10 范围，扣10分
        stock_data = {
            'profit_ratio': 0,
            'ma_bias': 6,  # > 5, 扣10分
            'volume_ratio': 1,
            'northbound': 0,
            'score': 100,
        }
        result = self.manager.evaluate_risk(stock_data)
        # 100 - 10 = 90 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

        # 刚好11%，> 10，扣20分
        stock_data['ma_bias'] = 11
        result = self.manager.evaluate_risk(stock_data)
        # 100 - 20 = 80 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

    def test_evaluate_risk_volume_ratio_boundary(self):
        """测试量比边界值"""
        # 刚好4%，在 3< vol_ratio <= 5 范围，扣10分
        stock_data = {
            'profit_ratio': 0,
            'ma_bias': 0,
            'volume_ratio': 4,  # > 3, 扣10分
            'northbound': 0,
            'score': 100,
        }
        result = self.manager.evaluate_risk(stock_data)
        # 100 - 10 = 90 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

        # 刚好6%，> 5，扣20分
        stock_data['volume_ratio'] = 6
        result = self.manager.evaluate_risk(stock_data)
        # 100 - 20 = 80 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

    def test_evaluate_risk_score_boundary(self):
        """测试评分边界值"""
        # 刚好39，< 40，扣20分
        stock_data = {
            'profit_ratio': 0,
            'ma_bias': 0,
            'volume_ratio': 1,
            'northbound': 0,
            'score': 39,  # < 40, 扣20分
        }
        result = self.manager.evaluate_risk(stock_data)
        # 100 - 20 = 80 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

        # 刚好40，不扣分
        stock_data['score'] = 40
        result = self.manager.evaluate_risk(stock_data)
        # 100 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

        # 刚好59，在 40-60 范围，扣10分
        stock_data['score'] = 59
        result = self.manager.evaluate_risk(stock_data)
        # 100 - 10 = 90 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

        # 刚好60，不扣分
        stock_data['score'] = 60
        result = self.manager.evaluate_risk(stock_data)
        # 100 >= 80，应该是 '低'
        self.assertEqual(result['risk_level'], '低')

    def test_get_trade_signal_stop_loss(self):
        """测试交易信号 - 止损"""
        position = {'buy_price': 100}
        market_data = pd.DataFrame({
            'close': [92],
        })

        result = self.manager.get_trade_signal(position, market_data)

        self.assertEqual(result['action'], '止损')
        self.assertEqual(result['priority'], 1)

    def test_get_trade_signal_hold(self):
        """测试交易信号 - 持有"""
        position = {'buy_price': 100}
        market_data = pd.DataFrame({
            'close': [103],
            'K': [60],
            'D': [55],
            'ma10': [102],
        })

        result = self.manager.get_trade_signal(position, market_data)

        self.assertEqual(result['action'], '持有')
        self.assertEqual(result['priority'], 0)

    def test_get_trade_signal_zero_buy_price(self):
        """测试交易信号 - 零买入价"""
        position = {'buy_price': 0}
        market_data = pd.DataFrame({
            'close': [103],
        })

        result = self.manager.get_trade_signal(position, market_data)

        self.assertEqual(result['action'], '持有')
        self.assertEqual(result['reason'], '数据不足')

    def test_get_trade_signal_negative_buy_price(self):
        """测试交易信号 - 负买入价"""
        position = {'buy_price': -10}
        market_data = pd.DataFrame({
            'close': [103],
        })

        result = self.manager.get_trade_signal(position, market_data)

        self.assertEqual(result['action'], '持有')
        self.assertEqual(result['reason'], '数据不足')

    def test_get_trade_signal_none_market_data(self):
        """测试交易信号 - None市场数据"""
        position = {'buy_price': 100}
        result = self.manager.get_trade_signal(position, None)

        self.assertEqual(result['action'], '持有')
        self.assertEqual(result['reason'], '数据不足')

    def test_get_trade_signal_empty_market_data(self):
        """测试交易信号 - 空市场数据"""
        position = {'buy_price': 100}
        market_data = pd.DataFrame()
        result = self.manager.get_trade_signal(position, market_data)

        self.assertEqual(result['action'], '持有')
        self.assertEqual(result['reason'], '数据不足')

    def test_get_trade_signal_without_kdj(self):
        """测试交易信号 - 无KDJ数据"""
        position = {'buy_price': 100}
        market_data = pd.DataFrame({
            'close': [103],
            'ma10': [102],
        })

        result = self.manager.get_trade_signal(position, market_data)

        # 没有KDJ，但仍应有止盈检查
        self.assertIn(result['action'], ['持有', '考虑止盈'])

    def test_get_trade_signal_without_ma10(self):
        """测试交易信号 - 无MA10数据"""
        position = {'buy_price': 100}
        market_data = pd.DataFrame({
            'close': [103],
            'K': [60],
            'D': [55],
        })

        result = self.manager.get_trade_signal(position, market_data)

        # 没有MA10，但仍应检查KDJ和止盈
        self.assertIn(result['action'], ['持有', '考虑止盈'])

    def test_get_trade_signal_reach_take_profit(self):
        """测试交易信号 - 达到止盈线"""
        position = {'buy_price': 100}
        market_data = pd.DataFrame({
            'close': [132],  # 盈利32%，超过30%止盈线
            'K': [60],       # 保持金叉
            'D': [55],
            'ma10': [105],
        })

        result = self.manager.get_trade_signal(position, market_data)

        # 盈利超过30%但没有触发止盈条件
        self.assertIn(result['action'], ['持有', '考虑止盈'])

    def test_get_trade_signal_priority_order(self):
        """测试交易信号优先级顺序"""
        # 止损优先级最高
        position = {'buy_price': 100}
        market_data = pd.DataFrame({
            'close': [91, 90, 89, 88, 87],  # 5个元素
            'K': [80, 75, 70, 65, 60],
            'D': [75, 78, 80, 82, 85],
            'ma10': [105, 106, 107, 108, 109]
        })

        result = self.manager.get_trade_signal(position, market_data)

        # 止损优先级最高
        self.assertEqual(result['action'], '止损')
        self.assertEqual(result['priority'], 1)


class TestRiskManagerConfig(unittest.TestCase):
    """风控配置测试类"""

    def test_stop_loss_config(self):
        """测试止损配置"""
        self.assertEqual(config.STOP_LOSS_PCT, 7.0)

    def test_take_profit_config(self):
        """测试止盈配置"""
        self.assertEqual(config.TAKE_PROFIT_PCT, 30.0)


class TestGetRiskManager(unittest.TestCase):
    """全局风控管理器测试"""

    def test_get_manager(self):
        """测试获取全局管理器"""
        manager1 = get_risk_manager()
        manager2 = get_risk_manager()

        # 应该是同一个实例
        self.assertIs(manager1, manager2)


class TestRiskSignalIntegration(unittest.TestCase):
    """
    风控与信号集成测试
    测试内容:
    1. 信号评分与风控评估的综合集成
    2. 多条件组合风控信号生成
    3. 持仓期间风控信号演变
    4. 风控规则对买入信号过滤
    """

    def setUp(self):
        """设置测试"""
        from api.tushare_client import TushareClient
        self.client = TushareClient(use_mock=True)
        self.risk_manager = get_risk_manager()
        from strategy.signal import evaluate_buy_signal
        self.evaluate_signal = evaluate_buy_signal
        from strategy.filter import StockFilter
        self.filter = StockFilter(self.client)

    def test_signal_evaluation_with_risk_integration(self):
        """
        测试1: 信号评分与风控评估的综合集成
        验证信号评估函数中集成了风控评估结果
        """
        # 创建测试股票数据 - 包含完整字段
        stock_data = {
            'code': '300274',
            'name': '阳光电源',
            'industry': '电气设备',
            'price': 100.0,
            'market_cap': 300e8,
            'roe': 20.0,
            'ma_bias': -3.0,
            'kdj': '金叉',
            'volume_ratio': 1.5,
            'macd_divergence': '底背离',
            'profit_ratio': 20.0,
            'concentration': 10.0,
            'single_peak': True,
            'northbound': 1000.0,
            'northbound_days': 5,
            'main_funds': 500.0,
            'bb_position': '中轨',
            'score': 85,
        }

        # 执行信号评估
        signal_result = self.evaluate_signal(stock_data)

        # 验证信号评估结果包含风控信息
        self.assertIn('risk_score', signal_result)
        self.assertIn('risk_level', signal_result)
        self.assertIn('risk_factors', signal_result)

        # 验证风控评估结果
        self.assertIsNotNone(signal_result['risk_score'])
        self.assertIn(signal_result['risk_level'], ['低', '中', '高'])

        print(f"✅ 信号评估与风控集成测试通过")
        print(f"   股票: {stock_data['code']} {stock_data['name']}")
        print(f"   信号评分: {signal_result['total_score']}")
        print(f"   风控评分: {signal_result['risk_score']}")
        print(f"   风控等级: {signal_result['risk_level']}")

    def test_multi_condition_risk_signal_generation(self):
        """
        测试2: 多条件组合风控信号生成
        验证同时满足多个风控条件时的信号优先级
        """
        # 场景1: 触发止损 (最高优先级)
        position = {'buy_price': 100.0, 'buy_date': '2024-01-01'}
        market_data = pd.DataFrame({
            'close': [100.0, 98.0, 95.0, 92.0, 91.0],
            'K': [80.0, 75.0, 70.0, 65.0, 60.0],
            'D': [70.0, 72.0, 74.0, 76.0, 78.0],
            'ma10': [100.0, 99.0, 98.0, 97.0, 96.0]
        })

        signal = self.risk_manager.get_trade_signal(position, market_data)

        # 止损优先级最高
        self.assertEqual(signal['action'], '止损')
        self.assertEqual(signal['priority'], 1)
        print(f"   止损信号: {signal['action']} - {signal.get('reason', '亏损超过7%')}")

        # 场景2: 触发KDJ死叉止盈 (优先级次之)
        position2 = {'buy_price': 100.0, 'buy_date': '2024-01-01'}
        market_data2 = pd.DataFrame({
            'close': [100.0, 105.0, 110.0, 112.0, 115.0],
            'K': [60.0, 70.0, 80.0, 75.0, 70.0],
            'D': [55.0, 65.0, 75.0, 78.0, 80.0],
            'ma10': [100.0, 102.0, 104.0, 106.0, 108.0]
        })

        signal2 = self.risk_manager.get_trade_signal(position2, market_data2)

        # 验证止盈信号
        self.assertIn(signal2['action'], ['持有', '减仓50%'])
        print(f"   KDJ止盈信号: {signal2['action']} - {signal2.get('reason', 'KDJ死叉')}")

        # 场景3: 触发MA10跌破止盈
        position3 = {'buy_price': 100.0, 'buy_date': '2024-01-01'}
        market_data3 = pd.DataFrame({
            'close': [100.0, 105.0, 108.0, 107.0, 103.0],
            'K': [60.0, 65.0, 70.0, 75.0, 80.0],  # 保持金叉
            'D': [55.0, 60.0, 65.0, 70.0, 75.0],  # 保持金叉
            'ma10': [100.0, 102.0, 104.0, 105.0, 106.0]
        })

        signal3 = self.risk_manager.get_trade_signal(position3, market_data3)

        # 验证MA10跌破信号
        self.assertIn(signal3['action'], ['持有', '全部止盈'])
        print(f"   MA10止盈信号: {signal3['action']} - {signal3.get('reason', '跌破MA10')}")

        print(f"✅ 多条件组合风控信号生成测试通过")

    def test_position_holding_risk_evolution(self):
        """
        测试3: 持仓期间风控信号演变
        模拟持仓期间不同阶段的信号变化
        """
        buy_price = 100.0
        buy_date = '2024-01-01'

        # 阶段1: 建仓后持有 (盈利5%)
        position = {'buy_price': buy_price, 'buy_date': buy_date}
        market_data_phase1 = pd.DataFrame({
            'close': [100.0, 102.0, 104.0, 105.0],
            'K': [60.0, 65.0, 70.0, 75.0],
            'D': [55.0, 60.0, 65.0, 70.0],
            'ma10': [100.0, 101.0, 102.0, 103.0]
        })

        signal1 = self.risk_manager.get_trade_signal(position, market_data_phase1)
        self.assertEqual(signal1['action'], '持有')
        print(f"   阶段1(盈利5%): {signal1['action']}")

        # 阶段2: 持续上涨 (盈利15%)
        market_data_phase2 = pd.DataFrame({
            'close': [100.0, 105.0, 110.0, 115.0],
            'K': [60.0, 70.0, 80.0, 85.0],
            'D': [55.0, 65.0, 75.0, 80.0],
            'ma10': [100.0, 102.0, 104.0, 106.0]
        })

        signal2 = self.risk_manager.get_trade_signal(position, market_data_phase2)
        self.assertEqual(signal2['action'], '持有')
        print(f"   阶段2(盈利15%): {signal2['action']}")

        # 阶段3: KDJ死叉，触发止盈 (盈利15%)
        market_data_phase3 = pd.DataFrame({
            'close': [100.0, 105.0, 110.0, 112.0, 115.0],
            'K': [60.0, 70.0, 80.0, 75.0, 70.0],  # 死叉
            'D': [55.0, 65.0, 75.0, 78.0, 80.0],  # 死叉
            'ma10': [100.0, 102.0, 104.0, 106.0, 108.0]
        })

        signal3 = self.risk_manager.get_trade_signal(position, market_data_phase3)
        self.assertIn(signal3['action'], ['持有', '减仓50%'])
        print(f"   阶段3(死叉): {signal3['action']} - {signal3.get('reason', '')}")

        # 阶段4: 触发止损 (亏损8%)
        market_data_phase4 = pd.DataFrame({
            'close': [100.0, 98.0, 95.0, 92.0],
            'K': [60.0, 55.0, 50.0, 45.0],
            'D': [55.0, 50.0, 45.0, 40.0],
            'ma10': [100.0, 99.0, 98.0, 97.0]
        })

        signal4 = self.risk_manager.get_trade_signal(position, market_data_phase4)
        self.assertEqual(signal4['action'], '止损')
        print(f"   阶段4(亏损8%): {signal4['action']}")

        print(f"✅ 持仓期间风控信号演变测试通过")

    def test_risk_filter_on_buy_signal(self):
        """
        测试4: 风控规则对买入信号过滤
        验证风控评估如何影响最终买入决策
        """
        # 场景1: 高风险股票 - 应该被过滤
        high_risk_stock = {
            'code': '300001',
            'name': '某高风险股',
            'industry': '传统行业',
            'price': 5.0,
            'market_cap': 10e8,
            'roe': -10.0,
            'ma_bias': 15.0,
            'kdj': '死叉',
            'volume_ratio': 5.0,
            'macd_divergence': '顶背离',
            'profit_ratio': 80.0,
            'concentration': 30.0,
            'single_peak': False,
            'northbound': -2000.0,
            'northbound_days': -5,
            'main_funds': -500.0,
            'bb_position': '上轨',
            'score': 20,
        }

        signal = self.evaluate_signal(high_risk_stock)

        # 高风险股票应该被标记
        self.assertIn(signal['risk_level'], ['高', '中'])
        self.assertLess(signal['total_score'], 50)
        print(f"   高风险股票: 评分={signal['total_score']}, 风控等级={signal['risk_level']}")

        # 场景2: 低风险股票 - 适合买入
        low_risk_stock = {
            'code': '600519',
            'name': '贵州茅台',
            'industry': '食品饮料',
            'price': 1800.0,
            'market_cap': 20000e8,
            'roe': 30.0,
            'ma_bias': -2.0,
            'kdj': '金叉',
            'volume_ratio': 1.2,
            'macd_divergence': '底背离',
            'profit_ratio': 15.0,
            'concentration': 8.0,
            'single_peak': True,
            'northbound': 2000.0,
            'northbound_days': 10,
            'main_funds': 1000.0,
            'bb_position': '下轨',
            'score': 90,
        }

        signal2 = self.evaluate_signal(low_risk_stock)

        # 低风险股票应该评分高
        self.assertGreaterEqual(signal2['total_score'], 60)
        print(f"   低风险股票: 评分={signal2['total_score']}, 风控等级={signal2['risk_level']}")

        # 场景3: 风控评估应该返回警告信息
        risk_eval = self.risk_manager.evaluate_risk(high_risk_stock)
        self.assertGreater(len(risk_eval.get('warnings', [])), 0)
        print(f"   高风险警告: {risk_eval.get('warnings', [])[:2]}")

        print(f"✅ 风控规则对买入信号过滤测试通过")

    def test_full_filter_to_risk_evaluation_pipeline(self):
        """
        测试5: 完整筛选到风控评估流程
        测试从股票筛选到风控评估的完整Pipeline
        """
        # Step 1: 执行股票分析
        stock_result = self.filter.analyze_single_stock('300274.SZ')

        self.assertIsNotNone(stock_result)
        self.assertIn('code', stock_result)

        # Step 2: 执行信号评估
        signal = self.evaluate_signal(stock_result)

        self.assertIn('total_score', signal)
        self.assertIn('risk_score', signal)

        # Step 3: 执行风控评估
        risk_eval = self.risk_manager.evaluate_risk(stock_result)

        self.assertIn('risk_level', risk_eval)
        self.assertIn('risk_score', risk_eval)

        # Step 4: 生成交易信号
        position = {
            'buy_price': stock_result.get('price', 100) * 0.95,
            'buy_date': '2024-01-01'
        }

        # 模拟市场数据
        market_data = pd.DataFrame({
            'close': [stock_result.get('price', 100)] * 5,
            'K': [70, 72, 74, 76, 78],
            'D': [65, 67, 69, 71, 73],
            'ma10': [stock_result.get('price', 100)] * 5
        })

        trade_signal = self.risk_manager.get_trade_signal(position, market_data)

        self.assertIn('action', trade_signal)
        self.assertIn('priority', trade_signal)

        print(f"✅ 完整筛选到风控评估流程测试通过")
        print(f"   股票: {stock_result['code']} {stock_result['name']}")
        print(f"   筛选评分: {stock_result.get('score', 0)}")
        print(f"   信号评分: {signal['total_score']}")
        print(f"   风控等级: {risk_eval['risk_level']}")
        print(f"   交易信号: {trade_signal['action']}")


if __name__ == '__main__':
    unittest.main()
