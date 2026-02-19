"""
股东人数数据模块单元测试
"""

import unittest
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.data_holder_number import HolderNumberClient, get_holder_number_client, reset_holder_number_client


class TestHolderNumber(unittest.TestCase):
    """股东人数数据测试"""

    def setUp(self):
        """测试前准备"""
        reset_holder_number_client()
        self.client = HolderNumberClient(use_mock=True)

    def test_get_holder_number(self):
        """测试获取股东人数"""
        result = self.client.get_holder_number('300274.SZ')

        # 验证返回类型
        self.assertIsInstance(result, dict)

        # 验证必要字段
        required_fields = ['holder_num', 'end_date', 'change', 'change_ratio']
        for field in required_fields:
            self.assertIn(field, result, f"缺少必要字段: {field}")

        # 验证数据类型
        self.assertIsInstance(result['holder_num'], int)
        self.assertIsInstance(result['change_ratio'], float)

    def test_get_holder_number_change(self):
        """测试获取股东人数变化趋势"""
        result = self.client.get_holder_number_change('300274.SZ', periods=4)

        # 验证返回类型
        self.assertIsInstance(result, dict)

        # 验证必要字段
        required_fields = ['current_num', 'previous_num', 'change', 'change_ratio', 'trend', 'quarters']
        for field in required_fields:
            self.assertIn(field, result, f"缺少必要字段: {field}")

        # 验证趋势类型
        self.assertIn(result['trend'], ['increasing', 'decreasing', 'stable'])

    def test_is_holder_concentrated(self):
        """测试股东集中度判断"""
        result = self.client.is_holder_concentrated('300274.SZ', threshold=-10.0)

        self.assertIsInstance(result, bool)

    def test_empty_stock(self):
        """测试不存在的股票"""
        result = self.client.get_holder_number('999999.SZ')

        # Mock数据会返回模拟数据，验证类型正确
        self.assertIsInstance(result['holder_num'], int)
        self.assertGreater(result['holder_num'], 0)

    def test_runtime_cache(self):
        """测试运行时缓存"""
        ts_code = '300274.SZ'

        # 第一次调用
        result1 = self.client.get_holder_number(ts_code)

        # 第二次调用应该从缓存获取
        result2 = self.client.get_holder_number(ts_code)

        # 验证缓存工作正常
        self.assertEqual(result1, result2)

    def test_different_stocks(self):
        """测试不同股票返回数据"""
        result1 = self.client.get_holder_number('300274.SZ')
        result2 = self.client.get_holder_number('600519.SH')

        # Mock数据可能相同，验证类型正确
        self.assertIsInstance(result1['holder_num'], int)
        self.assertIsInstance(result2['holder_num'], int)


class TestHolderNumberClient(unittest.TestCase):
    """HolderNumberClient客户端测试"""

    def test_client_init(self):
        """测试客户端初始化"""
        client = HolderNumberClient(use_mock=True)
        self.assertTrue(client.use_mock)

    def test_get_client(self):
        """测试获取全局客户端"""
        client1 = get_holder_number_client(use_mock=True)
        client2 = get_holder_number_client(use_mock=True)

        # 应该是同一个实例
        self.assertIs(client1, client2)

    def test_reset_client(self):
        """测试重置客户端"""
        client1 = get_holder_number_client(use_mock=True)
        reset_holder_number_client()
        client2 = get_holder_number_client(use_mock=True)

        # 重置后应该是新实例
        self.assertIsNot(client1, client2)


if __name__ == '__main__':
    unittest.main()
