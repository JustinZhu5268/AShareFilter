"""
融资融券数据模块单元测试
"""

import unittest
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.data_margin import MarginClient, get_margin_client, reset_margin_client


class TestMargin(unittest.TestCase):
    """融资融券数据测试"""

    def setUp(self):
        """测试前准备"""
        reset_margin_client()
        self.client = MarginClient(use_mock=True)

    def test_get_margin_data(self):
        """测试获取融资融券数据"""
        df = self.client.get_margin_data('300274.SZ')

        # 验证返回类型
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_margin_balance(self):
        """测试获取融资余额"""
        result = self.client.get_margin_balance('300274.SZ')

        self.assertIsInstance(result, dict)
        self.assertIn('rzye', result)
        self.assertIn('rqye', result)
        self.assertIn('rzrqye', result)
        self.assertIn('rz_rate', result)

    def test_get_margin_trend(self):
        """测试获取融资趋势"""
        result = self.client.get_margin_trend('300274.SZ', days=10)

        self.assertIsInstance(result, dict)
        self.assertIn('rz_change', result)
        self.assertIn('rz_change_pct', result)
        self.assertIn('trend', result)
        self.assertIn(result['trend'], ['increasing', 'decreasing', 'stable'])

    def test_is_margin_high(self):
        """测试融资占比判断"""
        result = self.client.is_margin_high('300274.SZ', threshold=0.3)

        self.assertIsInstance(result, bool)

    def test_runtime_cache(self):
        """测试运行时缓存"""
        ts_code = '300274.SZ'

        # 第一次调用
        df1 = self.client.get_margin_data(ts_code)

        # 第二次调用应该从缓存获取
        df2 = self.client.get_margin_data(ts_code)

        # 验证缓存工作正常
        if not df1.empty:
            pd.testing.assert_frame_equal(df1, df2)


class TestMarginClient(unittest.TestCase):
    """MarginClient客户端测试"""

    def test_client_init(self):
        """测试客户端初始化"""
        client = MarginClient(use_mock=True)
        self.assertTrue(client.use_mock)

    def test_get_client(self):
        """测试获取全局客户端"""
        client1 = get_margin_client(use_mock=True)
        client2 = get_margin_client(use_mock=True)

        # 应该是同一个实例
        self.assertIs(client1, client2)

    def test_reset_client(self):
        """测试重置客户端"""
        client1 = get_margin_client(use_mock=True)
        reset_margin_client()
        client2 = get_margin_client(use_mock=True)

        # 重置后应该是新实例
        self.assertIsNot(client1, client2)


if __name__ == '__main__':
    unittest.main()
