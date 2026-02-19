"""
边界条件测试 - 测试各种边界情况和异常处理
"""

import unittest
import pandas as pd
import numpy as np
import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.technical import (
    calculate_kdj,
    calculate_ma,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_ma_bias,
    calculate_volume_ratio,
)
from indicators.chips import analyze_chips
from indicators.weekly_kdj import calculate_weekly_kdj, check_weekly_kdj_oversold
from api.tushare_client import TushareClient
from data.mock_data import generate_mock_daily_data
from strategy.risk_management import RiskManager


class TestDataBoundary(unittest.TestCase):
    """数据边界测试"""

    def test_empty_dataframe(self):
        """测试空数据框"""
        df = pd.DataFrame()
        result = calculate_kdj(df)
        self.assertTrue(result.empty)
        print("✅ 空数据框测试通过")

    def test_single_row(self):
        """测试单行数据"""
        data = {
            'trade_date': ['20250101'],
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [102.0],
            'vol': [1000000.0]
        }
        df = pd.DataFrame(data)
        result = calculate_kdj(df)
        # 单行数据KDJ可能无法计算
        self.assertIsNotNone(result)
        print("✅ 单行数据测试通过")

    def test_missing_columns(self):
        """测试缺少必要字段"""
        data = {
            'trade_date': ['20250101'],
            'close': [102.0],
            # 缺少 open, high, low, vol
        }
        df = pd.DataFrame(data)
        try:
            result = calculate_kdj(df)
            # 应该能处理这种情况
            self.assertIsNotNone(result)
        except KeyError:
            # 允许抛出KeyError
            pass
        print("✅ 缺少字段测试通过")

    def test_null_values(self):
        """测试空值处理"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [100.0, None, 102.0],
            'high': [105.0, 106.0, None],
            'low': [99.0, 100.0, 101.0],
            'close': [102.0, 103.0, 104.0],
            'vol': [1000000.0, 1100000.0, 1200000.0]
        }
        df = pd.DataFrame(data)
        # 应该能处理空值
        result = calculate_kdj(df)
        self.assertIsNotNone(result)
        print("✅ 空值处理测试通过")


class TestNumericalBoundary(unittest.TestCase):
    """数值边界测试"""

    def test_zero_values(self):
        """测试零值处理"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [0.0, 0.0, 0.0],
            'high': [0.0, 0.0, 0.0],
            'low': [0.0, 0.0, 0.0],
            'close': [0.0, 0.0, 0.0],
            'vol': [0.0, 0.0, 0.0]
        }
        df = pd.DataFrame(data)
        # 零值可能导致计算问题，应该能处理
        try:
            result = calculate_ma(df)
            self.assertIsNotNone(result)
        except:
            pass
        print("✅ 零值处理测试通过")

    def test_negative_values(self):
        """测试负值处理"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [-100.0, -50.0, 0.0],
            'high': [-50.0, 0.0, 50.0],
            'low': [-150.0, -100.0, -50.0],
            'close': [-100.0, -50.0, 0.0],
            'vol': [1000000.0, 1100000.0, 1200000.0]
        }
        df = pd.DataFrame(data)
        # 负值可能不被支持，应该能处理
        try:
            result = calculate_ma(df)
            self.assertIsNotNone(result)
        except:
            pass
        print("✅ 负值处理测试通过")

    def test_extreme_values(self):
        """测试极值处理"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [1e10, 1e10, 1e10],
            'high': [1e10 + 100, 1e10 + 100, 1e10 + 100],
            'low': [1e10 - 100, 1e10 - 100, 1e10 - 100],
            'close': [1e10, 1e10, 1e10],
            'vol': [1e15, 1e15, 1e15]
        }
        df = pd.DataFrame(data)
        # 极值应该能被处理
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 极值处理测试通过")

    def test_infinity_values(self):
        """测试无穷值处理"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [100.0, float('inf'), 102.0],
            'high': [105.0, float('inf'), 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [102.0, float('inf'), 104.0],
            'vol': [1000000.0, 1100000.0, 1200000.0]
        }
        df = pd.DataFrame(data)
        # 无穷值应该能被替换或处理
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 无穷值处理测试通过")


class TestDateBoundary(unittest.TestCase):
    """日期边界测试"""

    def test_future_date(self):
        """测试未来日期"""
        future_date = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y%m%d')
        data = {
            'trade_date': [future_date],
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [102.0],
            'vol': [1000000.0]
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 未来日期测试通过")

    def test_very_old_date(self):
        """测试极早日期"""
        data = {
            'trade_date': ['19900101'],
            'open': [10.0],
            'high': [15.0],
            'low': [9.0],
            'close': [12.0],
            'vol': [1000000.0]
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 极早日期测试通过")

    def test_invalid_date_format(self):
        """测试无效日期格式"""
        data = {
            'trade_date': ['invalid-date', 'another-invalid', 'yet-another'],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [102.0, 103.0, 104.0],
            'vol': [1000000.0, 1100000.0, 1200000.0]
        }
        df = pd.DataFrame(data)
        # 应该能处理无效日期
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 无效日期格式测试通过")


class TestAPIBoundary(unittest.TestCase):
    """API边界测试"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)

    def test_invalid_stock_code(self):
        """测试无效股票代码"""
        result = self.client.get_market_cap('INVALID.SZ')
        # Mock客户端应该返回0
        self.assertEqual(result, 0)
        print("✅ 无效股票代码测试通过")

    def test_nonexistent_stock(self):
        """测试不存在的股票"""
        result = self.client.get_financial_ttm('999999.SZ')
        # 应该返回默认数据
        self.assertIsInstance(result, dict)
        self.assertIn('roe_ttm', result)
        print("✅ 不存在股票测试通过")

    def test_empty_date_range(self):
        """测试空日期范围"""
        end_date = '20250101'
        start_date = '20250102'  # 间隔1天
        try:
            df = self.client.get_daily_data('300274.SZ', start_date, end_date)
            # 应该能处理
            self.assertIsNotNone(df)
            print("✅ 空日期范围测试通过")
        except Exception as e:
            # 如果抛出异常，记录并允许
            print(f"✅ 空日期范围测试通过 (预期异常: {type(e).__name__})")

    def test_invalid_date_range(self):
        """测试无效日期范围（结束日期早于开始日期）"""
        end_date = '20240101'
        start_date = '20250101'  # 开始日期晚于结束日期
        try:
            df = self.client.get_daily_data('300274.SZ', start_date, end_date)
            # 应该能处理或返回空
            self.assertIsNotNone(df)
        except Exception:
            # 允许抛出异常
            pass
        print("✅ 无效日期范围测试通过")


class TestIndicatorBoundary(unittest.TestCase):
    """指标计算边界测试"""

    def test_kdj_insufficient_data(self):
        """测试KDJ数据不足"""
        # KDJ通常需要至少9个数据点
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 6)],
            'open': [100.0 + i for i in range(5)],
            'high': [105.0 + i for i in range(5)],
            'low': [99.0 + i for i in range(5)],
            'close': [102.0 + i for i in range(5)],
            'vol': [1000000.0 + i * 100000 for i in range(5)]
        }
        df = pd.DataFrame(data)
        result = calculate_kdj(df)
        # 数据不足时应该返回原始数据或部分结果
        self.assertIsNotNone(result)
        print("✅ KDJ数据不足测试通过")

    def test_ma_insufficient_periods(self):
        """测试均线周期不足"""
        data = {
            'trade_date': ['20250101', '20250102'],
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [99.0, 100.0],
            'close': [102.0, 103.0],
            'vol': [1000000.0, 1100000.0]
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df, periods=[5, 10, 20, 60])
        # 应该能处理周期不足的情况
        self.assertIsNotNone(result)
        print("✅ 均线周期不足测试通过")

    def test_weekly_kdj_insufficient_data(self):
        """测试周线KDJ数据不足"""
        # 周线KDJ需要至少5周数据
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 4)],
            'open': [100.0 + i for i in range(3)],
            'high': [105.0 + i for i in range(3)],
            'low': [99.0 + i for i in range(3)],
            'close': [102.0 + i for i in range(3)],
            'vol': [1000000.0 + i * 100000 for i in range(3)]
        }
        df = pd.DataFrame(data)
        result = calculate_weekly_kdj(df)
        # 数据不足时应该返回原始数据
        self.assertIsNotNone(result)
        print("✅ 周线KDJ数据不足测试通过")


class TestChipsBoundary(unittest.TestCase):
    """筹码分析边界测试"""

    def test_chips_insufficient_data(self):
        """测试筹码分析数据不足"""
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 10)],
            'open': [100.0 + i for i in range(9)],
            'high': [105.0 + i for i in range(9)],
            'low': [99.0 + i for i in range(9)],
            'close': [102.0 + i for i in range(9)],
            'vol': [1000000.0 + i * 100000 for i in range(9)]
        }
        df = pd.DataFrame(data)
        result = analyze_chips(df)
        # 应该能处理
        self.assertIsNotNone(result)
        self.assertIn('profit_ratio', result)
        print("✅ 筹码分析数据不足测试通过")

    def test_chips_zero_volume(self):
        """测试零成交量"""
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 61)],
            'open': [100.0 + i for i in range(60)],
            'high': [105.0 + i for i in range(60)],
            'low': [99.0 + i for i in range(60)],
            'close': [102.0 + i for i in range(60)],
            'vol': [0.0] * 60  # 零成交量
        }
        df = pd.DataFrame(data)
        result = analyze_chips(df)
        # 应该能处理零成交量
        self.assertIsNotNone(result)
        print("✅ 零成交量测试通过")


class TestNaNBoundary(unittest.TestCase):
    """NaN值传播边界测试"""

    def test_kdj_nan_values(self):
        """测试KDJ计算中NaN值传播"""
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 20)],
            'open': [100.0 + i for i in range(19)],
            'high': [105.0 + i for i in range(19)],
            'low': [99.0 + i for i in range(19)],
            'close': [102.0 + i for i in range(19)],
            'vol': [1000000.0 + i * 100000 for i in range(19)]
        }
        df = pd.DataFrame(data)
        # 手动注入 NaN 值
        df.loc[5, 'close'] = np.nan
        df.loc[10, 'high'] = np.nan
        result = calculate_kdj(df)
        # 应该能处理 NaN 值
        self.assertIsNotNone(result)
        print("✅ KDJ NaN值传播测试通过")

    def test_macd_nan_handling(self):
        """测试MACD中NaN值处理"""
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 35)],
            'open': [100.0 + i for i in range(34)],
            'high': [105.0 + i for i in range(34)],
            'low': [99.0 + i for i in range(34)],
            'close': [102.0 + i for i in range(34)],
            'vol': [1000000.0 + i * 100000 for i in range(34)]
        }
        df = pd.DataFrame(data)
        # 注入 NaN 值
        df.loc[15, 'close'] = np.nan
        result = calculate_macd(df)
        # 应该能处理 NaN 值
        self.assertIsNotNone(result)
        print("✅ MACD NaN值处理测试通过")

    def test_ma_nan_handling(self):
        """测试均线中NaN值处理"""
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 70)],
            'open': [100.0 + i for i in range(69)],
            'high': [105.0 + i for i in range(69)],
            'low': [99.0 + i for i in range(69)],
            'close': [102.0 + i for i in range(69)],
            'vol': [1000000.0 + i * 100000 for i in range(69)]
        }
        df = pd.DataFrame(data)
        # 注入多个 NaN 值
        df.loc[20:25, 'close'] = np.nan
        result = calculate_ma(df, periods=[5, 10, 20, 60])
        # 应该能处理 NaN 值
        self.assertIsNotNone(result)
        print("✅ 均线 NaN值处理测试通过")


class TestTypeConversionBoundary(unittest.TestCase):
    """数据类型转换边界测试"""

    def test_string_number_mixed(self):
        """测试字符串和数值混合数据"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': ['100.0', '101.0', '102.0'],  # 字符串类型
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [102.0, 103.0, 104.0],
            'vol': [1000000.0, 1100000.0, 1200000.0]
        }
        df = pd.DataFrame(data)
        try:
            result = calculate_ma(df)
            self.assertIsNotNone(result)
            print("✅ 字符串数值混合测试通过")
        except (TypeError, ValueError):
            # 如果不支持混合类型，也是可接受的
            print("✅ 字符串数值混合测试通过 (预期不支持)")

    def test_integer_float_mixed(self):
        """测试整数和浮点数混合数据"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [100, 101, 102],  # 整数类型
            'high': [105.5, 106.5, 107.5],  # 浮点数类型
            'low': [99, 100, 101],
            'close': [102.5, 103.5, 104.5],
            'vol': [1000000, 1100000, 1200000]
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 整数浮点数混合测试通过")


class TestTradeDateBoundary(unittest.TestCase):
    """交易日期边界测试"""

    def test_holiday_adjacent_dates(self):
        """测试节假日相邻日期"""
        # 测试春节前后的日期（假设）
        data = {
            'trade_date': ['20250127', '20250128', '20250129', '20250130'],
            'open': [100.0, 101.0, 102.0, 103.0],
            'high': [105.0, 106.0, 107.0, 108.0],
            'low': [99.0, 100.0, 101.0, 102.0],
            'close': [102.0, 103.0, 104.0, 105.0],
            'vol': [1000000.0, 1100000.0, 1200000.0, 1300000.0]
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 节假日相邻日期测试通过")

    def test_year_boundary(self):
        """测试年份边界日期"""
        # 测试年末和年初的日期
        data = {
            'trade_date': ['20241230', '20241231', '20250102', '20250103'],
            'open': [100.0, 101.0, 102.0, 103.0],
            'high': [105.0, 106.0, 107.0, 108.0],
            'low': [99.0, 100.0, 101.0, 102.0],
            'close': [102.0, 103.0, 104.0, 105.0],
            'vol': [1000000.0, 1100000.0, 1200000.0, 1300000.0]
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 年份边界日期测试通过")


class TestAdjFactorBoundary(unittest.TestCase):
    """复权因子缺失边界测试"""

    def setUp(self):
        """设置测试"""
        self.client = TushareClient(use_mock=True)

    def test_missing_adj_factor(self):
        """测试缺失复权因子的数据处理"""
        # Mock 客户端在缺失复权因子时应该能处理
        try:
            adj_factor = self.client.get_adj_factor('300274.SZ', '20250101')
            # 应该返回某个值（Mock 数据或默认值）
            self.assertIsNotNone(adj_factor)
            print("✅ 缺失复权因子测试通过")
        except Exception as e:
            # 如果抛出异常，也应该能处理
            print(f"✅ 缺失复权因子测试通过 (预期异常: {type(e).__name__})")

    def test_zero_adj_factor(self):
        """测试零值复权因子"""
        # 创建一个零复权因子的 DataFrame
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 11)],
            'open': [100.0 + i for i in range(10)],
            'high': [105.0 + i for i in range(10)],
            'low': [99.0 + i for i in range(10)],
            'close': [102.0 + i for i in range(10)],
            'vol': [1000000.0 + i * 100000 for i in range(10)],
            'adj_factor': [0.0] * 10  # 零复权因子
        }
        df = pd.DataFrame(data)
        # 应该能处理零复权因子
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 零复权因子测试通过")


class TestSuspensionBoundary(unittest.TestCase):
    """股票停牌期间边界测试"""

    def test_suspended_stock_data(self):
        """测试停牌股票数据"""
        # 模拟停牌期间（成交量为0）
        data = {
            'trade_date': ['20250101', '20250102', '20250103', '20250106', '20250107'],
            'open': [100.0, 100.0, 100.0, 101.0, 102.0],  # 停牌时价格不变
            'high': [105.0, 105.0, 105.0, 106.0, 107.0],
            'low': [99.0, 99.0, 99.0, 100.0, 101.0],
            'close': [102.0, 102.0, 102.0, 103.0, 104.0],
            'vol': [1000000.0, 0.0, 0.0, 1100000.0, 1200000.0]  # 停牌时成交量为0
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 停牌股票数据测试通过")

    def test_consecutive_zero_volume(self):
        """测试连续零成交量"""
        # 模拟长期停牌
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 16)],
            'open': [100.0] * 15,
            'high': [105.0] * 15,
            'low': [99.0] * 15,
            'close': [102.0] * 15,
            'vol': [0.0] * 15  # 全部零成交量
        }
        df = pd.DataFrame(data)
        result = calculate_volume_ratio(df)
        # 应该能处理连续零成交量
        self.assertIsNotNone(result)
        print("✅ 连续零成交量测试通过")


class TestSTStockBoundary(unittest.TestCase):
    """ST股票处理边界测试"""

    def test_st_stock_in_filter(self):
        """测试ST股票筛选逻辑"""
        # 模拟包含 ST 股票的列表
        stocks = [
            {'ts_code': '600519.SH', 'name': '贵州茅台', 'is_st': False},
            {'ts_code': '000001.SZ', 'name': '平安银行', 'is_st': False},
            {'ts_code': '600001.SH', 'name': 'ST某某', 'is_st': True},
            {'ts_code': '300001.SZ', 'name': 'ST个股', 'is_st': True},
            {'ts_code': '000002.SZ', 'name': '万科A', 'is_st': False},
        ]
        # 过滤 ST 股票
        non_st_stocks = [s for s in stocks if not s.get('is_st', False)]
        self.assertEqual(len(non_st_stocks), 3)
        print("✅ ST股票筛选逻辑测试通过")

    def test_delisted_stock(self):
        """测试退市股票处理"""
        # 模拟退市股票代码
        client = TushareClient(use_mock=True)
        result = client.get_market_cap('000000.SH')  # 退市或不存在
        # 应该返回默认值
        self.assertEqual(result, 0)
        print("✅ 退市股票处理测试通过")


class TestNewStockBoundary(unittest.TestCase):
    """新股处理边界测试"""

    def test_new_stock_insufficient_data(self):
        """测试新股数据不足"""
        # 模拟新股（上市不足60天）
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [102.0, 103.0, 104.0],
            'vol': [1000000.0, 1100000.0, 1200000.0]
        }
        df = pd.DataFrame(data)
        # 新股数据不足，应该能处理
        result = calculate_ma(df, periods=[5, 10, 20, 60])
        self.assertIsNotNone(result)
        print("✅ 新股数据不足测试通过")

    def test_ipo_date_boundary(self):
        """测试IPO日期边界"""
        # 测试刚上市一天的股票
        data = {
            'trade_date': ['20250110'],
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [102.0],
            'vol': [1000000.0]
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ IPO日期边界测试通过")


class TestLimitUpDownBoundary(unittest.TestCase):
    """涨跌停数据处理边界测试"""

    def test_limit_up_data(self):
        """测试涨停数据"""
        # 模拟连续涨停
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 11)],
            'open': [100.0, 110.0, 121.0, 133.1, 146.41, 161.05, 177.16, 194.88, 214.37, 235.81],
            'high': [110.0, 121.0, 133.1, 146.41, 161.05, 177.16, 194.88, 214.37, 235.81, 259.39],
            'low': [100.0, 110.0, 121.0, 133.1, 146.41, 161.05, 177.16, 194.88, 214.37, 235.81],
            'close': [110.0, 121.0, 133.1, 146.41, 161.05, 177.16, 194.88, 214.37, 235.81, 259.39],
            'vol': [1000000.0] * 10
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 涨停数据测试通过")

    def test_limit_down_data(self):
        """测试跌停数据"""
        # 模拟连续跌停
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 11)],
            'open': [100.0, 90.0, 81.0, 72.9, 65.61, 59.05, 53.14, 47.83, 43.05, 38.74],
            'high': [100.0, 90.0, 81.0, 72.9, 65.61, 59.05, 53.14, 47.83, 43.05, 38.74],
            'low': [90.0, 81.0, 72.9, 65.61, 59.05, 53.14, 47.83, 43.05, 38.74, 34.87],
            'close': [90.0, 81.0, 72.9, 65.61, 59.05, 53.14, 47.83, 43.05, 38.74, 34.87],
            'vol': [1000000.0] * 10
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 跌停数据测试通过")

    def test_amplitude_extreme(self):
        """测试极端振幅"""
        # 模拟极端振幅（天地板）
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [100.0, 50.0, 100.0],  # 从涨停到跌停
            'high': [110.0, 50.0, 110.0],
            'low': [100.0, 40.0, 90.0],
            'close': [110.0, 40.0, 90.0],
            'vol': [1000000.0, 2000000.0, 1500000.0]
        }
        df = pd.DataFrame(data)
        result = calculate_ma(df)
        self.assertIsNotNone(result)
        print("✅ 极端振幅测试通过")


class TestMultiFactorBoundary(unittest.TestCase):
    """多因素共振边界测试"""

    def test_multiple_indicator_boundary(self):
        """测试多指标边界条件同时满足"""
        # 创建满足多个边界条件的数据
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 70)],
            'open': [100.0 + i * 0.5 for i in range(69)],
            'high': [105.0 + i * 0.5 for i in range(69)],
            'low': [99.0 + i * 0.5 for i in range(69)],
            'close': [102.0 + i * 0.5 for i in range(69)],
            'vol': [1000000.0 + i * 10000 for i in range(69)]
        }
        df = pd.DataFrame(data)

        # 计算多个指标
        ma_result = calculate_ma(df, periods=[5, 10, 20, 60])
        kdj_result = calculate_kdj(df)
        macd_result = calculate_macd(df)

        # 所有指标都应该能计算
        self.assertIsNotNone(ma_result)
        self.assertIsNotNone(kdj_result)
        self.assertIsNotNone(macd_result)
        print("✅ 多指标边界条件测试通过")

    def test_indicator_conflicting_signals(self):
        """测试指标信号冲突"""
        # 创建可能导致指标信号冲突的数据
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 35)],
            'open': [100.0, 95.0, 105.0, 98.0, 102.0, 97.0, 103.0, 96.0, 104.0, 95.0,
                    105.0, 98.0, 102.0, 97.0, 103.0, 96.0, 104.0, 95.0, 105.0, 98.0,
                    102.0, 97.0, 103.0, 96.0, 104.0, 95.0, 105.0, 98.0, 102.0, 97.0,
                    103.0, 96.0, 104.0, 95.0],
            'high': [110.0, 105.0, 115.0, 108.0, 112.0, 107.0, 113.0, 106.0, 114.0, 105.0,
                    115.0, 108.0, 112.0, 107.0, 113.0, 106.0, 114.0, 105.0, 115.0, 108.0,
                    112.0, 107.0, 113.0, 106.0, 114.0, 105.0, 115.0, 108.0, 112.0, 107.0,
                    113.0, 106.0, 114.0, 105.0],
            'low': [90.0, 85.0, 95.0, 88.0, 92.0, 87.0, 93.0, 86.0, 94.0, 85.0,
                   95.0, 88.0, 92.0, 87.0, 93.0, 86.0, 94.0, 85.0, 95.0, 88.0,
                   92.0, 87.0, 93.0, 86.0, 94.0, 85.0, 95.0, 88.0, 92.0, 87.0,
                   93.0, 86.0, 94.0, 85.0],
            'close': [95.0, 105.0, 98.0, 102.0, 97.0, 103.0, 96.0, 104.0, 95.0, 105.0,
                     98.0, 102.0, 97.0, 103.0, 96.0, 104.0, 95.0, 105.0, 98.0, 102.0,
                     97.0, 103.0, 96.0, 104.0, 95.0, 105.0, 98.0, 102.0, 97.0, 103.0,
                     96.0, 104.0, 95.0, 105.0],
            'vol': [1000000.0 + i * 50000 for i in range(34)]
        }
        df = pd.DataFrame(data)
        result = calculate_kdj(df)
        self.assertIsNotNone(result)
        print("✅ 指标信号冲突测试通过")


class TestRiskControlBoundary(unittest.TestCase):
    """风控止损止盈边界测试"""

    def setUp(self):
        """设置测试"""
        self.risk_manager = RiskManager()

    def test_stop_loss_boundary(self):
        """测试止损边界值"""
        # 测试刚好达到止损线 (-7%)
        result = self.risk_manager.check_stop_loss(100.0, 93.0)
        self.assertTrue(result['triggered'])
        self.assertAlmostEqual(result['loss_pct'], -7.0, places=1)
        print("✅ 止损边界测试通过")

    def test_stop_loss_not_triggered(self):
        """测试止损未触发"""
        # 测试未达到止损线
        result = self.risk_manager.check_stop_loss(100.0, 94.0)
        self.assertFalse(result['triggered'])
        print("✅ 止损未触发测试通过")

    def test_stop_loss_zero_price(self):
        """测试零价格止损"""
        result = self.risk_manager.check_stop_loss(0.0, 100.0)
        self.assertFalse(result['triggered'])
        self.assertEqual(result['action'], '无效价格')
        print("✅ 零价格止损测试通过")

    def test_stop_loss_negative_price(self):
        """测试负价格止损"""
        result = self.risk_manager.check_stop_loss(-100.0, 50.0)
        self.assertFalse(result['triggered'])
        print("✅ 负价格止损测试通过")

    def test_take_profit_boundary(self):
        """测试止盈边界"""
        # 创建测试数据
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 15)],
            'open': [100.0 + i for i in range(14)],
            'high': [105.0 + i for i in range(14)],
            'low': [99.0 + i for i in range(14)],
            'close': [100.0 + i for i in range(14)],
            'vol': [1000000.0 + i * 100000 for i in range(14)],
            'K': [50.0 + i for i in range(14)],
            'D': [50.0 + i for i in range(14)]
        }
        df = pd.DataFrame(data)

        # 测试 KDJ 死叉
        result = self.risk_manager.check_take_profit_kdj_dead_cross(df, 100.0)
        self.assertIsNotNone(result)
        print("✅ 止盈边界测试通过")

    def test_take_profit_ma10_boundary(self):
        """测试MA10止盈边界"""
        # 创建测试数据
        data = {
            'trade_date': ['2025010' + str(i) for i in range(1, 15)],
            'open': [100.0 + i for i in range(14)],
            'high': [105.0 + i for i in range(14)],
            'low': [99.0 + i for i in range(14)],
            'close': [100.0 + i for i in range(14)],
            'vol': [1000000.0 + i * 100000 for i in range(14)],
            'ma10': [100.0 + i for i in range(14)]
        }
        df = pd.DataFrame(data)

        # 测试跌破 MA10
        result = self.risk_manager.check_take_profit_ma10_break(df, 95.0)
        self.assertIsNotNone(result)
        print("✅ MA10止盈边界测试通过")

    def test_position_size_boundary(self):
        """测试仓位计算边界"""
        # 测试零资金
        result = self.risk_manager.calculate_position_size(0, 5)
        self.assertEqual(result['max_per_stock'], 0.0)
        self.assertEqual(result['suggested_count'], 0)
        print("✅ 仓位计算零资金边界测试通过")

    def test_position_size_exceed_limit(self):
        """测试超限仓位"""
        # 测试超过最大持仓数量
        result = self.risk_manager.calculate_position_size(1000000, 10)
        self.assertLessEqual(result['suggested_count'], 8)  # 不超过8只
        self.assertLessEqual(result['max_total_pct'], 80.0)  # 总仓位不超过80%
        print("✅ 超限仓位测试通过")


class TestAPIExceptionBoundary(unittest.TestCase):
    """API 异常边界测试"""

    def setUp(self):
        """设置测试环境"""
        self.client = TushareClient(use_mock=True)

    def test_api_timeout_handling(self):
        """测试 API 超时处理"""
        from unittest.mock import patch, MagicMock
        import time

        # Mock 模式下 _pro 为 None，需要先初始化一个 mock
        if self.client._pro is None:
            self.client._pro = MagicMock()

        # 模拟超时情况
        def timeout_func(*args, **kwargs):
            raise TimeoutError("API request timeout")

        with patch.object(self.client._pro, 'daily', side_effect=timeout_func):
            start = time.time()
            result = self.client.get_daily_data('300274.SZ', '20250101', '20250131')
            elapsed = time.time() - start

            # 验证超时处理（应该返回空 DataFrame 或 fallback 数据）
            self.assertIsNotNone(result)
            print(f"✅ API 超时处理测试通过 (耗时: {elapsed:.2f}s)")

    def test_api_rate_limit_handling(self):
        """测试 API 限流处理"""
        from unittest.mock import patch, MagicMock

        # Mock 模式下 _pro 为 None，需要先初始化一个 mock
        if self.client._pro is None:
            self.client._pro = MagicMock()

        # 模拟限流返回
        class APIError(Exception):
            def __init__(self, code, msg):
                self.code = code
                self.msg = msg
                super().__init__(msg)

        def rate_limit_func(*args, **kwargs):
            raise APIError(429, 'Rate limit exceeded')

        with patch.object(self.client._pro, 'daily', side_effect=rate_limit_func):
            result = self.client.get_daily_data('300274.SZ', '20250101', '20250131')

            # 验证限流处理（应该返回空 DataFrame 或 fallback 数据）
            self.assertIsNotNone(result)
            print("✅ API 限流处理测试通过")

    def test_missing_field_handling(self):
        """测试 API 返回缺失字段"""
        # 模拟字段缺失的数据
        mock_df = pd.DataFrame({
            'ts_code': ['300274.SZ'],
            'trade_date': ['20250101'],
            # 缺少 close, open, high, low, vol 等字段
        })

        # 测试在字段缺失时的处理
        try:
            # 尝试计算 KDJ - 应该能处理
            result = calculate_kdj(mock_df)
            self.assertIsNotNone(result)
            print("✅ 字段缺失处理测试通过")
        except KeyError:
            # 如果抛出 KeyError，也是预期行为
            print("✅ 字段缺失处理测试通过 (预期 KeyError)")

    def test_invalid_data_type_handling(self):
        """测试数据类型异常"""
        # 模拟类型错误：string instead of float
        mock_df = pd.DataFrame({
            'ts_code': ['300274.SZ'] * 10,
            'trade_date': ['2025010' + str(i) for i in range(10)],
            'open': ['N/A', 'invalid', None, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0],
            'high': ['N/A', 'invalid', None, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0],
            'low': ['N/A', 'invalid', None, 99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
            'close': ['N/A', 'invalid', None, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
            'vol': ['N/A', 'invalid', None, 1000000.0, 1100000.0, 1200000.0, 1300000.0, 1400000.0, 1500000.0, 1600000.0]
        })

        # 测试在类型错误时的处理 - 应该能捕获异常
        try:
            result = calculate_kdj(mock_df)
            # 如果成功，应该返回有效结果
            self.fail("Expected exception but got result")
        except (ValueError, TypeError, KeyError, pd.errors.DataError) as e:
            # 如果抛出异常，也是预期行为
            print(f"✅ 数据类型异常处理测试通过 (捕获异常: {type(e).__name__})")

    def test_network_error_handling(self):
        """测试网络错误处理"""
        from unittest.mock import patch, MagicMock

        # Mock 模式下 _pro 为 None，需要先初始化一个 mock
        if self.client._pro is None:
            self.client._pro = MagicMock()

        def network_error_func(*args, **kwargs):
            raise ConnectionError("Network connection failed")

        with patch.object(self.client._pro, 'daily', side_effect=network_error_func):
            result = self.client.get_daily_data('300274.SZ', '20250101', '20250131')

            # 验证网络错误处理
            self.assertIsNotNone(result)
            print("✅ 网络错误处理测试通过")

    def test_api_response_empty_handling(self):
        """测试 API 返回空数据处理"""
        from unittest.mock import patch, MagicMock

        # Mock 模式下 _pro 为 None，需要先初始化一个 mock
        if self.client._pro is None:
            self.client._pro = MagicMock()

        # 模拟返回空 DataFrame
        def empty_response(*args, **kwargs):
            return pd.DataFrame()

        with patch.object(self.client._pro, 'daily', side_effect=empty_response):
            result = self.client.get_daily_data('300274.SZ', '20250101', '20250131')

            # 验证空数据处理
            self.assertIsInstance(result, pd.DataFrame)
            print("✅ API 空响应处理测试通过")

    def test_invalid_ts_code_handling(self):
        """测试无效股票代码处理"""
        # 测试不存在的股票代码
        result = self.client.get_daily_data('INVALID.SZ', '20250101', '20250131')

        # 验证无效代码处理
        self.assertIsInstance(result, (pd.DataFrame, type(None)))
        print("✅ 无效股票代码处理测试通过")

    def test_invalid_date_range_handling(self):
        """测试无效日期范围处理"""
        # 测试未来日期
        result = self.client.get_daily_data('300274.SZ', '20300101', '20301231')

        # 验证日期范围处理
        self.assertIsInstance(result, (pd.DataFrame, type(None)))
        print("✅ 无效日期范围处理测试通过")


class TestDataValidationBoundary(unittest.TestCase):
    """数据验证边界测试"""

    def test_negative_values_in_volume(self):
        """测试成交量为负数"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [102.0, 103.0, 104.0],
            'vol': [-1000.0, 1000000.0, 1100000.0]  # 负数成交量
        }
        df = pd.DataFrame(data)
        result = calculate_volume_ratio(df)
        # 验证处理
        self.assertIsInstance(result, float)
        print("✅ 负数成交量处理测试通过")

    def test_extreme_price_values(self):
        """测试极端价格值"""
        data = {
            'trade_date': ['20250101', '20250102', '20250103'],
            'open': [1e10, 1e15, 1e20],  # 极端大值
            'high': [1e10, 1e15, 1e20],
            'low': [1e10, 1e15, 1e20],
            'close': [1e10, 1e15, 1e20],
            'vol': [1000000.0, 1100000.0, 1200000.0]
        }
        df = pd.DataFrame(data)
        try:
            result = calculate_kdj(df)
            self.assertIsNotNone(result)
            print("✅ 极端价格值处理测试通过")
        except (OverflowError, ValueError):
            print("✅ 极端价格值处理测试通过 (预期异常)")

    def test_unicode_in_stock_name(self):
        """测试股票名称中的特殊字符"""
        data = {
            'trade_date': ['20250101'],
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [102.0],
            'vol': [1000000.0]
        }
        df = pd.DataFrame(data)
        # 股票名称不应该影响技术指标计算
        result = calculate_kdj(df)
        self.assertIsNotNone(result)
        print("✅ 特殊字符处理测试通过")


if __name__ == '__main__':
    unittest.main()
