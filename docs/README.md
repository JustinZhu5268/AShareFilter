# AShareFilter - 高精度行业龙头反转策略

## 项目概述

高精度行业龙头反转策略 V2.0 实现，基于 PRD V2.0 文档规范。

## 项目结构

```
AShareFilter/
├── config/
│   └── config.py          # 配置参数 (PRD V2.0)
├── data/
│   ├── cache_manager.py   # 缓存管理
│   └── mock_data.py       # Mock数据生成器 (与Tushare API一致)
├── api/
│   └── tushare_client.py  # Tushare API客户端
├── indicators/
│   ├── technical.py       # 技术指标 (KDJ/MACD/MA/布林带)
│   └── chips.py           # 筹码计算 (VWAP/获利盘/集中度)
├── strategy/
│   ├── filter.py          # 筛选逻辑
│   └── signal.py          # 信号评估
├── tests/
│   ├── test_indicators.py # 技术指标测试
│   └── test_integration.py # 集成测试
├── docs/
│   └── tushare_api_validation.py  # Tushare API验证脚本
├── run_single.py          # 单股票测试 (300274)
├── run_full.py            # 完整选股
└── README.md
```

## 功能清单 (PRD V2.0)

### 1. 股票池筛选
- [x] 剔除ST/*ST股票
- [x] 上市时间 > 60天
- [x] 交易状态正常

### 2. 行业筛选 (RPS)
- [x] 计算申万行业RPS
- [x] 选取RPS前20%行业

### 3. 龙头筛选
- [x] 总市值 ≥ 100亿
- [x] 扣非净利润(TTM) > 0
- [x] ROE(TTM) > 5%

### 4. 筹码面因子
- [x] 相对获利盘 < 15%
- [x] 筹码集中度 < 20%
- [x] 单峰密集判定

### 5. 技术面因子
- [x] 均线乖离率 -15% ~ 5%
- [x] KDJ日线金叉
- [x] MACD底背离
- [x] 布林下轨支撑

### 6. 量价配合
- [x] 量比 0.8 ~ 3.0

### 7. 资金面因子
- [x] 北向资金连续净买入
- [x] 主力资金净流入

## 使用方法

### 1. 环境准备

```bash
pip install tushare pandas numpy
```

### 2. 测试单股票 (300274 阳光电源)

```bash
# Mock模式 (快速测试，无需API)
python run_single.py --mock

# 真实API模式
python run_single.py
```

### 3. 运行完整选股

```bash
# Mock模式
python run_full.py --mock

# 真实API模式
python run_full.py
```

### 4. 运行测试

```bash
python tests/test_integration.py
python tests/test_indicators.py
```

## Tushare API 接口验证结果

本项目使用的 Tushare API 接口经过实际调用验证，以下是各接口的返回数据格式：

### 1. stock_basic (股票列表)

| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | string | 股票代码 (如 300274.SZ) |
| symbol | string | 股票代码 (6位数字) |
| name | string | 股票名称 |
| industry | string | 所属行业 |
| list_date | string | 上市日期 (YYYYMMDD) |

### 2. daily_basic (市值数据) ⚠️ 重要

| 字段 | 类型 | 说明 | 单位 |
|------|------|------|------|
| ts_code | string | 股票代码 | - |
| trade_date | string | 交易日期 | YYYYMMDD |
| close | float | 收盘价 | 元 |
| total_mv | float | 总市值 | **万元** |
| circ_mv | float | 流通市值 | **万元** |
| free_share | float | 流通股数 | 万股 |

**⚠️ 重要发现**: Tushare返回的 `total_mv` 和 `circ_mv` 单位是**万元**，不是千元！

```python
# 正确转换: 万元 → 亿元
mv = float(total_mv) / 10000
```

### 3. fina_indicator (财务指标)

| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | string | 股票代码 |
| ann_date | string | 公告日期 |
| end_date | string | 报告期结束日期 |
| roe | float | 净资产收益率(%) |

**⚠️ 重要发现**: 接口返回 `ann_date` 和 `end_date` 字段，没有 `report_date` 字段！

### 4. adj_factor (复权因子)

| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | string | 股票代码 |
| trade_date | string | 交易日期 |
| adj_factor | float | 复权因子 |

**使用说明**: 前复权价格 = 原始价格 × adj_factor

### 5. daily (日线数据)

| 字段 | 类型 | 说明 | 单位 |
|------|------|------|------|
| ts_code | string | 股票代码 | - |
| trade_date | string | 交易日期 | YYYYMMDD |
| open | float | 开盘价 | 元 |
| high | float | 最高价 | 元 |
| low | float | 最低价 | 元 |
| close | float | 收盘价 | 元 |
| pre_close | float | 前收盘价 | 元 |
| change | float | 涨跌额 | 元 |
| pct_chg | float | 涨跌幅 | % |
| vol | float | 成交量 | 手 |
| amount | float | 成交额 | **千元** |

### 6. moneyflow_hsgt (北向资金)

| 字段 | 类型 | 说明 | 单位 |
|------|------|------|------|
| trade_date | string | 交易日期 | YYYYMMDD |
| ggt_ss | float | 港股通(沪)买入额 | 万元 |
| ggt_sz | float | 港股通(深)买入额 | 万元 |
| hgt | float | 北向资金买入额 | 万元 |
| sgt | float | 深股通买入额 | 万元 |
| north_money | float | 北向资金净流入 | 万元 |
| south_money | float | 南向资金净流入 | 万元 |

**⚠️ 重要发现**: 接口返回 `north_money` 字段，没有直接的 `net_inflow` 字段！

### 7. moneyflow (主力资金)

| 字段 | 类型 | 说明 | 单位 |
|------|------|------|------|
| ts_code | string | 股票代码 | - |
| trade_date | string | 交易日期 | - |
| buy_sm_vol | float | 小单买入成交量 | 手 |
| sell_sm_vol | float | 小单卖出成交量 | 手 |
| buy_md_vol | float | 中单买入成交量 | 手 |
| sell_md_vol | float | 中单卖出成交量 | 手 |
| buy_lg_vol | float | 大单买入成交量 | 手 |
| sell_lg_vol | float | 大单卖出成交量 | 手 |
| buy_elg_vol | float | 超大单买入成交量 | 手 |
| sell_elg_vol | float | 超大单卖出成交量 | 手 |
| net_mf_vol | float | 净流入成交量 | 手 |
| net_mf_amount | float | 净流入金额 | 万元 |

**⚠️ 重要发现**: 接口返回 `net_mf_amount` 字段，没有直接的 `net_inflow` 字段！

### 8. sw_index (申万行业) ⚠️ 需要权限

| 状态 | 说明 |
|------|------|
| ❌ 调用失败 | 该接口需要特别权限或积分 |

### 9. index_daily (行业指数)

| 状态 | 说明 |
|------|------|
| ❌ 调用失败 | 需要正确的指数代码(ts_code)参数 |

## Mock数据与真实API对比

Mock数据生成器 (`data/mock_data.py`) 已经过调整，与真实API返回格式完全一致：

| 接口 | Mock数据 | 真实API | 状态 |
|------|----------|---------|------|
| stock_basic | ✅ | ✅ | 一致 |
| daily_basic | ✅ | ✅ | 一致 |
| fina_indicator | ✅ | ✅ | 一致 |
| adj_factor | ✅ | ✅ | 一致 |
| daily | ✅ | ✅ | 一致 |
| moneyflow_hsgt | ✅ | ✅ | 一致 |
| moneyflow | ✅ | ✅ | 一致 |

## 缓存机制

系统使用本地CSV文件缓存数据，减少API调用：

| 缓存类型 | 有效期 | 说明 |
|----------|--------|------|
| stock_list | 1天 | 股票列表 |
| market_cap | 7天 | 市值数据 |
| financial_ttm | 90天 | 财务数据 |
| adj_factor | 30天 | 复权因子 |
| industry_rps | 1天 | 行业RPS |
| daily_data | 1天 | 日线数据 |

缓存目录：`data_cache/`

## 配置说明

在 `config/config.py` 中可修改以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| MIN_MARKET_CAP | 最小市值(亿) | 100 |
| MIN_ROE_TTM | 最小ROE(%) | 5.0 |
| MAX_PROFIT_RATIO | 最大获利盘(%) | 15.0 |
| MA_BIAS_MIN | 乖离率下限(%) | -15.0 |
| MA_BIAS_MAX | 乖离率上限(%) | 5.0 |
| VOLUME_RATIO_MIN | 量比下限 | 0.8 |
| VOLUME_RATIO_MAX | 量比上限 | 3.0 |

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V2.0 | 2026-02-18 | 重构为多文件模块架构，添加Mock支持，完成API验证 |

## 注意事项

1. **API限制**：Tushare有调用频率限制，大规模筛选需使用缓存
2. **数据延迟**：财务数据有滞后性，需注意季报发布时间
3. **Mock模式**：开发调试时使用Mock模式，避免频繁调用API
4. **sw_index权限**：申万行业接口需要特别权限，无法正常使用
