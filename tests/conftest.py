"""
pytest 配置文件 - 测试框架核心配置

提供:
- 全局 fixtures
- Mock 数据 fixtures
- 测试环境配置
- 自定义标记
- CI/CD 支持
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
import datetime

# CI/CD 环境变量
CI_ENV = os.environ.get("CI", "false").lower() == "true"
USE_MOCK_DATA = os.environ.get("USE_MOCK_DATA", "true").lower() == "true"
GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.tushare_client import TushareClient
from strategy.filter import StockFilter
from strategy.risk_management import RiskManager, get_risk_manager
from data.mock_data import (
    generate_mock_stock_list,
    generate_mock_daily_data,
    generate_mock_financial_ttm,
)


# ============================================================================
# 环境配置 Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def mock_env():
    """设置 Mock 数据测试环境"""
    return {
        "use_mock": USE_MOCK_DATA,
        "data_dir": os.path.join(PROJECT_ROOT, "data_cache"),
    }


@pytest.fixture(scope="session")
def is_ci_environment():
    """检测是否在 CI 环境中运行"""
    return CI_ENV or GITHUB_ACTIONS


@pytest.fixture(scope="session")
def test_mode():
    """返回测试模式: mock 或 real"""
    return "mock" if USE_MOCK_DATA else "real"


@pytest.fixture(scope="session")
def project_root():
    """返回项目根目录"""
    return PROJECT_ROOT


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def tushare_client():
    """创建 Tushare 客户端 (Mock 模式)"""
    return TushareClient(use_mock=True)


@pytest.fixture
def mock_client():
    """创建 Mock Tushare 客户端 (每次测试新建)"""
    return TushareClient(use_mock=True)


@pytest.fixture
def real_client():
    """创建真实 Tushare 客户端 (需要 Token)"""
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        pytest.skip("TUSHARE_TOKEN not set")
    return TushareClient(use_mock=False, token=token)


# ============================================================================
# Strategy Fixtures
# ============================================================================

@pytest.fixture
def stock_filter(mock_client):
    """创建股票筛选器"""
    return StockFilter(mock_client)


@pytest.fixture
def risk_manager():
    """创建风控管理器"""
    return get_risk_manager()


# ============================================================================
# Mock 数据 Fixtures
# ============================================================================

@pytest.fixture
def sample_stock_list():
    """生成示例股票列表"""
    return generate_mock_stock_list()


@pytest.fixture
def sample_daily_data():
    """生成示例日线数据"""
    return generate_mock_daily_data(
        ts_code="300274.SZ",
        start_date="20240101",
        end_date=datetime.datetime.now().strftime("%Y%m%d"),
        base_price=100.0,
    )


@pytest.fixture
def sample_financial_data():
    """生成示例财务数据"""
    return generate_mock_financial_ttm()


@pytest.fixture
def sample_kdj_data():
    """生成用于 KDJ 计算的测试数据"""
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    data = {
        "trade_date": [d.strftime("%Y%m%d") for d in dates],
        "open": np.random.uniform(95, 105, 30).tolist(),
        "high": np.random.uniform(100, 110, 30).tolist(),
        "low": np.random.uniform(90, 100, 30).tolist(),
        "close": np.random.uniform(95, 105, 30).tolist(),
        "vol": np.random.uniform(1000000, 5000000, 30).tolist(),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_ma_data():
    """生成用于均线计算的测试数据"""
    dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
    base_prices = np.linspace(90, 110, 60)
    data = {
        "trade_date": [d.strftime("%Y%m%d") for d in dates],
        "open": base_prices.tolist(),
        "high": (base_prices + 5).tolist(),
        "low": (base_prices - 5).tolist(),
        "close": base_prices.tolist(),
        "vol": np.random.uniform(1000000, 5000000, 60).tolist(),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_chips_data():
    """生成用于筹码分析的测试数据"""
    dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
    base_prices = np.linspace(90, 110, 60)
    data = {
        "trade_date": [d.strftime("%Y%m%d") for d in dates],
        "open": base_prices.tolist(),
        "high": (base_prices + 5).tolist(),
        "low": (base_prices - 5).tolist(),
        "close": base_prices.tolist(),
        "vol": np.random.uniform(1000000, 5000000, 60).tolist(),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_position():
    """生成示例持仓数据"""
    return {
        "buy_price": 100.0,
        "buy_date": "2024-01-01",
        "shares": 1000,
    }


@pytest.fixture
def sample_market_data():
    """生成示例市场数据"""
    dates = pd.date_range(start="2024-01-01", periods=20, freq="D")
    data = {
        "trade_date": [d.strftime("%Y%m%d") for d in dates],
        "open": [100.0 + i for i in range(20)],
        "high": [105.0 + i for i in range(20)],
        "low": [99.0 + i for i in range(20)],
        "close": [102.0 + i for i in range(20)],
        "vol": [1000000.0 + i * 100000 for i in range(20)],
        "K": [50.0 + i * 2 for i in range(20)],
        "D": [50.0 + i * 1.5 for i in range(20)],
        "J": [50.0 + i * 3 for i in range(20)],
        "ma5": [100.0 + i for i in range(20)],
        "ma10": [100.0 + i * 0.8 for i in range(20)],
        "ma20": [100.0 + i * 0.5 for i in range(20)],
    }
    return pd.DataFrame(data)


# ============================================================================
# 测试数据 Fixtures (边界情况)
# ============================================================================

@pytest.fixture
def empty_dataframe():
    """空 DataFrame"""
    return pd.DataFrame()


@pytest.fixture
def single_row_data():
    """单行数据"""
    return pd.DataFrame({
        "trade_date": ["20240101"],
        "open": [100.0],
        "high": [105.0],
        "low": [99.0],
        "close": [102.0],
        "vol": [1000000.0],
    })


@pytest.fixture
def data_with_nulls():
    """包含空值的数据"""
    return pd.DataFrame({
        "trade_date": ["20240101", "20240102", "20240103"],
        "open": [100.0, None, 102.0],
        "high": [105.0, 106.0, None],
        "low": [99.0, 100.0, 101.0],
        "close": [102.0, 103.0, 104.0],
        "vol": [1000000.0, 1100000.0, 1200000.0],
    })


@pytest.fixture
def data_with_zeros():
    """包含零值的数据"""
    return pd.DataFrame({
        "trade_date": ["20240101", "20240102", "20240103"],
        "open": [0.0, 0.0, 0.0],
        "high": [0.0, 0.0, 0.0],
        "low": [0.0, 0.0, 0.0],
        "close": [0.0, 0.0, 0.0],
        "vol": [0.0, 0.0, 0.0],
    })


@pytest.fixture
def data_with_negative():
    """包含负值的数据"""
    return pd.DataFrame({
        "trade_date": ["20240101", "20240102", "20240103"],
        "open": [-100.0, -50.0, 0.0],
        "high": [-50.0, 0.0, 50.0],
        "low": [-150.0, -100.0, -50.0],
        "close": [-100.0, -50.0, 0.0],
        "vol": [1000000.0, 1100000.0, 1200000.0],
    })


@pytest.fixture
def data_with_infinity():
    """包含无穷值的数据"""
    return pd.DataFrame({
        "trade_date": ["20240101", "20240102", "20240103"],
        "open": [100.0, float("inf"), 102.0],
        "high": [105.0, float("inf"), 107.0],
        "low": [99.0, 100.0, 101.0],
        "close": [102.0, float("inf"), 104.0],
        "vol": [1000000.0, 1100000.0, 1200000.0],
    })


@pytest.fixture
def data_with_nan():
    """包含 NaN 值的数据"""
    df = pd.DataFrame({
        "trade_date": ["2024010" + str(i) for i in range(1, 20)],
        "open": [100.0 + i for i in range(19)],
        "high": [105.0 + i for i in range(19)],
        "low": [99.0 + i for i in range(19)],
        "close": [102.0 + i for i in range(19)],
        "vol": [1000000.0 + i * 100000 for i in range(19)],
    })
    df.loc[5, "close"] = np.nan
    df.loc[10, "high"] = np.nan
    return df


# ============================================================================
# 测试股票列表 Fixtures
# ============================================================================

@pytest.fixture
def test_stock_list():
    """标准测试股票列表"""
    return ["300274.SZ", "600519.SH", "000001.SZ", "000002.SZ", "600000.SH"]


@pytest.fixture
def test_stocks_with_st():
    """包含 ST 股票的测试列表"""
    return [
        {"ts_code": "600519.SH", "name": "贵州茅台", "is_st": False},
        {"ts_code": "000001.SZ", "name": "平安银行", "is_st": False},
        {"ts_code": "600001.SH", "name": "ST某某", "is_st": True},
        {"ts_code": "300001.SZ", "name": "ST个股", "is_st": True},
        {"ts_code": "000002.SZ", "name": "万科A", "is_st": False},
    ]


# ============================================================================
# Pytest 钩子函数
# ============================================================================

def pytest_configure(config):
    """Pytest 配置钩子"""
    # 注册自定义标记
    config.addinivalue_line("markers", "boundary: 边界条件测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "requires_token: 需要 Tushare Token 的测试")
    config.addinivalue_line("markers", "ci: CI/CD 特定测试")
    config.addinivalue_line("markers", "daily: 每日测试")

    # 设置 CI 模式标记
    if CI_ENV or GITHUB_ACTIONS:
        config.addinivalue_line("markers", "ci_run: 在 CI 环境中运行")


def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    for item in items:
        # 自动为测试添加标记
        if "boundary" in item.nodeid.lower():
            item.add_marker(pytest.mark.boundary)
        if "e2e" in item.nodeid.lower() or "enhanced" in item.nodeid.lower():
            item.add_marker(pytest.mark.e2e)
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        if "daily" in item.nodeid.lower():
            item.add_marker(pytest.mark.daily)


def pytest_report_header(config):
    """自定义测试报告头"""
    mode = "Mock Data" if USE_MOCK_DATA else "Real Data"
    ci_status = "CI Mode" if (CI_ENV or GITHUB_ACTIONS) else "Local"
    return [
        "=" * 60,
        "AShareFilter 测试框架",
        "=" * 60,
        f"项目路径: {PROJECT_ROOT}",
        f"测试模式: {mode}",
        f"运行环境: {ci_status}",
        f"Python版本: {sys.version.split()[0]}",
        "=" * 60,
    ]


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """自定义测试摘要报告"""
    if CI_ENV or GITHUB_ACTIONS:
        # CI 环境下添加额外的摘要信息
        terminalreporter.write_sep("=", "CI/CD 测试摘要")
        terminalreporter.write_line(f"测试模式: {'Mock' if USE_MOCK_DATA else 'Real'}")
        terminalreporter.write_line(f"环境: GitHub Actions")

        # 输出测试结果统计
        stats = terminalreporter.stats
        if 'passed' in stats:
            terminalreporter.write_line(f"通过: {len(stats['passed'])}")
        if 'failed' in stats:
            terminalreporter.write_line(f"失败: {len(stats['failed'])}")
        if 'skipped' in stats:
            terminalreporter.write_line(f"跳过: {len(stats['skipped'])}")


# ============================================================================
# 辅助函数
# ============================================================================

def create_test_dataframe(rows=60, base_price=100.0):
    """创建测试用 DataFrame"""
    dates = pd.date_range(start="2024-01-01", periods=rows, freq="D")
    base_prices = np.linspace(base_price - 10, base_price + 10, rows)
    return pd.DataFrame({
        "trade_date": [d.strftime("%Y%m%d") for d in dates],
        "open": base_prices.tolist(),
        "high": (base_prices + 5).tolist(),
        "low": (base_prices - 5).tolist(),
        "close": base_prices.tolist(),
        "vol": np.random.uniform(1000000, 5000000, rows).tolist(),
    })


def assert_dataframe_not_empty(df, message="DataFrame 不应为空"):
    """断言 DataFrame 不为空"""
    assert df is not None and not df.empty, message


def assert_required_columns(df, columns, message="缺少必要字段"):
    """断言 DataFrame 包含必要字段"""
    for col in columns:
        assert col in df.columns, f"{message}: {col}"


def assert_no_null_in_columns(df, columns, message="包含空值"):
    """断言指定列不包含空值"""
    for col in columns:
        assert not df[col].isnull().any(), f"{message}: {col}"
