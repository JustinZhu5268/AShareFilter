"""
股东增减持数据模块单元测试
"""

import unittest
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.data_holder_trade import HolderTradeClient, get_holder_trade_client, reset_holder_trade_client


class TestHolderTrade(unittest.TestCase):
    """股东增减持数据测试"""

    def setUp(self):
        """测试前准备"""
        reset_holder_trade_client()
        self.client = HolderTradeClient(use_mock=True)

    def test_get_holder_trade(self):
        """测试获取股东增减持数据"""
        df = self.client.get_holder_trade('300274.SZ')

        # 验证返回类型
        self.assertIsInstance(df, pd.DataFrame)

        # 验证非空
        self.assertFalse(df.empty)

        # 验证必要字段存在
        expected_columns = ['ts_code', 'ann_date', 'holder_name', 'holder_type', 'holder_vol']
        for col in expected_columns:
            self.assertIn(col, df.columns, f"缺少必要字段: {col}")

    def test_holder_trade_date_filter(self):
        """测试日期过滤"""
        df = self.client.get_holder_trade('300274.SZ', start_date='20250101', end_date='20251231')

        self.assertIsInstance(df, pd.DataFrame)

    def test_holder_trade_summary(self):
        """测试增减持摘要统计"""
        summary = self.client.get_holder_trade_summary('300274.SZ', days=90)

        # 验证返回类型
        self.assertIsInstance(summary, dict)

        # 验证必要字段
        required_fields = ['total_increase', 'total_decrease', 'total_increase_amount',
                          'total_decrease_amount', 'net_change', 'recent_increase']
        for field in required_fields:
            self.assertIn(field, summary, f"缺少必要字段: {field}")

        # 验证数据类型
        self.assertIsInstance(summary['total_increase'], int)
        self.assertIsInstance(summary['recent_increase'], bool)

    def test_recent_increase(self):
        """测试近期增持检查"""
        result = self.client.get_recent_increase('300274.SZ', days=30)

        self.assertIsInstance(result, bool)

    def test_empty_stock(self):
        """测试不存在的股票"""
        df = self.client.get_holder_trade('999999.SZ')

        # 应该返回空DataFrame
        self.assertIsInstance(df, pd.DataFrame)

    def test_runtime_cache(self):
        """测试运行时缓存"""
        ts_code = '300274.SZ'

        # 第一次调用
        df1 = self.client.get_holder_trade(ts_code)

        # 第二次调用应该从缓存获取
        df2 = self.client.get_holder_trade(ts_code)

        # 验证缓存工作正常
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_stocks(self):
        """测试不同股票返回不同数据"""
        df1 = self.client.get_holder_trade('300274.SZ')
        df2 = self.client.get_holder_trade('600519.SH')

        # 不同股票应该返回不同数据
        self.assertFalse(df1.equals(df2))


class TestHolderTradeClient(unittest.TestCase):
    """HolderTradeClient客户端测试"""

    def test_client_init(self):
        """测试客户端初始化"""
        client = HolderTradeClient(use_mock=True)
        self.assertTrue(client.use_mock)

    def test_get_client(self):
        """测试获取全局客户端"""
        client1 = get_holder_trade_client(use_mock=True)
        client2 = get_holder_trade_client(use_mock=True)

        # 应该是同一个实例
        self.assertIs(client1, client2)

    def test_reset_client(self):
        """测试重置客户端"""
        client1 = get_holder_trade_client(use_mock=True)
        reset_holder_trade_client()
        client2 = get_holder_trade_client(use_mock=True)

        # 重置后应该是新实例
        self.assertIsNot(client1, client2)


if __name__ == '__main__':
    unittest.main()
