"""
限售股解禁数据模块单元测试
"""

import unittest
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.data_stk_redeem import StkRedeemClient, get_stk_redeem_client, reset_stk_redeem_client


class TestStkRedeem(unittest.TestCase):
    """限售股解禁数据测试"""

    def setUp(self):
        """测试前准备"""
        reset_stk_redeem_client()
        self.client = StkRedeemClient(use_mock=True)

    def test_get_redeem_info(self):
        """测试获取限售股解禁信息"""
        df = self.client.get_redeem_info('300274.SZ')

        # 验证返回类型
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_upcoming_redeem(self):
        """测试获取即将解禁的股票"""
        df = self.client.get_upcoming_redeem('300274.SZ', days=90)

        self.assertIsInstance(df, pd.DataFrame)

    def test_has_upcoming_redeem(self):
        """测试检查是否有即将解禁"""
        result = self.client.has_upcoming_redeem('300274.SZ', days=30)

        self.assertIsInstance(result, bool)

    def test_get_redeem_risk_level(self):
        """测试获取解禁风险等级"""
        result = self.client.get_redeem_risk_level('300274.SZ', days=90)

        self.assertIsInstance(result, str)
        self.assertIn(result, ['high', 'medium', 'low'])

    def test_runtime_cache(self):
        """测试运行时缓存"""
        ts_code = '300274.SZ'

        # 第一次调用
        df1 = self.client.get_redeem_info(ts_code)

        # 第二次调用应该从缓存获取
        df2 = self.client.get_redeem_info(ts_code)

        # 验证缓存工作正常
        if not df1.empty:
            pd.testing.assert_frame_equal(df1, df2)


class TestStkRedeemClient(unittest.TestCase):
    """StkRedeemClient客户端测试"""

    def test_client_init(self):
        """测试客户端初始化"""
        client = StkRedeemClient(use_mock=True)
        self.assertTrue(client.use_mock)

    def test_get_client(self):
        """测试获取全局客户端"""
        client1 = get_stk_redeem_client(use_mock=True)
        client2 = get_stk_redeem_client(use_mock=True)

        # 应该是同一个实例
        self.assertIs(client1, client2)

    def test_reset_client(self):
        """测试重置客户端"""
        client1 = get_stk_redeem_client(use_mock=True)
        reset_stk_redeem_client()
        client2 = get_stk_redeem_client(use_mock=True)

        # 重置后应该是新实例
        self.assertIsNot(client1, client2)


if __name__ == '__main__':
    unittest.main()
