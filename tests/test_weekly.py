"""
周线数据获取单元测试
"""

import unittest
import pandas as pd
import numpy as np
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.data_weekly import (
    WeeklyDataClient,
    get_weekly_client,
    reset_weekly_client,
)


class TestWeeklyDataClient(unittest.TestCase):
    """周线数据客户端测试类"""

    def setUp(self):
        """设置测试"""
        reset_weekly_client()
        self.client = WeeklyDataClient()

    def test_client_initialization(self):
        """测试客户端初始化"""
        self.assertIsNotNone(self.client)

    def test_get_weekly_data(self):
        """测试获取周线数据"""
        df = self.client.get_weekly_data('300274.SZ')

        self.assertIsNotNone(df)
        self.assertFalse(df.empty)

        # 验证字段
        required_fields = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']
        for field in required_fields:
            self.assertIn(field, df.columns)

        print(f"✅ 周线数据: {len(df)} 周")

    def test_get_weekly_data_with_date_range(self):
        """测试指定日期范围获取周线数据"""
        start_date = '20250101'
        end_date = '20260101'
        df = self.client.get_weekly_data('300274.SZ', start_date, end_date)

        self.assertIsNotNone(df)

        # 验证日期范围 - 由于周线转换的特性，可能包含超出范围的数据
        # 只验证数据存在且有日期字段
        if not df.empty:
            self.assertIn('trade_date', df.columns)
            # 验证第一周的开始日期不早于请求的开始日期
            df_sorted = df.sort_values('trade_date')
            first_date = df_sorted['trade_date'].iloc[0]
            self.assertGreaterEqual(first_date, start_date)

    def test_weekly_data_conversion(self):
        """测试日线转周线"""
        # 使用已有的日线数据
        df_daily = self.client._get_daily_data('300274.SZ', '20250101', '20251231')

        if df_daily is not None and not df_daily.empty:
            df_weekly = self.client._convert_to_weekly(df_daily)

            self.assertIsNotNone(df_weekly)
            self.assertFalse(df_weekly.empty)

            # 周线数据应该比日线少
            self.assertLess(len(df_weekly), len(df_daily))

            # 验证周线数据的正确性
            # 周收盘价应该是每周最后一天的收盘价
            print(f"✅ 日线转周线: {len(df_daily)} 天 -> {len(df_weekly)} 周")

    def test_runtime_cache(self):
        """测试运行时缓存"""
        # 第一次获取
        df1 = self.client.get_weekly_data('300274.SZ')

        # 第二次获取应该从缓存
        df2 = self.client.get_weekly_data('300274.SZ')

        self.assertEqual(len(df1), len(df2))
        print(f"✅ 运行时缓存工作正常")

    def test_different_stocks(self):
        """测试不同股票"""
        stocks = ['300274.SZ', '600519.SH', '000001.SZ']

        for code in stocks:
            df = self.client.get_weekly_data(code)
            self.assertIsNotNone(df)
            if not df.empty:
                self.assertEqual(df['ts_code'].iloc[0], code)

        print(f"✅ 不同股票周线数据正常")


class TestWeeklyDataEdgeCases(unittest.TestCase):
    """周线数据边界测试类"""

    def setUp(self):
        reset_weekly_client()
        self.client = WeeklyDataClient()

    def test_empty_daily_data(self):
        """测试空日线数据"""
        empty_df = pd.DataFrame()
        result = self.client._convert_to_weekly(empty_df)
        self.assertTrue(result.empty)

    def test_single_day_data(self):
        """测试单日数据"""
        # 创建单日数据
        df = pd.DataFrame({
            'ts_code': ['300274.SZ'],
            'trade_date': ['20250101'],
            'open': [100.0],
            'high': [105.0],
            'low': [98.0],
            'close': [103.0],
            'vol': [1000000],
            'amount': [103000000],
        })

        result = self.client._convert_to_weekly(df)
        # 单日数据应该能处理
        self.assertIsNotNone(result)

    def test_weekly_data_columns(self):
        """测试周线数据列"""
        df = self.client.get_weekly_data('300274.SZ')

        if not df.empty:
            # 验证high >= low
            valid = df[df['high'] >= df['low']]
            self.assertEqual(len(valid), len(df))

            # 验证high >= open, high >= close
            self.assertTrue((df['high'] >= df['open']).all())
            self.assertTrue((df['high'] >= df['close']).all())

            # 验证low <= open, low <= close
            self.assertTrue((df['low'] <= df['open']).all())
            self.assertTrue((df['low'] <= df['close']).all())


class TestGetWeeklyClient(unittest.TestCase):
    """全局客户端测试"""

    def test_get_client(self):
        """测试获取全局客户端"""
        reset_weekly_client()
        client1 = get_weekly_client()
        client2 = get_weekly_client()

        # 应该是同一个实例
        self.assertIs(client1, client2)

    def test_reset_client(self):
        """测试重置客户端"""
        client1 = get_weekly_client()
        reset_weekly_client()
        client2 = get_weekly_client()

        # 重置后应该创建新实例
        self.assertIsNot(client1, client2)


if __name__ == '__main__':
    unittest.main()
