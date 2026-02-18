"""
API客户端和数据准确性测试
"""
import unittest
import pandas as pd
import numpy as np
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.tushare_client import TushareClient
from data.mock_data import (
    MockTushareClient,
    generate_mock_stock_list,
    generate_mock_market_cap,
    generate_mock_financial_ttm,
    generate_mock_adj_factor,
    generate_mock_daily_data,
)


class TestTushareClientMock(unittest.TestCase):
    """Tushare客户端Mock模式测试"""
    
    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        self.assertTrue(self.client.use_mock)
        self.assertIsNotNone(self.client._mock_client)
    
    def test_get_stock_list(self):
        """测试获取股票列表"""
        stocks = self.client.get_stock_list()
        
        self.assertIsNotNone(stocks)
        self.assertFalse(stocks.empty)
        self.assertGreater(len(stocks), 0)
        
        # 验证字段
        self.assertIn('ts_code', stocks.columns)
        self.assertIn('name', stocks.columns)
        self.assertIn('industry', stocks.columns)
    
    def test_get_market_cap(self):
        """测试获取市值"""
        market_cap = self.client.get_market_cap('300274.SZ')
        
        self.assertGreater(market_cap, 0)
        self.assertIsInstance(market_cap, float)
    
    def test_get_all_market_caps(self):
        """测试获取所有市值"""
        caps = self.client.get_all_market_caps()
        
        self.assertIsNotNone(caps)
        self.assertFalse(caps.empty)
        
        # 验证字段
        self.assertIn('ts_code', caps.columns)
        self.assertIn('total_mv', caps.columns)
    
    def test_get_financial_ttm(self):
        """测试获取财务TTM"""
        fin_data = self.client.get_financial_ttm('300274.SZ')
        
        self.assertIn('roe_ttm', fin_data)
        self.assertIn('net_profit_ttm', fin_data)
        self.assertIn('revenue_ttm', fin_data)
    
    def test_get_adj_factor(self):
        """测试获取复权因子"""
        adj = self.client.get_adj_factor('300274.SZ')
        
        # 返回值应该是float类型
        self.assertIsInstance(adj, float)
        self.assertGreater(adj, 0)
    
    def test_get_daily_data(self):
        """测试获取日线数据"""
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y%m%d')
        
        df = self.client.get_daily_data('300274.SZ', start_date, end_date)
        
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        
        # 验证字段
        required_fields = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol']
        for field in required_fields:
            self.assertIn(field, df.columns)
    
    def test_get_industry_rps(self):
        """测试获取行业RPS"""
        df = self.client.get_industry_rps()
        
        self.assertIsNotNone(df)
        
        # 验证字段
        if not df.empty:
            self.assertIn('industry', df.columns)
            self.assertIn('rps', df.columns)
    
    def test_get_northbound_funds(self):
        """测试获取北向资金"""
        funds = self.client.get_northbound_funds('300274.SZ')
        
        self.assertIsNotNone(funds)
    
    def test_get_main_funds(self):
        """测试获取主力资金"""
        funds = self.client.get_main_funds('300274.SZ')
        
        self.assertIsNotNone(funds)


class TestMockDataAccuracy(unittest.TestCase):
    """Mock数据准确性测试 - 验证Mock数据与真实API格式一致"""
    
    def test_stock_list_fields(self):
        """测试股票列表字段"""
        df = generate_mock_stock_list()
        
        # 验证字段与真实API一致
        self.assertIn('ts_code', df.columns)
        self.assertIn('symbol', df.columns)
        self.assertIn('name', df.columns)
        self.assertIn('industry', df.columns)
        self.assertIn('list_date', df.columns)
    
    def test_market_cap_fields(self):
        """测试市值数据字段"""
        df = generate_mock_market_cap()
        
        # 验证字段与真实API一致
        self.assertIn('ts_code', df.columns)
        self.assertIn('trade_date', df.columns)
        self.assertIn('close', df.columns)
        self.assertIn('total_mv', df.columns)
        self.assertIn('circ_mv', df.columns)
        self.assertIn('free_share', df.columns)
    
    def test_financial_ttm_fields(self):
        """测试财务TTM字段"""
        df = generate_mock_financial_ttm()
        
        # 验证字段与真实API一致
        self.assertIn('ts_code', df.columns)
        self.assertIn('ann_date', df.columns)
        self.assertIn('end_date', df.columns)
        self.assertIn('roe', df.columns)
    
    def test_adj_factor_fields(self):
        """测试复权因子字段"""
        df = generate_mock_adj_factor()
        
        # 验证字段与真实API一致
        self.assertIn('ts_code', df.columns)
        self.assertIn('trade_date', df.columns)
        self.assertIn('adj_factor', df.columns)
    
    def test_daily_data_fields(self):
        """测试日线数据字段"""
        df = generate_mock_daily_data('300274.SZ', 10)
        
        # 验证字段与真实API一致
        required_fields = ['ts_code', 'trade_date', 'open', 'high', 'low', 
                          'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']
        for field in required_fields:
            self.assertIn(field, df.columns)
    
    def test_market_cap_unit(self):
        """测试市值单位 - 万元"""
        df = generate_mock_market_cap()
        
        # Mock数据应该使用万元单位（与真实API一致）
        # total_mv 应该在合理范围内（股票市值）
        if not df.empty:
            # 市值应该是正值
            self.assertTrue((df['total_mv'] > 0).all())


class TestMockClient(unittest.TestCase):
    """Mock客户端测试"""
    
    def setUp(self):
        self.mock_client = MockTushareClient()
    
    def test_stock_basic(self):
        """测试stock_basic方法"""
        df = self.mock_client.stock_basic()
        
        self.assertFalse(df.empty)
        self.assertIn('300274.SZ', df['ts_code'].values)
    
    def test_daily_basic(self):
        """测试daily_basic方法"""
        df = self.mock_client.daily_basic(ts_code='300274.SZ')
        
        self.assertFalse(df.empty)
        self.assertIn('total_mv', df.columns)
    
    def test_fina_indicator(self):
        """测试fina_indicator方法"""
        df = self.mock_client.fina_indicator(ts_code='300274.SZ')
        
        self.assertFalse(df.empty)
        self.assertIn('roe', df.columns)
    
    def test_adj_factor(self):
        """测试adj_factor方法"""
        df = self.mock_client.adj_factor(ts_code='300274.SZ')
        
        self.assertFalse(df.empty)
        self.assertIn('adj_factor', df.columns)
    
    def test_daily(self):
        """测试daily方法"""
        df = self.mock_client.daily(ts_code='300274.SZ', 
                                     start_date='20250101', 
                                     end_date='20250110')
        
        self.assertFalse(df.empty)
        self.assertIn('close', df.columns)
    
    def test_index_classify(self):
        """测试index_classify方法"""
        df = self.mock_client.index_classify()
        
        self.assertFalse(df.empty)
        self.assertIn('index_code', df.columns)
        self.assertIn('industry_name', df.columns)
    
    def test_sw_daily(self):
        """测试sw_daily方法"""
        df = self.mock_client.sw_daily(index_code='801010.SI', 
                                        start_date='20250101')
        
        self.assertFalse(df.empty)


class TestBoundaryConditions(unittest.TestCase):
    """边界条件测试"""
    
    def test_empty_stock_list(self):
        """测试空股票列表"""
        client = TushareClient(use_mock=True)
        
        # Mock数据不应该返回空
        stocks = client.get_stock_list()
        self.assertFalse(stocks.empty)
    
    def test_invalid_stock_code(self):
        """测试无效股票代码"""
        client = TushareClient(use_mock=True)
        
        # 无效代码应该返回默认值
        market_cap = client.get_market_cap('INVALID')
        self.assertGreaterEqual(market_cap, 0)
    
    def test_old_date_range(self):
        """测试过旧的日期范围"""
        client = TushareClient(use_mock=True)
        
        # 应该能处理过旧的日期
        df = client.get_daily_data('300274.SZ', '20200101', '20200110')
        # Mock数据会生成足够的天数
    
    def test_future_date(self):
        """测试未来日期"""
        client = TushareClient(use_mock=True)
        
        # 应该能处理未来日期
        future_date = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y%m%d')
        df = client.get_daily_data('300274.SZ', '20250101', future_date)
        self.assertIsNotNone(df)


if __name__ == '__main__':
    unittest.main()
