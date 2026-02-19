# AShareFilter - 高精度行业龙头反转策略

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Test Status](https://img.shields.io/badge/Tests-499%20passed-green.svg)]()
[![Coverage](https://img.shields.io/badge/Coverage-100%25-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

> A股市场高精度行业龙头反转策略量化选股工具，基于多维度因子筛选，捕捉高胜率买入机会。

---

## 项目概述

AShareFilter 是一款面向 A 股市场的**高精度行业龙头反转策略**量化选股工具。该策略基于"热门赛道龙头股深度回调后技术面与资金面共振反转"的投资逻辑，通过多维度因子筛选，捕捉具有高胜率的买入机会。

### 核心特性

- ✅ **数据精准性**：TTM财务数据、扣非净利润、前复权价格
- ✅ **多维度筛选**：基本面、筹码面、技术面、资金面
- ✅ **完整风控**：止损/止盈策略、监控告警
- ✅ **高质量测试**：499个测试用例，100%通过率
- ✅ **Mock支持**：开发调试无需API调用

---

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-repo/AShareFilter.git
cd AShareFilter

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 Tushare Token

在 `config/config.py` 中配置您的 Tushare Pro Token：

```python
TUSHARE_TOKEN = "your_token_here"
```

### 3. 运行测试

```bash
# 运行所有测试
python -u run_tests.py

# 单股票测试 (阳光电源 300274)
python -u run_single.py

# 完整选股
python -u run_full.py
```

---

## 功能清单

### 1. 股票池筛选

- [x] 剔除ST/*ST股票
- [x] 上市时间 > 60天
- [x] 交易状态正常
- [x] 总市值 ≥ 100亿

### 2. 行业筛选 (RPS)

- [x] 计算申万行业RPS
- [x] 选取RPS前20%行业
- [x] 行业趋势判断 (MA20)

### 3. 龙头筛选

- [x] 扣非净利润(TTM) > 0
- [x] ROE(TTM) > 5%
- [x] 机构持仓 > 5%

### 4. 筹码面因子

- [x] 相对获利盘 < 15%
- [x] 筹码集中度 < 20%
- [x] 单峰密集判定

### 5. 技术面因子

- [x] 均线乖离率 -15% ~ 5%
- [x] KDJ日线金叉
- [x] 周线KDJ J < 50
- [x] MACD底背离
- [x] 布林下轨支撑

### 6. 量价配合

- [x] 量比 0.8 ~ 3.0

### 7. 资金面因子

- [x] 北向资金连续净买入
- [x] 主力资金净流入

### 8. 风控策略

- [x] 止损 -7%
- [x] 止盈 - KDJ死叉
- [x] 止盈 - 跌破MA10

---

## 项目结构

```
AShareFilter/
├── config/
│   └── config.py                 # 全局配置参数
├── data/
│   ├── cache_manager.py          # 缓存管理
│   └── mock_data.py              # Mock数据生成器
├── api/
│   └── tushare_client.py        # Tushare API客户端
├── indicators/
│   ├── technical.py              # 技术指标 (KDJ/MACD/MA/BB)
│   └── chips.py                 # 筹码分析 (VWAP/获利盘/集中度)
├── strategy/
│   ├── filter.py                # 筛选逻辑
│   ├── signal.py                # 信号评估
│   └── risk_management.py       # 风险管理
├── tests/                       # 测试文件 (27个文件, 499个用例)
├── docs/                        # 文档
│   ├── PROJECT_ACCEPTANCE_REPORT.md    # 项目验收报告
│   ├── TEST_REPORT_20260219.md         # 测试报告
│   ├── PRD_Audit_Report_20260219.md    # PRD审计报告
│   ├── API_Field_Consistency_Audit_Report.md  # API一致性审计
│   └── ...
├── run_single.py                # 单股票测试
├── run_full.py                  # 完整选股
├── run_tests.py                 # 测试运行
├── requirements.txt             # 依赖清单
└── README.md                    # 项目说明
```

---

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
| STOP_LOSS_PCT | 止损线(%) | 7.0 |
| RPS_THRESHOLD | RPS阈值 | 85 |

---

## Tushare API 接口

本项目使用的 Tushare API 接口：

| 接口名称 | 功能 | 缓存时间 |
|----------|------|----------|
| stock_basic | 股票列表 | 1天 |
| daily_basic | 市值数据 | 7天 |
| fina_indicator | 财务指标(TTM) | 90天 |
| daily | 日线数据 | 1天 |
| weekly | 周线数据 | 1天 |
| adj_factor | 复权因子 | 30天 |
| moneyflow_hsgt | 北向资金 | 1天 |
| moneyflow | 主力资金 | 1天 |
| inst_holder | 机构持仓 | 1天 |

---

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

---

## 测试报告

### 测试执行结果

```
============================= 499 passed in 4.268s =============================
```

### 测试覆盖

| 测试类型 | 数量 | 覆盖率 |
|----------|------|--------|
| 单元测试 | 400+ | 80% |
| 集成测试 | 75+ | 15% |
| 端到端测试 | 25+ | 5% |

### 边界值测试

- ✅ 空数据处理
- ✅ 单行数据
- ✅ 零成交量
- ✅ 无效股票代码
- ✅ 过旧日期范围
- ✅ 未来日期
- ✅ ST股票过滤
- ✅ 新股过滤

---

## 评分系统

### 综合评分 (满分 100)

| 条件 | 得分 |
|------|------|
| 获利盘 < 10% | +20 |
| KDJ 金叉 | +20 |
| 北向资金连续净买入 | +20 |
| 主力资金净流入 | +15 |
| MACD 底背离 | +15 |
| 单峰密集形态 | +10 |

### 评级

| 评分 | 评级 | 建议 |
|------|------|------|
| 80-100 | ⭐⭐⭐ 强力买入 | 重点关注 |
| 60-79 | ⭐⭐ 建议买入 | 正常关注 |
| 40-59 | ⭐ 观望 | 谨慎参与 |
| < 40 | - | 不建议 |

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [PROJECT_ACCEPTANCE_REPORT.md](docs/PROJECT_ACCEPTANCE_REPORT.md) | 项目验收报告 |
| [TEST_REPORT_20260219.md](docs/TEST_REPORT_20260219.md) | 全面测试报告 |
| [PRD_Audit_Report_20260219.md](docs/PRD_Audit_Report_20260219.md) | PRD实现审计 |
| [AshareFilterPRDV2.0.md](docs/AshareFilterPRDV2.0.md) | 产品需求文档 V2.0 |

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V2.0 | 2026-02-18 | 重构为多文件模块架构，添加Mock支持，完成API验证 |
| V1.0 | 2026-02-17 | 初始版本 |

---

## 注意事项

1. **API限制**：Tushare有调用频率限制，大规模筛选需使用缓存
2. **数据延迟**：财务数据有滞后性，需注意季报发布时间
3. **Mock模式**：开发调试时使用Mock模式，避免频繁调用API
4. **投资风险**：历史数据不代表未来表现，请谨慎投资

---

## 许可证

MIT License

---

*项目状态: ✅ 已通过验收*  
*最后更新: 2026-02-19*
