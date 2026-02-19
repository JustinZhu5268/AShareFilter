#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机构持仓数据单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
from api.data_inst_holder import InstHolderClient, get_inst_holder_client, reset_inst_holder_client


class TestInstHolderClient(unittest.TestCase):
    """机构持仓数据客户端测试"""

    def setUp(self):
        """测试前准备"""
        # 使用Mock模式
        self.client = InstHolderClient(use_mock=True)
        reset_inst_holder_client()

    def test_get_inst_holder(self):
        """测试获取机构持仓数据"""
        result = self.client.get_inst_holder('300274.SZ')

        self.assertIsInstance(result, dict)
        self.assertIn('holder_num', result)
        self.assertIn('hold_ratio', result)
        self.assertIn('change_ratio', result)
        self.assertIn('end_date', result)
        self.assertIn('institutions', result)

        print(f"✅ 机构持仓数据: {result}")

    def test_get_inst_holder_different_stocks(self):
        """测试不同股票的机构持仓数据"""
        stocks = ['300274.SZ', '000001.SZ', '600519.SH']

        for stock in stocks:
            result = self.client.get_inst_holder(stock)
            self.assertIsInstance(result, dict)
            self.assertGreaterEqual(result['holder_num'], 0)
            self.assertGreaterEqual(result['hold_ratio'], 0.0)
            print(f"✅ {stock} 机构持仓: 机构数={result['holder_num']}, 持股比例={result['hold_ratio']}%")

    def test_get_inst_holder_ratio(self):
        """测试获取机构持股比例"""
        ratio = self.client.get_inst_holder_ratio('300274.SZ')

        self.assertIsInstance(ratio, float)
        self.assertGreaterEqual(ratio, 0.0)
        print(f"✅ 机构持股比例: {ratio}%")

    def test_is_institution_holding(self):
        """测试机构持股阈值判断"""
        # 测试默认阈值5%
        result = self.client.is_institution_holding('300274.SZ')
        self.assertIsInstance(result, bool)

        # 测试自定义阈值
        result_high = self.client.is_institution_holding('300274.SZ', threshold=50.0)
        self.assertFalse(result_high)

        result_low = self.client.is_institution_holding('300274.SZ', threshold=0.1)
        self.assertIsInstance(result_low, bool)

        print(f"✅ 机构持股阈值判断测试通过")

    def test_get_inst_holder_trend(self):
        """测试机构持仓趋势"""
        result = self.client.get_inst_holder_trend('300274.SZ')

        self.assertIsInstance(result, dict)
        self.assertIn('current_ratio', result)
        self.assertIn('previous_ratio', result)
        self.assertIn('change', result)
        self.assertIn('trend', result)
        self.assertIn('periods', result)

        # 验证趋势值
        self.assertIn(result['trend'], ['increasing', 'decreasing', 'stable'])

        print(f"✅ 机构持仓趋势: 当前={result['current_ratio']}%, 趋势={result['trend']}")

    def test_runtime_cache(self):
        """测试运行时缓存"""
        ts_code = '300274.SZ'

        # 第一次调用
        result1 = self.client.get_inst_holder(ts_code)

        # 第二次调用应该从缓存获取
        result2 = self.client.get_inst_holder(ts_code)

        self.assertEqual(result1, result2)
        print(f"✅ 运行时缓存工作正常")

    def test_empty_stock_code(self):
        """测试空股票代码"""
        result = self.client.get_inst_holder('')

        self.assertIsInstance(result, dict)
        # 空代码应该返回默认数据
        self.assertGreaterEqual(result['holder_num'], 0)
        print(f"✅ 空股票代码处理正常")

    def test_mock_data_format(self):
        """测试Mock数据格式"""
        result = self.client.get_inst_holder('600519.SH')

        # 验证返回字段
        self.assertIsInstance(result['holder_num'], int)
        self.assertIsInstance(result['hold_ratio'], float)
        self.assertIsInstance(result['change_ratio'], float)
        self.assertIsInstance(result['institutions'], list)

        print(f"✅ Mock数据格式正确")


class TestInstHolderIntegration(unittest.TestCase):
    """机构持仓集成测试"""

    def setUp(self):
        """测试前准备"""
        self.client = get_inst_holder_client(use_mock=True)
        reset_inst_holder_client()

    def test_client_singleton(self):
        """测试客户端单例模式"""
        client1 = get_inst_holder_client()
        client2 = get_inst_holder_client()

        self.assertIs(client1, client2)
        print(f"✅ 单例模式正常")

    def test_batch_stocks(self):
        """测试批量股票查询"""
        stocks = ['300274.SZ', '000001.SZ', '600519.SH', '000002.SZ', '600036.SH']

        results = {}
        for stock in stocks:
            ratio = self.client.get_inst_holder_ratio(stock)
            results[stock] = ratio

        self.assertEqual(len(results), len(stocks))
        for stock, ratio in results.items():
            print(f"  {stock}: {ratio}%")

        print(f"✅ 批量查询完成: {len(results)} 只股票")


class TestInstHolderAdvanced(unittest.TestCase):
    """机构持仓高级功能测试"""

    def setUp(self):
        """测试前准备"""
        self.client = get_inst_holder_client(use_mock=True)
        reset_inst_holder_client()

    def test_inst_holder_trend_analysis(self):
        """测试机构持仓趋势分析"""
        ts_code = '300274.SZ'

        # 获取趋势数据
        trend = self.client.get_inst_holder_trend(ts_code, periods=4)

        # 验证返回结构
        self.assertIn('current_ratio', trend)
        self.assertIn('previous_ratio', trend)
        self.assertIn('change', trend)
        self.assertIn('trend', trend)
        self.assertIn('periods', trend)

        # 验证趋势值有效
        self.assertIn(trend['trend'], ['increasing', 'decreasing', 'stable'])
        print(f"✅ 趋势分析: 当前={trend['current_ratio']}%, 趋势={trend['trend']}")

    def test_inst_holder_trend_increasing(self):
        """测试机构增持趋势"""
        # 创建模拟的增持数据
        ts_code = '600519.SH'
        trend = self.client.get_inst_holder_trend(ts_code)

        # 验证数据格式
        self.assertIsInstance(trend['change'], float)
        self.assertIsInstance(trend['periods'], list)
        print(f"✅ 机构增持趋势测试通过")

    def test_is_institution_holding_various_thresholds(self):
        """测试不同阈值的机构持股判断"""
        ts_code = '300274.SZ'

        # 测试默认阈值5%
        result_5 = self.client.is_institution_holding(ts_code, threshold=5.0)
        self.assertIsInstance(result_5, bool)

        # 测试10%阈值
        result_10 = self.client.is_institution_holding(ts_code, threshold=10.0)
        self.assertIsInstance(result_10, bool)

        # 测试1%阈值
        result_1 = self.client.is_institution_holding(ts_code, threshold=1.0)
        self.assertIsInstance(result_1, bool)

        # 验证逻辑：低阈值更容易通过
        self.assertGreaterEqual(result_1, result_5)
        self.assertGreaterEqual(result_5, result_10)

        print(f"✅ 多阈值测试: 1%={result_1}, 5%={result_5}, 10%={result_10}")

    def test_inst_holder_cache_invalidation(self):
        """测试缓存失效机制"""
        ts_code = '300274.SZ'

        # 第一次调用
        result1 = self.client.get_inst_holder(ts_code)

        # 验证缓存工作 - 缓存键有前缀
        cache_key = f"inst_holder_{ts_code}"
        self.assertIn(cache_key, self.client._runtime_cache)

        # 清除缓存
        self.client._runtime_cache.clear()

        # 再次调用应该重新获取
        result2 = self.client.get_inst_holder(ts_code)
        self.assertEqual(result1, result2)

        print(f"✅ 缓存失效机制测试通过")

    def test_inst_holder_multiple_periods(self):
        """测试多期数据查询"""
        ts_code = '300274.SZ'

        # 获取4期数据
        trend_4 = self.client.get_inst_holder_trend(ts_code, periods=4)
        self.assertEqual(len(trend_4['periods']), min(4, len(trend_4['periods'])))

        # 获取8期数据
        trend_8 = self.client.get_inst_holder_trend(ts_code, periods=8)
        self.assertLessEqual(len(trend_8['periods']), 8)

        print(f"✅ 多期数据: 4期={len(trend_4['periods'])}, 8期={len(trend_8['periods'])}")

    def test_inst_holder_empty_result_handling(self):
        """测试空结果处理"""
        # 测试不存在的股票
        result = self.client.get_inst_holder('999999.SZ')

        # 应该返回默认值而非抛出异常
        self.assertIsInstance(result, dict)
        # 注意：Mock数据可能返回默认值，需要验证字段存在
        self.assertIn('holder_num', result)
        self.assertIn('hold_ratio', result)
        self.assertIn('institutions', result)

        print(f"✅ 空结果处理正常")

    def test_inst_holder_trend_with_no_data(self):
        """测试无数据的趋势分析"""
        # Mock数据可能返回默认数据，测试其处理
        trend = self.client.get_inst_holder_trend('999999.SX', periods=4)

        # 应该返回有效结构
        self.assertIn('current_ratio', trend)
        self.assertIn('trend', trend)
        self.assertIn('periods', trend)

        print(f"✅ 无数据趋势分析测试通过")


class TestInstHolderDataQuality(unittest.TestCase):
    """机构持仓数据质量测试"""

    def setUp(self):
        """测试前准备"""
        self.client = InstHolderClient(use_mock=True)

    def test_data_types(self):
        """测试返回数据类型"""
        result = self.client.get_inst_holder('300274.SZ')

        # 验证类型正确
        self.assertIsInstance(result['holder_num'], int)
        self.assertIsInstance(result['hold_ratio'], float)
        self.assertIsInstance(result['change_ratio'], float)
        self.assertIsInstance(result['end_date'], str)
        self.assertIsInstance(result['institutions'], list)

        print(f"✅ 数据类型验证通过")

    def test_ratio_bounds(self):
        """测试持股比例边界"""
        stocks = ['300274.SZ', '000001.SZ', '600519.SH']

        for stock in stocks:
            result = self.client.get_inst_holder(stock)

            # 比例应该在合理范围内
            self.assertGreaterEqual(result['hold_ratio'], 0.0)
            self.assertLessEqual(result['hold_ratio'], 100.0)

            # 机构数量应该非负
            self.assertGreaterEqual(result['holder_num'], 0)

        print(f"✅ 比例边界验证通过")

    def test_change_ratio_calculation(self):
        """测试持股比例变化计算"""
        result = self.client.get_inst_holder('300274.SZ')

        # 变化比例可以是正负值
        self.assertIsInstance(result['change_ratio'], float)
        # 注意：不限制范围，因为可能大幅增持或减持

        print(f"✅ 变化比例: {result['change_ratio']}%")


class TestInstHolderMockVsReal(unittest.TestCase):
    """Mock vs Real 数据对比测试"""

    def test_mock_client_functionality(self):
        """测试Mock客户端功能"""
        mock_client = InstHolderClient(use_mock=True)
        result = mock_client.get_inst_holder('300274.SZ')

        # Mock应该返回有效数据
        self.assertIsInstance(result, dict)
        self.assertIn('holder_num', result)

        print(f"✅ Mock客户端功能正常")

    def test_real_client_fallback(self):
        """测试真实客户端降级处理"""
        # 创建一个非Mock客户端
        real_client = InstHolderClient(use_mock=False)

        # 测试返回结果是有效的（无论是否降级）
        result = real_client.get_inst_holder('300274.SZ')

        # 应该返回有效数据
        self.assertIsInstance(result, dict)
        self.assertIn('holder_num', result)

        print(f"✅ 真实客户端降级处理正常")


if __name__ == '__main__':
    unittest.main()
