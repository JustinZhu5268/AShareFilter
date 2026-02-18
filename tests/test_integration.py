"""
集成测试 - 使用Mock数据测试完整流程
"""

import unittest
import datetime

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.tushare_client import TushareClient
from strategy.filter import StockFilter
from data.mock_data import (
    generate_mock_stock_list,
    generate_mock_daily_data,
)


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """设置测试"""
        # 使用Mock客户端
        self.client = TushareClient(use_mock=True)
    
    def test_mock_client_initialization(self):
        """测试Mock客户端初始化"""
        self.assertTrue(self.client.use_mock)
        print("✅ Mock客户端初始化成功")
    
    def test_get_stock_list(self):
        """测试获取股票列表"""
        stocks = self.client.get_stock_list()
        
        self.assertIsNotNone(stocks)
        self.assertFalse(stocks.empty)
        self.assertGreater(len(stocks), 0)
        print(f"✅ 获取股票列表: {len(stocks)} 只")
    
    def test_get_market_cap(self):
        """测试获取市值"""
        market_cap = self.client.get_market_cap('300274.SZ')
        
        self.assertGreater(market_cap, 0)
        print(f"✅ 获取市值: {market_cap:.0f} 亿")
    
    def test_get_financial_ttm(self):
        """测试获取财务数据"""
        fin_data = self.client.get_financial_ttm('300274.SZ')
        
        self.assertIn('roe_ttm', fin_data)
        self.assertIn('net_profit_ttm', fin_data)
        self.assertIn('revenue_ttm', fin_data)
        print(f"✅ 获取财务数据: ROE={fin_data['roe_ttm']:.1f}%")
    
    def test_get_daily_data(self):
        """测试获取日线数据"""
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=120)).strftime('%Y%m%d')
        
        df = self.client.get_daily_data('300274.SZ', start_date, end_date)
        
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        # Mock数据会生成所有请求的天数
        self.assertGreater(len(df), 0)
        print(f"✅ 获取日线数据: {len(df)} 条")
    
    def test_single_stock_analysis(self):
        """测试单股票分析"""
        # 创建筛选器
        filter_obj = StockFilter(self.client)
        
        # 分析300274
        result = filter_obj.analyze_single_stock('300274.SZ')
        
        self.assertIsNotNone(result)
        # 使用str转换处理numpy类型
        self.assertEqual(str(result['code']), '300274')
        self.assertEqual(result['name'], '阳光电源')
        
        # 检查关键字段
        self.assertIn('price', result)
        self.assertIn('roe', result)
        self.assertIn('ma_bias', result)
        self.assertIn('kdj', result)
        self.assertIn('profit_ratio', result)
        
        print(f"✅ 单股票分析完成")
        print(f"   代码: {result['code']} {result['name']}")
        print(f"   价格: {result['price']:.2f}")
        print(f"   ROE: {result['roe']:.1f}%")
        print(f"   乖离率: {result['ma_bias']:.1f}%")
        print(f"   KDJ: {result['kdj']}")
        print(f"   评分: {result['score']}")
    
    def test_full_filter_pipeline(self):
        """测试完整筛选流程"""
        # 创建筛选器
        filter_obj = StockFilter(self.client)
        
        # 运行完整筛选
        results = filter_obj.run_full_filter()
        
        # 验证结果
        self.assertIsInstance(results, list)
        
        if results:
            # 检查结果字段
            r = results[0]
            self.assertIn('code', r)
            self.assertIn('name', r)
            self.assertIn('industry', r)
            self.assertIn('price', r)
            self.assertIn('score', r)
            
            print(f"✅ 完整筛选流程完成")
            print(f"   符合条件: {len(results)} 只")
            for r in results:
                print(f"   - {r['code']} {r['name']}: 评分 {r['score']}")
        else:
            print("ℹ️ 没有股票符合所有条件")


class TestMockData(unittest.TestCase):
    """Mock数据测试类"""
    
    def test_generate_mock_stock_list(self):
        """测试生成Mock股票列表"""
        df = generate_mock_stock_list()
        
        self.assertFalse(df.empty)
        self.assertIn('300274.SZ', df['ts_code'].values)
        print(f"✅ Mock股票列表: {len(df)} 只")
    
    def test_generate_mock_daily_data(self):
        """测试生成Mock日线数据"""
        df = generate_mock_daily_data('300274.SZ', 120)
        
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 120)
        self.assertIn('open', df.columns)
        self.assertIn('close', df.columns)
        self.assertIn('vol', df.columns)
        print(f"✅ Mock日线数据: {len(df)} 条")


if __name__ == '__main__':
    unittest.main()
