"""
风控管理模块
功能：
1. 止损检测
2. 止盈检测 (KDJ死叉/跌破MA10)
3. 仓位管理
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from config import config


class RiskManager:
    """风控管理器"""

    def __init__(self):
        self.stop_loss_pct = config.STOP_LOSS_PCT
        self.take_profit_pct = config.TAKE_PROFIT_PCT

    def check_stop_loss(self, buy_price: float, current_price: float) -> Dict[str, Any]:
        """
        检查是否触发止损

        Args:
            buy_price: 买入价格
            current_price: 当前价格

        Returns:
            {
                'triggered': bool,  # 是否触发止损
                'loss_pct': float,   # 亏损百分比
                'action': str        # 建议动作
            }
        """
        if buy_price <= 0:
            return {
                'triggered': False,
                'loss_pct': 0.0,
                'action': '无效价格'
            }

        # 计算亏损比例
        loss_pct = (current_price - buy_price) / buy_price * 100

        # 检查是否触发止损 (跌破成本价 -7%)
        triggered = loss_pct <= -self.stop_loss_pct

        action = '止损' if triggered else '持有'

        return {
            'triggered': triggered,
            'loss_pct': loss_pct,
            'action': action
        }

    def check_take_profit_kdj_dead_cross(self, df: pd.DataFrame, buy_price: float) -> Dict[str, Any]:
        """
        检查是否因KDJ死叉触发止盈

        Args:
            df: 包含 K, D 列的日线DataFrame
            buy_price: 买入价格

        Returns:
            {
                'triggered': bool,     # 是否触发
                'reason': str,         # 原因
                'profit_pct': float,   # 盈利百分比
                'action': str          # 建议动作
            }
        """
        if df is None or len(df) < 2:
            return {
                'triggered': False,
                'reason': '数据不足',
                'profit_pct': 0.0,
                'action': '持有'
            }

        # 获取最新两天的K和D
        k_current = df['K'].iloc[-1]
        d_current = df['D'].iloc[-1]
        k_prev = df['K'].iloc[-2]
        d_prev = df['D'].iloc[-2]

        # 检查死叉: 昨天K>=D，今天K<D
        dead_cross = k_prev >= d_prev and k_current < d_current

        # 计算当前盈利
        current_price = df['close'].iloc[-1]
        profit_pct = (current_price - buy_price) / buy_price * 100 if buy_price > 0 else 0

        if dead_cross:
            return {
                'triggered': True,
                'reason': 'KDJ死叉',
                'profit_pct': profit_pct,
                'action': '减仓50%'
            }

        return {
            'triggered': False,
            'reason': '无死叉',
            'profit_pct': profit_pct,
            'action': '持有'
        }

    def check_take_profit_ma10_break(self, df: pd.DataFrame, buy_price: float) -> Dict[str, Any]:
        """
        检查是否因跌破MA10触发止盈

        Args:
            df: 包含 close, ma10 列的日线DataFrame
            buy_price: 买入价格

        Returns:
            {
                'triggered': bool,     # 是否触发
                'reason': str,         # 原因
                'profit_pct': float,   # 盈利百分比
                'action': str          # 建议动作
            }
        """
        if df is None or len(df) < 1:
            return {
                'triggered': False,
                'reason': '数据不足',
                'profit_pct': 0.0,
                'action': '持有'
            }

        # 检查是否有ma10列
        if 'ma10' not in df.columns:
            return {
                'triggered': False,
                'reason': '缺少MA10数据',
                'profit_pct': 0.0,
                'action': '持有'
            }

        # 获取最新价格和MA10
        current_price = df['close'].iloc[-1]
        ma10 = df['ma10'].iloc[-1]

        # 检查是否跌破MA10
        ma10_break = current_price < ma10 if not pd.isna(ma10) else False

        # 计算当前盈利
        profit_pct = (current_price - buy_price) / buy_price * 100 if buy_price > 0 else 0

        if ma10_break:
            return {
                'triggered': True,
                'reason': '跌破MA10',
                'profit_pct': profit_pct,
                'action': '全部止盈'
            }

        return {
            'triggered': False,
            'reason': '未跌破MA10',
            'profit_pct': profit_pct,
            'action': '持有'
        }

    def calculate_position_size(self, total_capital: float, stock_count: int = 5,
                               max_position_pct: float = 20.0) -> Dict[str, Any]:
        """
        计算仓位大小

        Args:
            total_capital: 总资金
            stock_count: 持仓股票数量
            max_position_pct: 单只股票最大仓位比例

        Returns:
            {
                'max_per_stock': float,  # 单只股票最大金额
                'suggested_count': int,   # 建议持仓数量
                'max_total_pct': float   # 最大总仓位比例
            }
        """
        if total_capital <= 0 or stock_count <= 0:
            return {
                'max_per_stock': 0.0,
                'suggested_count': 0,
                'max_total_pct': 0.0
            }

        # 单只股票最大金额
        max_per_stock = total_capital * (max_position_pct / 100)

        # 建议持仓数量 (不超过8只)
        suggested_count = min(stock_count, 8)

        # 计算如果满仓的总仓位
        max_total_pct = suggested_count * max_position_pct

        return {
            'max_per_stock': max_per_stock,
            'suggested_count': suggested_count,
            'max_total_pct': min(max_total_pct, 80.0)  # 总仓位不超过80%
        }

    def evaluate_risk(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        综合评估股票风险

        Args:
            stock_data: 包含股票分析数据的字典

        Returns:
            风险评估结果
        """
        risk_level = '低'
        warnings = []
        score = 100

        # 检查获利盘
        profit_ratio = stock_data.get('profit_ratio', 0)
        if profit_ratio > 30:
            risk_level = '高'
            warnings.append('获利盘过高，可能面临抛压')
            score -= 30
        elif profit_ratio > 15:
            risk_level = '中'
            warnings.append('获利盘偏高')
            score -= 15

        # 检查乖离率
        ma_bias = stock_data.get('ma_bias', 0)
        if ma_bias > 10:
            risk_level = '高'
            warnings.append('乖离率过高，警惕回调')
            score -= 20
        elif ma_bias > 5:
            risk_level = '中'
            warnings.append('乖离率偏高')
            score -= 10

        # 检查量比
        vol_ratio = stock_data.get('volume_ratio', 1)
        if vol_ratio > 5:
            risk_level = '高'
            warnings.append('量比过高，警惕放量下跌')
            score -= 20
        elif vol_ratio > 3:
            risk_level = '中'
            warnings.append('量比偏高')
            score -= 10

        # 检查北向资金
        northbound = stock_data.get('northbound', 0)
        if northbound < 0:
            warnings.append('北向资金净流出')
            score -= 10

        # 检查评分
        stock_score = stock_data.get('score', 0)
        if stock_score < 40:
            risk_level = '高'
            score -= 20
        elif stock_score < 60:
            risk_level = '中'
            score -= 10

        # 确定最终风险等级
        if score >= 80:
            risk_level = '低'
        elif score >= 60:
            risk_level = '中'

        return {
            'risk_level': risk_level,
            'risk_score': score,
            'warnings': warnings,
            'recommendation': '买入' if score >= 60 else '观望'
        }

    def get_trade_signal(self, position: Dict[str, Any], market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        获取交易信号

        Args:
            position: 持仓信息 {'buy_price': float, 'buy_date': str}
            market_data: 当前市场数据

        Returns:
            交易信号 {'action': str, 'reason': str, 'priority': int}
        """
        buy_price = position.get('buy_price', 0)
        if buy_price <= 0 or market_data is None or market_data.empty:
            return {
                'action': '持有',
                'reason': '数据不足',
                'priority': 0
            }

        current_price = market_data['close'].iloc[-1]

        # 1. 首先检查止损
        stop_loss_result = self.check_stop_loss(buy_price, current_price)
        if stop_loss_result['triggered']:
            return {
                'action': '止损',
                'reason': f"触发止损 ({stop_loss_result['loss_pct']:.1f}%)",
                'priority': 1  # 最高优先级
            }

        # 2. 检查止盈 - KDJ死叉
        if 'K' in market_data.columns and 'D' in market_data.columns:
            kdj_result = self.check_take_profit_kdj_dead_cross(market_data, buy_price)
            if kdj_result['triggered']:
                return {
                    'action': '减仓50%',
                    'reason': 'KDJ死叉',
                    'priority': 2
                }

        # 3. 检查止盈 - 跌破MA10
        if 'ma10' in market_data.columns:
            ma10_result = self.check_take_profit_ma10_break(market_data, buy_price)
            if ma10_result['triggered']:
                return {
                    'action': '全部止盈',
                    'reason': '跌破MA10',
                    'priority': 2
                }

        # 4. 检查是否达到止盈线
        profit_pct = (current_price - buy_price) / buy_price * 100
        if profit_pct >= self.take_profit_pct:
            return {
                'action': '考虑止盈',
                'reason': f"盈利{profit_pct:.1f}%，达到止盈线",
                'priority': 3
            }

        return {
            'action': '持有',
            'reason': '无风控信号',
            'priority': 0
        }


# 全局风控管理器实例
_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    """获取全局风控管理器"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager()
    return _risk_manager
