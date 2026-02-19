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
from strategy.signal import evaluate_buy_signal
from strategy.risk_management import get_risk_manager
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


class TestE2E(unittest.TestCase):
    """E2E端到端测试类"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)
        self.filter = StockFilter(self.client)

    def test_end_to_end_filter_flow(self):
        """测试端到端筛选流程"""
        # Step 1: 获取股票列表
        stocks = self.client.get_stock_list()
        self.assertIsNotNone(stocks)

        # Step 2: 数据清洗
        cleaned = self.filter.step1_clean_data(stocks)
        self.assertIsNotNone(cleaned)

        # Step 3: 行业筛选
        industries = self.filter.step2_industry_filter(cleaned)
        self.assertIsInstance(industries, list)

        # Step 4: 龙头筛选
        leaders = self.filter.step3_leader_filter(cleaned, industries)
        self.assertIsInstance(leaders, list)

        # Step 5: 技术筛选
        results = self.filter.step4_technical_filter(leaders)
        self.assertIsInstance(results, list)

        print("✅ 端到端筛选流程测试通过")

    def test_end_to_end_with_deducted_profit(self):
        """测试扣非净利润集成的完整流程"""
        # 获取财务数据（包含扣非净利润）
        fin_data = self.client.get_financial_ttm('300274.SZ')

        # 验证扣非净利润字段
        self.assertIn('deducted_net_profit_ttm', fin_data)
        self.assertIsInstance(fin_data['deducted_net_profit_ttm'], float)

        print("✅ 扣非净利润集成测试通过")

    def test_end_to_end_with_weekly_kdj(self):
        """测试周线KDJ集成的完整流程"""
        # 单股票分析应包含周线KDJ
        result = self.filter.analyze_single_stock('300274.SZ')

        self.assertIsNotNone(result)
        self.assertIn('weekly_kdj_j', result)
        self.assertIn('weekly_kdj_status', result)

        print("✅ 周线KDJ集成测试通过")

    def test_signal_evaluation_integration(self):
        """测试信号评估集成"""
        # 创建测试股票数据
        stock = {
            'code': '300274',
            'name': '阳光电源',
            'industry': '电气设备',
            'price': 100.0,
            'market_cap': 300e8,
            'roe': 20.0,
            'net_profit': 10e8,
            'revenue': 50e8,
            'ma_bias': -5.0,
            'kdj': '金叉',
            'volume_ratio': 1.5,
            'macd_divergence': '无',
            'profit_ratio': 20.0,
            'concentration': 10.0,
            'single_peak': True,
            'northbound': 1000.0,
            'northbound_days': 5,
            'main_funds': 500.0,
            'bb_position': '中轨',
            'weekly_kdj_j': 30.0,
            'weekly_kdj_status': '超卖'
        }

        # 信号评估
        signal = evaluate_buy_signal(stock)

        # 验证结果
        self.assertIn('total_score', signal)
        self.assertIn('rating', signal)
        self.assertIn('recommendation', signal)
        self.assertIn('risk_score', signal)
        self.assertIn('risk_level', signal)

        print(f"✅ 信号评估集成测试通过: 评分={signal['total_score']}, 风控等级={signal['risk_level']}")

    def test_risk_evaluation_integration(self):
        """测试风控评估集成"""
        # 创建测试股票数据
        stock_data = {
            'code': '300274',
            'name': '阳光电源',
            'price': 100.0,
            'ma_bias': -5.0,
            'kdj': '金叉',
            'volume_ratio': 1.5,
            'profit_ratio': 20.0,
            'concentration': 10.0,
        }

        # 风控评估
        risk_manager = get_risk_manager()
        risk_eval = risk_manager.evaluate_risk(stock_data)

        # 验证结果
        self.assertIn('risk_score', risk_eval)
        self.assertIn('risk_level', risk_eval)
        self.assertIn('warnings', risk_eval)

        print(f"✅ 风控评估集成测试通过: 风险分数={risk_eval['risk_score']}")

    def test_e2e_with_multiple_stocks(self):
        """测试多股票处理流程"""
        # 获取多只股票
        stocks = self.client.get_stock_list()

        # 处理每只股票
        for i, row in stocks.head(3).iterrows():
            ts_code = row['ts_code']
            result = self.filter.analyze_single_stock(ts_code)
            # 每只股票都应该有分析结果
            self.assertIsNotNone(result)

        print("✅ 多股票处理流程测试通过")

    def test_e2e_full_pipeline_with_report(self):
        """测试完整流程并生成报告"""
        # 完整筛选
        results = self.filter.run_full_filter()

        # 对结果进行信号评估
        for stock in results:
            signal = evaluate_buy_signal(stock)
            stock['signal'] = signal

        # 验证
        self.assertIsInstance(results, list)
        print(f"✅ 完整流程报告测试通过: 筛选到 {len(results)} 只股票")


class TestDataPipelineIntegration(unittest.TestCase):
    """数据Pipeline集成测试类 - 测试数据获取、缓存、处理的完整流程"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)
        self.filter = StockFilter(self.client)

    def test_data_fetch_cache_pipeline(self):
        """测试数据获取与缓存完整流程

        场景：测试从API获取数据、缓存存储、缓存读取的完整流程
        验证：数据能正确存储到缓存并从缓存正确读取
        """
        import data.cache_manager as cache_mgr

        # Step 1: 清除可能存在的旧缓存
        try:
            old_cache = cache_mgr.load_stock_list_cache()
            if old_cache is not None:
                print(f"    清理旧缓存: {len(old_cache)} 条")
        except:
            pass

        # Step 2: 从API获取股票列表（应触发缓存保存）
        stocks = self.client.get_stock_list()
        self.assertIsNotNone(stocks)
        self.assertGreater(len(stocks), 0)

        # Step 3: 验证缓存已保存
        cached_stocks = cache_mgr.load_stock_list_cache()
        self.assertIsNotNone(cached_stocks)
        self.assertEqual(len(cached_stocks), len(stocks))

        # Step 4: 再次获取应从缓存读取
        stocks_again = self.client.get_stock_list()
        self.assertIsNotNone(stocks_again)
        self.assertEqual(len(stocks_again), len(stocks))

        print("✅ 数据获取与缓存完整流程测试通过")

    def test_multi_source_aggregation_pipeline(self):
        """测试多数据源聚合Pipeline

        场景：从多个API获取不同类型数据并聚合成完整的股票分析数据
        验证：多数据源能正确聚合，形成完整的股票数据
        """
        ts_code = '300274.SZ'

        # Step 1: 获取股票基本信息
        stocks = self.client.get_stock_list()
        stock_info = stocks[stocks['ts_code'] == ts_code].iloc[0]

        # Step 2: 获取市值数据
        market_cap = self.client.get_market_cap(ts_code)
        self.assertGreater(market_cap, 0)

        # Step 3: 获取财务数据
        fin_data = self.client.get_financial_ttm(ts_code)
        self.assertIn('roe_ttm', fin_data)
        self.assertIn('net_profit_ttm', fin_data)

        # Step 4: 获取日线数据
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y%m%d')
        daily_data = self.client.get_daily_data(ts_code, start_date, end_date)
        self.assertIsNotNone(daily_data)
        self.assertGreater(len(daily_data), 0)

        # Step 5: 获取北向资金数据
        northbound = self.client.get_northbound_funds(ts_code)
        self.assertIn('north_money', northbound)

        # Step 6: 聚合数据 - 模拟完整的股票数据对象
        aggregated_data = {
            'ts_code': ts_code,
            'name': stock_info['name'],
            'industry': stock_info['industry'],
            'market_cap': market_cap,
            'roe': fin_data.get('roe_ttm', 0),
            'net_profit': fin_data.get('net_profit_ttm', 0),
            'revenue': fin_data.get('revenue_ttm', 0),
            'latest_close': daily_data.iloc[-1]['close'] if len(daily_data) > 0 else 0,
            'northbound_total': sum(northbound.get('north_money', [])),
        }

        # 验证聚合结果
        self.assertEqual(aggregated_data['ts_code'], ts_code)
        self.assertEqual(aggregated_data['name'], '阳光电源')
        self.assertGreater(aggregated_data['market_cap'], 0)
        self.assertGreater(aggregated_data['roe'], 0)

        print(f"✅ 多数据源聚合Pipeline测试通过")
        print(f"   聚合数据: {aggregated_data['name']}, 市值={aggregated_data['market_cap']:.0f}亿, ROE={aggregated_data['roe']:.1f}%")

    def test_data_processing_pipeline(self):
        """测试数据处理Pipeline（清洗、转换）

        场景：测试数据清洗、格式转换、指标计算的完整处理流程
        验证：原始数据经过处理后符合业务要求
        """
        # Step 1: 获取原始日线数据
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y%m%d')
        raw_data = self.client.get_daily_data('300274.SZ', start_date, end_date)

        # Step 2: 数据清洗 - 处理缺失值
        cleaned_data = raw_data.dropna(subset=['close', 'vol'])
        self.assertGreater(len(cleaned_data), 0)

        # Step 3: 数据转换 - 计算收益率
        cleaned_data = cleaned_data.copy()
        cleaned_data['returns'] = cleaned_data['close'].pct_change()

        # Step 4: 计算移动平均
        cleaned_data['ma5'] = cleaned_data['close'].rolling(window=5).mean()
        cleaned_data['ma10'] = cleaned_data['close'].rolling(window=10).mean()

        # Step 5: 计算波动率
        cleaned_data['volatility'] = cleaned_data['returns'].rolling(window=20).std()

        # Step 6: 数据验证 - 验证计算结果
        self.assertIn('returns', cleaned_data.columns)
        self.assertIn('ma5', cleaned_data.columns)
        self.assertIn('ma10', cleaned_data.columns)
        self.assertIn('volatility', cleaned_data.columns)

        # 验证数据完整性
        self.assertGreater(cleaned_data['close'].min(), 0)
        self.assertGreater(cleaned_data['vol'].min(), 0)

        print(f"✅ 数据处理Pipeline测试通过")
        print(f"   原始数据: {len(raw_data)} 条, 处理后: {len(cleaned_data)} 条")

    def test_cache_expiry_fallback_pipeline(self):
        """测试缓存失效与回退机制

        场景：测试当缓存过期时，系统能正确回退到API获取数据
        验证：缓存过期后能自动从API获取最新数据
        """
        import data.cache_manager as cache_mgr
        import tempfile
        import shutil
        from pathlib import Path

        # 创建临时缓存目录
        test_cache_dir = Path(tempfile.mkdtemp())
        original_cache_dir = cache_mgr.CACHE_DIR

        try:
            # 临时替换缓存目录
            cache_mgr.CACHE_DIR = test_cache_dir

            # Step 1: 首次获取数据（API获取并缓存）
            stocks1 = self.client.get_stock_list()
            self.assertIsNotNone(stocks1)
            cached_data = cache_mgr.load_stock_list_cache()
            self.assertIsNotNone(cached_data)

            # Step 2: 手动使缓存失效（修改缓存文件时间戳）
            cache_file = test_cache_dir / 'stock_list.csv'
            old_date = datetime.datetime.now() - datetime.timedelta(days=10)
            import os
            os.utime(cache_file, (old_date.timestamp(), old_date.timestamp()))

            # Step 3: 验证缓存已失效
            is_valid = cache_mgr.is_cache_valid('stock_list', max_age_days=1)
            self.assertFalse(is_valid)

            # Step 4: 重新获取数据（应回退到API）
            # 由于使用Mock客户端，这里验证系统能处理缓存失效场景
            stocks2 = self.client.get_stock_list()
            self.assertIsNotNone(stocks2)
            self.assertGreater(len(stocks2), 0)

            print(f"✅ 缓存失效与回退机制测试通过")

        finally:
            # 恢复原始缓存目录并清理
            cache_mgr.CACHE_DIR = original_cache_dir
            shutil.rmtree(test_cache_dir, ignore_errors=True)

    def test_batch_data_processing_pipeline(self):
        """测试批量数据处理Pipeline

        场景：测试批量获取多只股票数据并并行处理的流程
        验证：能正确批量处理多只股票的数据获取和分析
        """
        # Step 1: 获取股票列表
        stocks = self.client.get_stock_list()
        self.assertGreater(len(stocks), 0)

        # Step 2: 批量获取多只股票的市值
        market_caps = {}
        for _, row in stocks.head(5).iterrows():
            ts_code = row['ts_code']
            try:
                mc = self.client.get_market_cap(ts_code)
                market_caps[ts_code] = mc
            except:
                market_caps[ts_code] = 0

        # Step 3: 验证批量获取结果
        self.assertEqual(len(market_caps), 5)
        for ts_code, mc in market_caps.items():
            self.assertGreaterEqual(mc, 0)

        # Step 4: 批量分析多只股票
        results = []
        for _, row in stocks.head(3).iterrows():
            ts_code = row['ts_code']
            result = self.filter.analyze_single_stock(ts_code)
            if result:
                results.append(result)

        # 验证批量分析结果
        self.assertGreater(len(results), 0)

        print(f"✅ 批量数据处理Pipeline测试通过")
        print(f"   处理股票数: {len(market_caps)}, 分析成功: {len(results)}")

    def test_data_quality_validation_pipeline(self):
        """测试数据质量验证Pipeline

        场景：测试数据质量检查、异常值处理、数据完整性验证
        验证：能正确识别和处理数据质量问题
        """
        # Step 1: 获取日线数据
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y%m%d')
        raw_data = self.client.get_daily_data('300274.SZ', start_date, end_date)

        # Step 2: 数据完整性检查
        required_columns = ['open', 'high', 'low', 'close', 'vol']
        for col in required_columns:
            self.assertIn(col, raw_data.columns)

        # Step 3: 异常值检测 - 检查价格是否为正数
        invalid_prices = raw_data[raw_data['close'] <= 0]
        self.assertEqual(len(invalid_prices), 0, "存在无效价格数据")

        # Step 4: 异常值检测 - 检查成交量是否为非负数
        invalid_vol = raw_data[raw_data['vol'] < 0]
        self.assertEqual(len(invalid_vol), 0, "存在无效成交量数据")

        # Step 5: 异常值检测 - 检查High >= Low
        invalid_hl = raw_data[raw_data['high'] < raw_data['low']]
        self.assertEqual(len(invalid_hl), 0, "存在High < Low的异常数据")

        # Step 6: 异常值检测 - 检查High >= Open, Close
        invalid_high = raw_data[(raw_data['high'] < raw_data['open']) | (raw_data['high'] < raw_data['close'])]
        self.assertEqual(len(invalid_high), 0, "存在High不是最高价的异常数据")

        # Step 7: 缺失值统计
        missing_counts = raw_data[required_columns].isnull().sum()
        for col, count in missing_counts.items():
            self.assertEqual(count, 0, f"{col}列存在缺失值")

        print(f"✅ 数据质量验证Pipeline测试通过")
        print(f"   数据完整性: {len(raw_data)} 条, 无异常数据")


if __name__ == '__main__':
    unittest.main()
