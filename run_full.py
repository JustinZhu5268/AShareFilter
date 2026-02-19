"""
完整选股程序
运行完整的选股筛选流程
"""

import os
import datetime
import pandas as pd
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入配置
from config import config

# 导入缓存管理
from data.cache_manager import print_cache_status

# 导入API客户端
from api.tushare_client import get_client, reset_client

# 导入筛选器
from strategy.filter import StockFilter

# 导入信号评估
from strategy.signal import generate_stock_report


def main():
    """运行完整选股流程"""
    start_time = time.time()
    
    # 打印缓存状态
    print_cache_status()
    
    print("\n" + "="*60)
    print("🚀 高精度行业龙头反转策略 V2.0")
    print("="*60)
    print(f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查是否使用Mock模式
    use_mock = '--mock' in sys.argv or config.USE_MOCK_DATA
    
    if use_mock:
        print("\n🔧 模式: Mock数据")
    else:
        print("\n🌐 模式: 真实API")
    
    # 重置客户端以应用新设置
    reset_client()
    
    # 获取客户端
    client = get_client(use_mock=use_mock)
    
    # 创建筛选器
    filter_obj = StockFilter(client)
    
    # 运行完整筛选
    results = filter_obj.run_full_filter()
    
    # 输出结果
    print("\n" + "="*60)
    print(f"📋 筛选结果: {len(results)} 只符合条件")
    print("="*60)
    
    if results:
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r['code']} {r['name']}")
            print(f"   行业: {r['industry']}")
            print(f"   价格: {r['price']:.2f} | ROE: {r['roe']:.1f}%")
            print(f"   获利盘: {r['profit_ratio']:.1f}% | 集中度: {r['concentration']:.1f}%")
            print(f"   乖离率: {r['ma_bias']:.1f}% | KDJ: {r['kdj']} | MACD: {r['macd_divergence']}")
            print(f"   量比: {r['volume_ratio']:.2f} | 北向: {r['northbound']:.0f}万")
            print(f"   评分: {r['score']}")
    else:
        print("\n未找到符合所有条件的股票")
    
    # 保存结果
    if results:
        save_results(results)
        generate_full_report(results)
    
    # 打印耗时
    elapsed = time.time() - start_time
    print(f"\n⏱️ 总耗时: {elapsed:.1f}秒")


def save_results(results: list):
    """保存选股结果到CSV"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    df = pd.DataFrame(results)
    csv_file = f"选股结果_V2_{timestamp}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ CSV结果已保存: {csv_file}")


def generate_full_report(results: list):
    """生成完整的Markdown报告"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = f"""# 📊 高精度行业龙头反转策略 V2.0 - 选股报告

**生成时间**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 一、策略说明

### 1.1 核心优化点 (PRD V2.0)

本策略基于PRD V2.0建议实现，包含以下核心优化：

| 维度 | 优化项 | 说明 |
|------|--------|------|
| **财务数据** | TTM + 扣非净利润 | 滚动4个季度，剔除非经常性损益 |
| **财务指标** | ROE(TTM) > 5% | 确保盈利能力和股东回报 |
| **价格数据** | 前复权处理 | 消除除权干扰 |
| **行业筛选** | RPS > 85 | 只选真热点行业 |
| **筹码分布** | VWAP算法 | 精确计算获利盘和集中度 |
| **技术信号** | KDJ金叉 + 乖离率 + MACD底背离 | 多重确认买点 |
| **量价配合** | 量比0.8~3.0 | 温和放量 |
| **资金验证** | 北向资金 | 验证聪明钱动向 |
| **数据缓存** | 本地CSV | 减少API调用 |

### 1.2 筛选标准

| 条件 | 阈值 |
|------|------|
| 股票池 | 剔除ST/新股，上市>60天 |
| 市值 | ≥ 100亿 |
| ROE(TTM) | > 5% |
| 扣非净利润(TTM) | > 0 |
| 行业RPS | > 85 |
| 获利比例 | < 15% |
| 筹码集中度 | < 20% |
| 乖离率 | -15% ~ 5% |
| KDJ | 日线金叉 |
| 量比 | 0.8 ~ 3.0 |

---

## 二、筛选结果

### 2.1 统计汇总

- **符合条件**: {len(results)} 只

### 2.2 符合条件股票

| 代码 | 名称 | 行业 | 现价 | ROE | 获利盘 | 集中度 | 乖离率 | KDJ | MACD | 量比 | 评分 |
|------|------|------|------|-----|--------|--------|--------|-----|------|------|------|
"""
    
    for r in results:
        report += f"| {r['code']} | {r['name']} | {r['industry']} | {r['price']:.2f} | {r['roe']:.1f}% | {r['profit_ratio']:.1f}% | {r['concentration']:.1f}% | {r['ma_bias']:.1f}% | {r['kdj']} | {r['macd_divergence']} | {r['volume_ratio']:.2f} | {r['score']} |\n"
    
    # 重点股票分析
    report += "\n## 三、重点股票分析\n"
    
    for r in results:
        report += generate_stock_report(r)
        report += "\n---\n"
    
    # 策略总结
    report += f"""
## 四、策略总结

### 4.1 策略说明

本策略为**高精度行业龙头反转策略 V2.0 (PRD V2.0)**，核心逻辑：

1. **行业筛选**: RPS > 85，只选真热点
2. **基本面**: ROE(TTM) > 5% + 扣非净利润 > 0
3. **市值门槛**: ≥ 100亿，确保流动性和机构持仓
4. **前复权**: 消除除权干扰
5. **超跌信号**: 获利盘 < 15%，筹码集中度 < 20%
6. **技术确认**: KDJ金叉 + 乖离率在-15%~5%区间 + MACD底背离
7. **资金验证**: 北向资金净流入

### 4.2 风控提示

- **止损**: 买入后收盘价跌破成本价 - 7%，无条件止损
- **止盈**: KDJ死叉或跌破MA10止盈
- **仓位**: 单只股票不超过总资金20%

### 4.3 风险提示

- 本策略仅供参考，不构成投资建议
- 市场有风险，投资需谨慎
- 建议结合基本面和技术面综合判断

---

*报告生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    # 保存报告
    report_file = f"选股报告_V2_{timestamp}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Markdown报告已保存: {report_file}")


if __name__ == "__main__":
    main()
