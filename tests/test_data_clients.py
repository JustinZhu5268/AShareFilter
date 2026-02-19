#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据客户端测试
功能：
1. 各数据客户端单元测试
2. 客户端集成测试
3. Mock数据一致性测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import numpy as np
from api.tushare_client import TushareClient
from api.data_holder_trade import HolderTradeClient
from api.data_holder_number import HolderNumberClient
from api.data_main_business import MainBusinessClient
from api.data_limit_list import LimitListClient
from api.data_stk_redeem import StkRedeemClient
from api.data_margin import MarginClient
from api.data_inst_holder import InstHolderClient
from api.data_longhu_bang import LongHuBangClient


class TestDataClients(unittest.TestCase):
    """数据客户端测试"""

    def setUp(self):
        """测试前准备"""
        # 使用Mock模式
        self.tushare_client = TushareClient(use_mock=True)

    def test_tushare_client_stock_list(self):
        """测试Tushare客户端获取股票列表"""
        df = self.tushare_client.get_stock_list()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('ts_code', df.columns)
        print(f"✅ 获取股票列表: {len(df)}只")

    def test_tushare_client_market_cap(self):
        """测试Tushare客户端获取市值"""
        cap = self.tushare_client.get_market_cap('300274.SZ')
        self.assertIsInstance(cap, (int, float))
        print(f"✅ 获取市值数据: {cap}")

    def test_tushare_client_financial(self):
        """测试Tushare客户端获取财务数据"""
        data = self.tushare_client.get_financial_ttm('300274.SZ')
        self.assertIsInstance(data, dict)
        self.assertIn('roe_ttm', data)
        print(f"✅ 获取财务数据: ROE_TTM={data.get('roe_ttm')}")


class TestHolderTradeClient(unittest.TestCase):
    """股东增减持客户端测试"""

    def setUp(self):
        self.client = HolderTradeClient(use_mock=True)

    def test_get_holder_trade(self):
        """测试获取股东增减持数据"""
        df = self.client.get_holder_trade('300274.SZ')
        self.assertIsInstance(df, pd.DataFrame)
        print(f"✅ 股东增减持数据: {len(df)}条")

    def test_get_holder_trade_summary(self):
        """测试获取增减持汇总"""
        summary = self.client.get_holder_trade_summary('300274.SZ')
        self.assertIsInstance(summary, dict)
        print(f"✅ 增减持汇总: {summary}")

    def test_get_recent_increase(self):
        """测试近期是否有增持"""
        result = self.client.get_recent_increase('300274.SZ', days=30)
        self.assertIsInstance(result, bool)
        print(f"✅ 近期增持: {result}")


class TestHolderNumberClient(unittest.TestCase):
    """股东人数客户端测试"""

    def setUp(self):
        self.client = HolderNumberClient(use_mock=True)

    def test_get_holder_number(self):
        """测试获取股东人数"""
        data = self.client.get_holder_number('300274.SZ')
        self.assertIsInstance(data, dict)
        print(f"✅ 股东人数数据: {data}")

    def test_get_holder_number_change(self):
        """测试获取变化趋势"""
        change = self.client.get_holder_number_change('300274.SZ')
        self.assertIsInstance(change, dict)
        print(f"✅ 股东人数变化: {change}")

    def test_is_holder_concentrated(self):
        """测试股东集中度"""
        result = self.client.is_holder_concentrated('300274.SZ', threshold=-10.0)
        self.assertIsInstance(result, bool)
        print(f"✅ 股东集中: {result}")


class TestMainBusinessClient(unittest.TestCase):
    """主营业务客户端测试"""

    def setUp(self):
        self.client = MainBusinessClient(use_mock=True)

    def test_get_main_business(self):
        """测试获取主营业务"""
        data = self.client.get_main_business('300274.SZ')
        self.assertIsInstance(data, dict)
        print(f"✅ 主营业务: {data}")

    def test_is_pure_industry_leader(self):
        """测试行业龙头判断"""
        result = self.client.is_pure_industry_leader('600519.SH', ['白酒', '酒'])
        self.assertIsInstance(result, bool)
        print(f"✅ 行业龙头: {result}")


class TestLimitListClient(unittest.TestCase):
    """涨跌停客户端测试"""

    def setUp(self):
        self.client = LimitListClient(use_mock=True)

    def test_get_limit_list(self):
        """测试获取涨跌停数据"""
        df = self.client.get_limit_list()
        self.assertIsInstance(df, pd.DataFrame)
        print(f"✅ 涨跌停数据: {len(df)}条")

    def test_is_limit_up(self):
        """测试是否涨停"""
        result = self.client.is_limit_up('300274.SZ')
        self.assertIsInstance(result, dict)
        print(f"✅ 涨停状态: {result}")

    def test_is_limit_down(self):
        """测试是否跌停"""
        result = self.client.is_limit_down('300274.SZ')
        self.assertIsInstance(result, bool)
        print(f"✅ 跌停状态: {result}")

    def test_get_limit_stats(self):
        """测试获取统计信息"""
        stats = self.client.get_limit_stats('300274.SZ', days=30)
        self.assertIsInstance(stats, dict)
        print(f"✅ 涨跌停统计: {stats}")


class TestStkRedeemClient(unittest.TestCase):
    """限售股解禁客户端测试"""

    def setUp(self):
        self.client = StkRedeemClient(use_mock=True)

    def test_get_redeem_info(self):
        """测试获取解禁信息"""
        df = self.client.get_redeem_info('300274.SZ')
        self.assertIsInstance(df, pd.DataFrame)
        print(f"✅ 解禁信息: {len(df)}条")

    def test_get_upcoming_redeem(self):
        """测试是否有即将解禁"""
        df = self.client.get_upcoming_redeem('300274.SZ', days=90)
        self.assertIsInstance(df, pd.DataFrame)
        print(f"✅ 即将解禁: {len(df)}条")

    def test_get_redeem_risk_level(self):
        """测试风险等级"""
        level = self.client.get_redeem_risk_level('300274.SZ')
        self.assertIsInstance(level, str)
        print(f"✅ 解禁风险: {level}")


class TestMarginClient(unittest.TestCase):
    """融资融券客户端测试"""

    def setUp(self):
        self.client = MarginClient(use_mock=True)

    def test_get_margin_data(self):
        """测试获取融资融券数据"""
        df = self.client.get_margin_data('300274.SZ')
        self.assertIsInstance(df, pd.DataFrame)
        print(f"✅ 融资融券数据: {len(df)}条")

    def test_get_margin_balance(self):
        """测试获取融资余额"""
        balance = self.client.get_margin_balance('300274.SZ')
        self.assertIsInstance(balance, dict)
        print(f"✅ 融资余额: {balance}")

    def test_is_margin_high(self):
        """测试融资占比"""
        result = self.client.is_margin_high('300274.SZ', threshold=0.3)
        self.assertIsInstance(result, bool)
        print(f"✅ 融资占比高: {result}")


class TestInstHolderClient(unittest.TestCase):
    """机构持仓客户端测试"""

    def setUp(self):
        self.client = InstHolderClient(use_mock=True)

    def test_get_inst_holder(self):
        """测试获取机构持仓"""
        data = self.client.get_inst_holder('300274.SZ')
        self.assertIsInstance(data, dict)
        print(f"✅ 机构持仓: {data}")

    def test_get_inst_holder_ratio(self):
        """测试获取机构持股比例"""
        ratio = self.client.get_inst_holder_ratio('300274.SZ')
        self.assertIsInstance(ratio, (int, float, type(None)))
        print(f"✅ 机构持股比例: {ratio}")

    def test_is_institution_holding(self):
        """测试是否有机构持仓"""
        result = self.client.is_institution_holding('300274.SZ', threshold=5.0)
        self.assertIsInstance(result, bool)
        print(f"✅ 机构持股: {result}")


class TestLongHuBangClient(unittest.TestCase):
    """龙虎榜客户端测试"""

    def setUp(self):
        self.client = LongHuBangClient(use_mock=True)

    def test_get_longhu_bang(self):
        """测试获取龙虎榜数据"""
        data = self.client.get_longhu_bang('300274.SZ')
        self.assertIsInstance(data, dict)
        print(f"✅ 龙虎榜数据: {data}")

    def test_get_longhu_count(self):
        """测试获取上榜次数"""
        count = self.client.get_longhu_count('300274.SZ', days=30)
        self.assertIsInstance(count, int)
        print(f"✅ 上榜次数: {count}")

    def test_is_longhu_stock(self):
        """测试是否龙虎榜股票"""
        result = self.client.is_longhu_stock('300274.SZ', days=30)
        self.assertIsInstance(result, bool)
        print(f"✅ 龙虎榜股票: {result}")


class TestMockDataConsistency(unittest.TestCase):
    """Mock数据一致性测试"""

    def test_mock_data_structure(self):
        """测试Mock数据结构"""
        from data.mock_data import generate_mock_stock_list
        df = generate_mock_stock_list()
        # 验证必需字段
        required_fields = ['ts_code', 'symbol', 'name', 'industry', 'list_date']
        for field in required_fields:
            self.assertIn(field, df.columns, f"缺少字段: {field}")
        print("✅ Mock数据结构正确")

    def test_mock_financial_ttm(self):
        """测试Mock财务数据"""
        from data.mock_data import generate_mock_financial_ttm
        df = generate_mock_financial_ttm()
        # 验证必需字段
        required_fields = ['ts_code', 'ann_date', 'end_date', 'roe']
        for field in required_fields:
            self.assertIn(field, df.columns, f"缺少字段: {field}")
        print("✅ Mock财务数据字段正确")

    def test_mock_daily_data(self):
        """测试Mock日线数据"""
        from data.mock_data import generate_mock_daily_data
        df = generate_mock_daily_data('300274.SZ')
        # 验证必需字段
        required_fields = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol']
        for field in required_fields:
            self.assertIn(field, df.columns, f"缺少字段: {field}")
        print("✅ Mock日线数据字段正确")


if __name__ == '__main__':
    unittest.main()
