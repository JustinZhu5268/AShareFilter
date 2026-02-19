"""
主营业务数据模块单元测试
"""

import unittest
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.data_main_business import MainBusinessClient, get_main_business_client, reset_main_business_client


class TestMainBusiness(unittest.TestCase):
    """主营业务数据测试"""

    def setUp(self):
        """测试前准备"""
        reset_main_business_client()
        self.client = MainBusinessClient(use_mock=True)

    def test_get_main_business(self):
        """测试获取主营业务"""
        result = self.client.get_main_business('300274.SZ')

        # 验证返回类型
        self.assertIsInstance(result, dict)

        # 验证必要字段
        required_fields = ['ts_code', 'end_date', 'businesses', 'main_business']
        for field in required_fields:
            self.assertIn(field, result, f"缺少必要字段: {field}")

        # 验证数据类型
        self.assertIsInstance(result['businesses'], list)
        self.assertIsInstance(result['main_business'], str)

    def test_check_business_match(self):
        """测试主营业务关键词匹配"""
        # 阳光电源应该匹配"光伏"、"太阳能"
        result = self.client.check_business_match('300274.SZ', ['光伏', '太阳能'])

        self.assertIsInstance(result, dict)
        self.assertIn('matched', result)
        self.assertIn('matched_keywords', result)
        self.assertIn('main_business', result)
        self.assertIn('match_details', result)

    def test_check_business_match_no_match(self):
        """测试主营业务不匹配"""
        result = self.client.check_business_match('300274.SZ', ['白酒', '银行'])

        # 阳光电源不匹配白酒或银行
        self.assertFalse(result['matched'])

    def test_is_pure_industry_leader(self):
        """测试行业龙头判断"""
        # 阳光电源是光伏行业龙头
        result = self.client.is_pure_industry_leader('300274.SZ', ['光伏', '太阳能', '发电'])

        self.assertTrue(result)

    def test_is_pure_industry_leader_not_match(self):
        """测试非行业龙头"""
        result = self.client.is_pure_industry_leader('300274.SZ', ['白酒', '银行'])

        self.assertFalse(result)

    def test_empty_keywords(self):
        """测试空关键词"""
        result = self.client.check_business_match('300274.SZ', [])

        self.assertFalse(result['matched'])

    def test_runtime_cache(self):
        """测试运行时缓存"""
        ts_code = '300274.SZ'

        # 第一次调用
        result1 = self.client.get_main_business(ts_code)

        # 第二次调用应该从缓存获取
        result2 = self.client.get_main_business(ts_code)

        # 验证缓存工作正常
        self.assertEqual(result1, result2)

    def test_different_stocks(self):
        """测试不同股票返回不同数据"""
        result1 = self.client.get_main_business('300274.SZ')
        result2 = self.client.get_main_business('600519.SH')

        # 不同股票主营业务应该不同
        self.assertNotEqual(result1['main_business'], result2['main_business'])


class TestMainBusinessClient(unittest.TestCase):
    """MainBusinessClient客户端测试"""

    def test_client_init(self):
        """测试客户端初始化"""
        client = MainBusinessClient(use_mock=True)
        self.assertTrue(client.use_mock)

    def test_get_client(self):
        """测试获取全局客户端"""
        client1 = get_main_business_client(use_mock=True)
        client2 = get_main_business_client(use_mock=True)

        # 应该是同一个实例
        self.assertIs(client1, client2)

    def test_reset_client(self):
        """测试重置客户端"""
        client1 = get_main_business_client(use_mock=True)
        reset_main_business_client()
        client2 = get_main_business_client(use_mock=True)

        # 重置后应该是新实例
        self.assertIsNot(client1, client2)


if __name__ == '__main__':
    unittest.main()
