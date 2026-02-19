"""
涨跌停数据模块单元测试
"""

import unittest
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.data_limit_list import LimitListClient, get_limit_list_client, reset_limit_list_client


class TestLimitList(unittest.TestCase):
    """涨跌停数据测试"""

    def setUp(self):
        """测试前准备"""
        reset_limit_list_client()
        self.client = LimitListClient(use_mock=True)

    def test_get_limit_list(self):
        """测试获取涨跌停记录"""
        df = self.client.get_limit_list('300274.SZ')

        # 验证返回类型
        self.assertIsInstance(df, pd.DataFrame)

    def test_is_limit_up(self):
        """测试涨停判断"""
        result = self.client.is_limit_up('300274.SZ')

        self.assertIsInstance(result, dict)
        self.assertIn('is_limit_up', result)
        self.assertIn('limit_type', result)
        self.assertIn('pct_chg', result)

    def test_is_limit_down(self):
        """测试跌停判断"""
        result = self.client.is_limit_down('300274.SZ')

        self.assertIsInstance(result, bool)

    def test_get_limit_stats(self):
        """测试涨跌停统计"""
        result = self.client.get_limit_stats('300274.SZ', days=30)

        self.assertIsInstance(result, dict)
        self.assertIn('limit_up_count', result)
        self.assertIn('limit_down_count', result)
        self.assertIn('total_limit', result)

    def test_is_locked_limit_up(self):
        """测试涨停锁筹判断"""
        result = self.client.is_locked_limit_up('300274.SZ', days=10)

        self.assertIsInstance(result, bool)

    def test_runtime_cache(self):
        """测试运行时缓存"""
        ts_code = '300274.SZ'

        # 第一次调用
        df1 = self.client.get_limit_list(ts_code)

        # 第二次调用应该从缓存获取
        df2 = self.client.get_limit_list(ts_code)

        # 验证缓存工作正常
        if not df1.empty:
            pd.testing.assert_frame_equal(df1, df2)


class TestLimitListClient(unittest.TestCase):
    """LimitListClient客户端测试"""

    def test_client_init(self):
        """测试客户端初始化"""
        client = LimitListClient(use_mock=True)
        self.assertTrue(client.use_mock)

    def test_get_client(self):
        """测试获取全局客户端"""
        client1 = get_limit_list_client(use_mock=True)
        client2 = get_limit_list_client(use_mock=True)

        # 应该是同一个实例
        self.assertIs(client1, client2)

    def test_reset_client(self):
        """测试重置客户端"""
        client1 = get_limit_list_client(use_mock=True)
        reset_limit_list_client()
        client2 = get_limit_list_client(use_mock=True)

        # 重置后应该是新实例
        self.assertIsNot(client1, client2)


if __name__ == '__main__':
    unittest.main()
