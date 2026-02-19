"""
信号评估模块
"""

from typing import Dict, Any, List
from config import config

# 导入风控管理
from strategy.risk_management import get_risk_manager


def evaluate_buy_signal(stock: Dict[str, Any]) -> Dict[str, Any]:
    """
    评估买入信号
    
    Args:
        stock: 股票分析结果
    
    Returns:
        信号评估结果
    """
    signals = []
    score = 0
    
    # 必须满足的条件
    must_have = []
    
    # 1. 乖离率检查
    if config.MA_BIAS_MIN <= stock.get('ma_bias', 0) <= config.MA_BIAS_MAX:
        must_have.append({
            'name': '乖离率',
            'value': f"{stock.get('ma_bias', 0):.1f}%",
            'status': 'pass'
        })
    else:
        must_have.append({
            'name': '乖离率',
            'value': f"{stock.get('ma_bias', 0):.1f}%",
            'status': 'fail'
        })
    
    # 2. 量比检查
    vol_ratio = stock.get('volume_ratio', 1)
    if config.VOLUME_RATIO_MIN <= vol_ratio <= config.VOLUME_RATIO_MAX:
        must_have.append({
            'name': '量比',
            'value': f"{vol_ratio:.2f}",
            'status': 'pass'
        })
    else:
        must_have.append({
            'name': '量比',
            'value': f"{vol_ratio:.2f}",
            'status': 'fail'
        })
    
    # 3. 获利盘检查
    profit_ratio = stock.get('profit_ratio', 100)
    if profit_ratio <= config.MAX_PROFIT_RATIO:
        must_have.append({
            'name': '获利盘',
            'value': f"{profit_ratio:.1f}%",
            'status': 'pass'
        })
    else:
        must_have.append({
            'name': '获利盘',
            'value': f"{profit_ratio:.1f}%",
            'status': 'fail'
        })
    
    # 4. KDJ金叉
    if stock.get('kdj') == '金叉':
        signals.append({
            'name': 'KDJ金叉',
            'score': 20,
            'description': '短期买点信号'
        })
        score += 20
    
    # 5. MACD底背离
    if stock.get('macd_divergence') == '底背离':
        signals.append({
            'name': 'MACD底背离',
            'score': 15,
            'description': '强烈买入信号'
        })
        score += 15
    
    # 6. 北向资金
    northbound_days = stock.get('northbound_days', 0)
    if northbound_days >= config.NORTHBOUND_DAYS:
        signals.append({
            'name': '北向资金连续净买入',
            'score': 20,
            'description': f'连续{northbound_days}天净买入'
        })
        score += 20
    elif stock.get('northbound', 0) > 0:
        signals.append({
            'name': '北向资金净流入',
            'score': 10,
            'description': '外资关注'
        })
        score += 10
    
    # 7. 主力资金
    if stock.get('main_funds', 0) > 0:
        signals.append({
            'name': '主力资金净流入',
            'score': 15,
            'description': '国内主力关注'
        })
        score += 15
    
    # 8. 单峰密集
    if stock.get('single_peak', False):
        signals.append({
            'name': '单峰密集形态',
            'score': 10,
            'description': '主力吸筹完成'
        })
        score += 10
    
    # 判断是否通过
    all_pass = all(s['status'] == 'pass' for s in must_have)

    # 风控评估
    risk_manager = get_risk_manager()
    risk_evaluation = risk_manager.evaluate_risk(stock)

    # 评级
    rating = ''
    recommendation = ''
    if score >= 80:
        rating = '⭐⭐⭐ 强力买入'
        recommendation = '重点关注'
    elif score >= 60:
        rating = '⭐⭐ 建议买入'
        recommendation = '正常关注'
    elif score >= 40:
        rating = '⭐ 观望'
        recommendation = '谨慎参与'
    else:
        rating = '- 不建议'
        recommendation = '等待更好时机'

    return {
        'stock_code': stock.get('code', ''),
        'stock_name': stock.get('name', ''),
        'must_have': must_have,
        'signals': signals,
        'total_score': score,
        'rating': rating,
        'recommendation': recommendation,
        'qualified': all_pass,
        # 风控评估结果
        'risk_score': risk_evaluation.get('risk_score', 50),
        'risk_level': risk_evaluation.get('risk_level', 'medium'),
        'risk_factors': risk_evaluation.get('factors', []),
    }


def generate_stock_report(stock: Dict[str, Any]) -> str:
    """
    生成单只股票的详细分析报告
    
    Args:
        stock: 股票分析结果
    
    Returns:
        Markdown格式的报告
    """
    signal = evaluate_buy_signal(stock)
    
    report = f"""
### {stock.get('code')} {stock.get('name')}

**行业**: {stock.get('industry', 'N/A')}
**现价**: {stock.get('price', 0):.2f} 元
**市值**: {stock.get('market_cap', 0):.0f} 亿
**ROE(TTM)**: {stock.get('roe', 0):.1f}%

**扣非净利润(TTM)**: {stock.get('net_profit', 0)/1e8:.0f} 亿元
**营收(TTM)**: {stock.get('revenue', 0)/1e8:.0f} 亿元

---

#### 技术指标

| 指标 | 值 | 阈值 | 状态 |
|------|-----|------|------|
| 乖离率 | {stock.get('ma_bias', 0):.1f}% | {config.MA_BIAS_MIN}~{config.MA_BIAS_MAX}% | {'✅' if config.MA_BIAS_MIN <= stock.get('ma_bias', 0) <= config.MA_BIAS_MAX else '❌'} |
| KDJ | {stock.get('kdj', 'N/A')} | 金叉 | {'✅' if stock.get('kdj') == '金叉' else '❌'} |
| 量比 | {stock.get('volume_ratio', 1):.2f} | {config.VOLUME_RATIO_MIN}~{config.VOLUME_RATIO_MAX} | {'✅' if config.VOLUME_RATIO_MIN <= stock.get('volume_ratio', 1) <= config.VOLUME_RATIO_MAX else '❌'} |
| 布林带 | {stock.get('bb_position', 'N/A')} | - | - |

#### 筹码分析

| 指标 | 值 | 阈值 | 状态 |
|------|-----|------|------|
| 获利盘 | {stock.get('profit_ratio', 0):.1f}% | <{config.MAX_PROFIT_RATIO}% | {'✅' if stock.get('profit_ratio', 0) <= config.MAX_PROFIT_RATIO else '❌'} |
| 集中度 | {stock.get('concentration', 0):.1f}% | <{config.MAX_CHIP_CONCENTRATION}% | {'✅' if stock.get('concentration', 0) <= config.MAX_CHIP_CONCENTRATION else '❌'} |
| 单峰密集 | {'是' if stock.get('single_peak') else '否'} | 是 | {'✅' if stock.get('single_peak') else '❌'} |

#### 资金流向

| 资金类型 | 金额(万元) | 状态 |
|----------|-----------|------|
| 北向资金 | {stock.get('northbound', 0):.0f} | {'✅净流入' if stock.get('northbound', 0) > 0 else '❌净流出'} |
| 主力资金 | {stock.get('main_funds', 0):.0f} | {'✅净流入' if stock.get('main_funds', 0) > 0 else '❌净流出'} |

---

#### 综合评估

**评分**: {signal['total_score']}/100
**评级**: {signal['rating']}
**建议**: {signal['recommendation']}

**选股理由**:
"""
    
    # 添加选股理由
    if stock.get('profit_ratio', 0) < 10:
        report += "- 获利盘较低，存在超跌反弹机会\n"
    if stock.get('concentration', 0) < 15:
        report += "- 筹码集中度低，主力控盘度高\n"
    if stock.get('ma_bias', 0) < 0:
        report += "- 股价回踩MA60均线附近，获得支撑\n"
    if stock.get('kdj') == '金叉':
        report += "- KDJ指标金叉，短期买点信号\n"
    if stock.get('macd_divergence') == '底背离':
        report += "- MACD底背离，反转信号强烈\n"
    if stock.get('northbound', 0) > 0:
        report += "- 北向资金净流入，聪明钱关注\n"
    
    return report
