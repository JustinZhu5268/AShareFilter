"""
选股筛选逻辑模块
功能：
1. 股票池初筛 (ST/新股/停牌)
2. 行业RPS筛选
3. 龙头股筛选 (市值/财务)
4. 技术面筛选
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, List, Optional

# 导入配置
from config import config

# 导入API客户端
from api.tushare_client import TushareClient

# 导入扣非净利润数据
from api.data_fina_deducted import get_deducted_client

# 导入技术指标
from indicators.technical import (
    calculate_kdj,
    calculate_macd,
    calculate_ma,
    calculate_bollinger_bands,
    calculate_ma_bias,
    calculate_volume_ratio,
    get_latest_indicators,
    check_kdj_golden_cross,
    check_macd_divergence,
)

# 导入筹码分析
from indicators.chips import analyze_chips

# 导入周线数据
from api.data_weekly import get_weekly_client
from indicators.weekly_kdj import (
    calculate_weekly_kdj,
    check_weekly_kdj_oversold_detailed,
    analyze_weekly_tech,
)

# 导入机构持仓数据
from api.data_inst_holder import get_inst_holder_client

# 导入技术指标 - 行业趋势和支撑位共振
from indicators.technical import (
    check_industry_above_ma20,
    check_support_resonance,
    get_industry_trend,
)


class StockFilter:
    """股票筛选器"""

    def __init__(self, client: TushareClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []
        # 初始化扣非净利润客户端
        self._deducted_client = get_deducted_client(use_mock=client.use_mock)
        # 初始化周线数据客户端
        self._weekly_client = get_weekly_client()
        # 初始化机构持仓客户端
        self._inst_holder_client = get_inst_holder_client(use_mock=client.use_mock)
    
    def step1_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 1: 数据清洗
        - 剔除ST/*ST股票
        - 剔除新股 (上市不足60天)
        - 剔除停牌股票
        """
        if df is None or df.empty:
            return df
        
        print("  Step 1: 数据清洗")
        
        # 记录原始数量
        original_count = len(df)
        
        # 剔除ST/*ST
        df = df[~df['name'].str.contains(r'ST|\*ST|S*ST', na=False, regex=True)]
        st_removed = original_count - len(df)
        print(f"    剔除ST股票: {st_removed} 只")
        
        # 剔除新股 (上市不足60天)
        today = datetime.datetime.now()
        df['list_date'] = pd.to_datetime(df['list_date'])
        df['listed_days'] = (today - df['list_date']).dt.days
        df = df[df['listed_days'] >= config.MIN_LISTED_DAYS]
        
        # 保留正常上市状态
        df = df[df['list_status'] == 'L']
        
        print(f"    上市时间≥60天: {len(df)} 只")
        
        return df
    
    def step2_industry_filter(self, stocks: pd.DataFrame) -> List[str]:
        """
        Step 2: 行业RPS筛选 + 行业趋势判断
        返回: 符合RPS条件和趋势条件的行业列表
        """
        print("\n  Step 2: 行业RPS筛选")
        
        # 获取行业RPS数据
        df_rps = self.client.get_industry_rps()
        
        if df_rps is None or df_rps.empty:
            # 备用方案：使用股票数量最多的行业
            industry_counts = stocks['industry'].value_counts()
            top_industries = industry_counts.head(config.TOP_N_INDUSTRIES).index.tolist()
            print(f"    备用方案: 使用股票数量最多的{len(top_industries)}个行业")
            return top_industries
        
        # 取前20%的行业
        top_count = max(int(len(df_rps) * 0.2), config.TOP_N_INDUSTRIES)
        top_industries = df_rps.head(top_count)['industry'].tolist()
        
        print(f"    RPS筛选: {len(top_industries)} 个强势行业")
        
        # 显示前5个行业
        for i, row in df_rps.head(5).iterrows():
            print(f"      - {row['industry']}: {row['rps']:.1f}%")
        
        # ===== Agent 2: 行业趋势判断 =====
        if config.INDUSTRY_ABOVE_MA_REQUIRED:
            print("\n    -> 行业趋势判断：筛选站上20日均线的行业")
            trending_industries = []
            for industry in top_industries:
                try:
                    # 获取行业指数数据
                    industry_code = self._get_industry_code(industry)
                    if industry_code:
                        df_industry = self.client.get_sw_daily(industry_code)
                        if df_industry is not None and len(df_industry) >= config.INDUSTRY_MA_PERIOD:
                            trend_result = check_industry_above_ma20(df_industry)
                            if trend_result.get('above_ma20', False):
                                trending_industries.append(industry)
                                print(f"      ✓ {industry}: 站上20日均线")
                            else:
                                print(f"      ✗ {industry}: 未站上20日均线")
                        else:
                            # 数据不足时保留该行业
                            trending_industries.append(industry)
                    else:
                        trending_industries.append(industry)
                except Exception as e:
                    print(f"      ⚠ {industry}: 趋势判断失败 ({e})")
                    trending_industries.append(industry)
            
            # 如果有行业通过趋势筛选，使用这些行业；否则使用原始RPS结果
            if trending_industries:
                top_industries = trending_industries
                print(f"    趋势筛选后: {len(top_industries)} 个行业")
            else:
                print(f"    趋势筛选无符合条件，使用RPS筛选结果")
        
        return top_industries
    
    def _get_industry_code(self, industry_name: str) -> str:
        """
        获取行业指数代码

        Args:
            industry_name: 行业名称

        Returns:
            申万行业指数代码，如果行业不存在则返回 None
        """
        from config import config
        # 从配置文件读取行业映射，如果不存在则返回 None
        return config.INDUSTRY_CODE_MAP.get(industry_name, None)
    
    def step3_leader_filter(self, stocks: pd.DataFrame, industries: List[str]) -> List[Dict[str, Any]]:
        """
        Step 3: 筛选龙头股
        - 市值 ≥ 100亿
        - ROE(TTM) > 5%
        - 扣非净利润(TTM) > 0
        - 机构持仓比例 > 5%
        """
        print("\n  Step 3: 筛选行业龙头")
        
        # 预先加载市值数据
        print("    预加载市值数据...")
        self.client.get_all_market_caps()
        
        # 预先加载财务数据
        print("    预加载财务数据...")
        self.client.get_all_financial_ttm()
        
        results = []
        
        for industry in industries:
            # 获取该行业股票
            ind_stocks = stocks[stocks['industry'] == industry]
            
            stock_candidates = []
            
            # 筛选市值
            for _, stock in ind_stocks.iterrows():
                ts_code = stock['ts_code']
                
                market_cap = self.client.get_market_cap(ts_code)
                if market_cap < config.MIN_MARKET_CAP:
                    continue
                
                stock_candidates.append({
                    'ts_code': ts_code,
                    'symbol': stock['symbol'],
                    'name': stock['name'],
                    'industry': industry,
                    'market_cap': market_cap,
                })
            
            print(f"\n    行业: {industry}")
            print(f"      市值≥100亿: {len(stock_candidates)} 只")
            
            # 获取财务数据
            valid_stocks = []
            for stock in stock_candidates:
                ts_code = stock['ts_code']

                # 获取财务数据
                fin_data = self.client.get_financial_ttm(ts_code)

                roe_ttm = fin_data.get('roe_ttm', 0)
                net_profit = fin_data.get('net_profit_ttm', 0)

                if roe_ttm < config.MIN_ROE_TTM:
                    continue
                if net_profit <= config.MIN_NET_PROFIT_TTM:
                    continue

                # 获取扣非净利润(TTM)
                deducted_data = self._deducted_client.get_deducted_net_profit(ts_code)
                deducted_profit = deducted_data.get('deducted_net_profit', 0)

                if deducted_profit <= config.MIN_DEDUCTED_PROFIT_TTM:
                    continue

                stock['roe_ttm'] = roe_ttm
                stock['net_profit_ttm'] = net_profit
                stock['revenue_ttm'] = fin_data.get('revenue_ttm', 0)
                stock['deducted_profit_ttm'] = deducted_profit
                valid_stocks.append(stock)
            
            # ===== Agent 1: 机构持仓筛选 =====
            inst_holder_stocks = []
            if config.MIN_INST_HOLDING_RATIO > 0:
                print(f"      机构持仓筛选 (>{config.MIN_INST_HOLDING_RATIO}%)...")
                for stock in valid_stocks:
                    ts_code = stock['ts_code']
                    try:
                        # 获取机构持仓数据
                        inst_data = self._inst_holder_client.get_inst_holder(ts_code)
                        hold_ratio = inst_data.get('hold_ratio', 0.0)
                        
                        if hold_ratio >= config.MIN_INST_HOLDING_RATIO:
                            stock['inst_hold_ratio'] = hold_ratio
                            inst_holder_stocks.append(stock)
                            print(f"        ✓ {stock['name']}: 机构持仓{hold_ratio:.1f}%")
                        else:
                            print(f"        ✗ {stock['name']}: 机构持仓{hold_ratio:.1f}%")
                    except Exception as e:
                        print(f"        ⚠ {stock['name']}: 机构持仓获取失败 ({e})")
                        # 获取失败时保留该股票
                        stock['inst_hold_ratio'] = 0.0
                        inst_holder_stocks.append(stock)
                
                print(f"      机构持仓≥{config.MIN_INST_HOLDING_RATIO}%: {len(inst_holder_stocks)} 只")
            else:
                inst_holder_stocks = valid_stocks
            
            # 按ROE排序
            inst_holder_stocks.sort(key=lambda x: x.get('roe_ttm', 0), reverse=True)
            top_stocks = inst_holder_stocks[:config.TOP_N_STOCKS_PER_IND]
            
            print(f"      最终筛选: {len(top_stocks)} 只")
            
            results.extend(top_stocks)
        
        return results
    
    def step4_technical_filter(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Step 4: 技术面筛选
        - 乖离率: -15% ~ 5%
        - KDJ金叉
        - 量比: 0.8 ~ 3.0
        """
        print("\n  Step 4: 技术面筛选")
        
        results = []
        
        # 计算日期范围
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=120)).strftime('%Y%m%d')
        
        total = len(stocks)
        
        for i, stock in enumerate(stocks):
            ts_code = stock['ts_code']
            
            if (i + 1) % 5 == 0:
                print(f"    进度: {i + 1}/{total}")
            
            # 获取日线数据
            df_daily = self.client.get_daily_data(ts_code, start_date, end_date)
            
            if df_daily is None or len(df_daily) < 60:
                continue
            
            # 排序
            df_daily = df_daily.sort_values('trade_date')
            
            # 应用前复权
            adj_factor = self.client.get_adj_factor(ts_code)
            df_daily = self._apply_adjustment(df_daily, adj_factor)
            
            # 计算技术指标
            df_daily = calculate_kdj(df_daily)
            df_daily = calculate_macd(df_daily)
            df_daily = calculate_ma(df_daily)
            df_daily = calculate_bollinger_bands(df_daily)
            
            # 获取最新指标
            indicators = get_latest_indicators(df_daily)
            
            # 筹码分析
            chips = analyze_chips(df_daily)
            
            # 北向资金
            northbound = self.client.get_northbound_funds(ts_code)

            # 主力资金
            main_funds = self.client.get_main_funds(ts_code)

            # 周线KDJ检测
            weekly_kdj_status = None
            try:
                # 获取周线数据
                df_weekly = self._weekly_client.get_weekly_data(ts_code)
                if df_weekly is not None and len(df_weekly) >= 5:
                    # 计算周线KDJ
                    df_weekly = calculate_weekly_kdj(df_weekly)
                    # 获取详细状态
                    weekly_kdj_status = check_weekly_kdj_oversold_detailed(
                        df_weekly,
                        threshold=config.WEEKLY_KDJ_THRESHOLD
                    )
                    # 打印调试信息
                    print(f"      周线KDJ: J={weekly_kdj_status.get('j_value', 0):.1f}, 状态={weekly_kdj_status.get('status', '未知')}")
            except Exception as e:
                print(f"      周线KDJ计算失败: {e}")

            # ===== Agent 3: 支撑位共振检测 =====
            support_resonance = None
            if config.SUPPORT_RESONANCE_REQUIRED:
                try:
                    support_resonance = check_support_resonance(
                        df_daily,
                        ma60_tolerance=config.MA60_TOLERANCE,
                        bollinger_tolerance=config.BOLLINGER_TOLERANCE
                    )
                    resonance_status = support_resonance.get('support_level', 'none')
                    print(f"      支撑位共振: {resonance_status}")
                    if support_resonance.get('at_ma60'):
                        print(f"        - 获得MA60支撑: 距离{support_resonance.get('ma60_info', {}).get('distance', 0)*100:.1f}%")
                    if support_resonance.get('at_bollinger'):
                        print(f"        - 获得布林下轨支撑: 距离{support_resonance.get('bollinger_info', {}).get('distance', 0)*100:.1f}%")
                except Exception as e:
                    print(f"      支撑位共振检测失败: {e}")

            # 技术面筛选条件
            ma_bias = indicators.get('ma_bias', 0)
            vol_ratio = indicators.get('volume_ratio', 1)
            kdj_golden = indicators.get('kdj_golden_cross', False)
            
            # 打印调试信息
            print(f"\n    [调试] {stock['symbol']} {stock['name']}")
            print(f"      乖离率: {ma_bias:.1f}% (范围: {config.MA_BIAS_MIN}~{config.MA_BIAS_MAX}%)")
            print(f"      KDJ金叉: {'是' if kdj_golden else '否'}")
            print(f"      量比: {vol_ratio:.2f} (范围: {config.VOLUME_RATIO_MIN}~{config.VOLUME_RATIO_MAX})")
            print(f"      获利盘: {chips['profit_ratio']:.1f}%")
            print(f"      集中度: {chips['concentration']:.1f}%")
            
            # 筛选条件 - 增加周线KDJ检测（J值在正常区域，未超买）
            weekly_kdj_pass = True
            if weekly_kdj_status is not None:
                weekly_kdj_pass = weekly_kdj_status.get('j_value', 100) < config.WEEKLY_KDJ_THRESHOLD

            # ===== Agent 3: 支撑位共振筛选条件 =====
            support_resonance_pass = True
            if config.SUPPORT_RESONANCE_REQUIRED and support_resonance is not None:
                # 强共振或中等共振都通过
                support_level = support_resonance.get('support_level', 'none')
                support_resonance_pass = support_level in ['strong', 'medium']

            if (config.MA_BIAS_MIN <= ma_bias <= config.MA_BIAS_MAX and
                config.VOLUME_RATIO_MIN <= vol_ratio <= config.VOLUME_RATIO_MAX and
                chips['profit_ratio'] <= config.MAX_PROFIT_RATIO and
                chips['concentration'] <= config.MAX_CHIP_CONCENTRATION and
                weekly_kdj_pass and
                support_resonance_pass):
                
                result = {
                    'code': stock['symbol'],
                    'name': stock['name'],
                    'industry': stock['industry'],
                    'price': indicators.get('close', 0),
                    'market_cap': stock['market_cap'],
                    'roe': stock.get('roe_ttm', 0),
                    'net_profit': stock.get('net_profit_ttm', 0),
                    'revenue': stock.get('revenue_ttm', 0),
                    
                    # 技术指标
                    'ma_bias': ma_bias,
                    'kdj': '金叉' if kdj_golden else '死叉',
                    'volume_ratio': vol_ratio,
                    
                    # MACD
                    'macd_divergence': '底背离' if indicators.get('macd_divergence', {}).get('bullish') else '无',
                    
                    # 筹码
                    'profit_ratio': chips['profit_ratio'],
                    'concentration': chips['concentration'],
                    'single_peak': chips['single_peak'],
                    
                    # 资金
                    'northbound': northbound.get('total_net_inflow', 0),
                    'northbound_days': northbound.get('consecutive_days', 0),
                    'main_funds': main_funds.get('net_inflow_5d', 0),

                    # 布林带
                    'bb_position': self._calculate_bb_position(indicators),

                    # 周线KDJ
                    'weekly_kdj_j': weekly_kdj_status.get('j_value', 0) if weekly_kdj_status else 0,
                    'weekly_kdj_status': weekly_kdj_status.get('status', '未知') if weekly_kdj_status else '未知',

                    # 支撑位共振
                    'support_resonance': support_resonance.get('support_level', 'none') if support_resonance else 'none',
                    'support_at_ma60': support_resonance.get('at_ma60', False) if support_resonance else False,
                    'support_at_bollinger': support_resonance.get('at_bollinger', False) if support_resonance else False,

                    # 机构持仓 (从step3继承)
                    'inst_hold_ratio': stock.get('inst_hold_ratio', 0),
                }
                
                # 计算评分
                result['score'] = self._calculate_score(result)
                
                results.append(result)
                print(f"      ✅ 符合条件! 评分: {result['score']}")
        
        return results
    
    def _apply_adjustment(self, df: pd.DataFrame, adj_factor: float) -> pd.DataFrame:
        """应用前复权"""
        if adj_factor == 1.0 or adj_factor is None:
            return df
        
        df = df.copy()
        df['close'] = df['close'] * adj_factor
        df['high'] = df['high'] * adj_factor
        df['low'] = df['low'] * adj_factor
        df['open'] = df['open'] * adj_factor
        return df
    
    def _calculate_bb_position(self, indicators: Dict[str, Any]) -> str:
        """计算布林带位置"""
        close = indicators.get('close', 0)
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        
        if bb_upper == bb_lower:
            return '中轨'
        
        position = (close - bb_lower) / (bb_upper - bb_lower) * 100
        
        if position < 20:
            return '下轨附近'
        elif position < 40:
            return '中下轨'
        elif position < 60:
            return '中轨'
        elif position < 80:
            return '中上轨'
        else:
            return '上轨附近'
    
    def _calculate_score(self, stock: Dict[str, Any]) -> int:
        """计算综合评分 (满分100)"""
        score = 0
        
        # 1. 获利盘 < 10% (+15)
        if stock['profit_ratio'] < 10:
            score += 15
        elif stock['profit_ratio'] < 15:
            score += 10
        elif stock['profit_ratio'] < 20:
            score += 5
        
        # 2. KDJ金叉 (+15)
        if stock['kdj'] == '金叉':
            score += 15
        
        # 3. 北向资金连续净买入 (+15)
        if stock['northbound_days'] >= config.NORTHBOUND_DAYS:
            score += 15
        elif stock['northbound'] > 0:
            score += 10
        
        # 4. 主力资金净流入 (+10)
        if stock['main_funds'] > 0:
            score += 10
        
        # 5. MACD底背离 (+10)
        if stock['macd_divergence'] == '底背离':
            score += 10
        
        # 6. 单峰密集形态 (+5)
        if stock['single_peak']:
            score += 5

        # ===== Agent 4: 新增评分项 =====
        
        # 7. 机构持仓比例 (+10)
        inst_ratio = stock.get('inst_hold_ratio', 0)
        if inst_ratio >= 10:
            score += 10
        elif inst_ratio >= 5:
            score += 5
        
        # 8. 支撑位共振 (+10)
        resonance = stock.get('support_resonance', 'none')
        if resonance == 'strong':
            score += 10
        elif resonance == 'medium':
            score += 5
        
        # 9. 周线KDJ未超买 (+5)
        weekly_status = stock.get('weekly_kdj_status', '未知')
        if weekly_status == '未超买':
            score += 5
        
        # 10. 周线金叉 (+5)
        if weekly_status == '周线金叉+未超买':
            score += 5
        
        return score
    
    def run_full_filter(self) -> List[Dict[str, Any]]:
        """运行完整筛选流程"""
        print("\n" + "="*60)
        print("🚀 开始选股筛选流程")
        print("="*60)
        
        # Step 1: 获取股票列表并清洗
        stocks = self.client.get_stock_list()
        if stocks is None or stocks.empty:
            print("❌ 无法获取股票列表")
            return []
        
        stocks = self.step1_clean_data(stocks)
        print(f"✅ 清洗后剩余: {len(stocks)} 只")
        
        # Step 2: 行业RPS筛选
        top_industries = self.step2_industry_filter(stocks)
        
        # Step 3: 龙头筛选
        leaders = self.step3_leader_filter(stocks, top_industries)
        
        # Step 4: 技术面筛选
        results = self.step4_technical_filter(leaders)
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def analyze_single_stock(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """
        分析单只股票
        
        Args:
            ts_code: 股票代码 (如 '300274.SZ')
        
        Returns:
            分析结果字典
        """
        print(f"\n分析股票: {ts_code}")
        
        # 获取股票基本信息
        stocks = self.client.get_stock_list()
        stock_info = stocks[stocks['ts_code'] == ts_code]
        
        if stock_info.empty:
            print(f"❌ 找不到股票: {ts_code}")
            return None
        
        stock = stock_info.iloc[0]
        
        # 获取市值
        market_cap = self.client.get_market_cap(ts_code)
        
        # 获取财务数据
        fin_data = self.client.get_financial_ttm(ts_code)
        
        # 获取日线数据
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=120)).strftime('%Y%m%d')
        
        df_daily = self.client.get_daily_data(ts_code, start_date, end_date)
        
        if df_daily is None or len(df_daily) < 60:
            print(f"❌ 日线数据不足")
            return None
        
        # 排序和应用复权
        df_daily = df_daily.sort_values('trade_date')
        adj_factor = self.client.get_adj_factor(ts_code)
        df_daily = self._apply_adjustment(df_daily, adj_factor)
        
        # 计算技术指标
        df_daily = calculate_kdj(df_daily)
        df_daily = calculate_macd(df_daily)
        df_daily = calculate_ma(df_daily)
        df_daily = calculate_bollinger_bands(df_daily)
        
        # 获取指标
        indicators = get_latest_indicators(df_daily)
        
        # 筹码分析
        chips = analyze_chips(df_daily)
        
        # 资金流向
        northbound = self.client.get_northbound_funds(ts_code)
        main_funds = self.client.get_main_funds(ts_code)
        
        # 构建结果
        result = {
            'ts_code': ts_code,
            'code': stock['symbol'],
            'name': stock['name'],
            'industry': stock['industry'],
            'price': indicators.get('close', 0),
            'market_cap': market_cap,
            'roe': fin_data.get('roe_ttm', 0),
            'net_profit': fin_data.get('net_profit_ttm', 0),
            'revenue': fin_data.get('revenue_ttm', 0),
            
            # 技术指标
            'ma_bias': indicators.get('ma_bias', 0),
            'kdj': '金叉' if indicators.get('kdj_golden_cross') else '死叉',
            'volume_ratio': indicators.get('volume_ratio', 1),
            
            # MACD
            'macd': indicators.get('macd', 0),
            'macd_signal': indicators.get('macd_signal', 0),
            'macd_hist': indicators.get('macd_hist', 0),
            'macd_divergence': '底背离' if indicators.get('macd_divergence', {}).get('bullish') else '无',
            
            # 均线
            'ma5': indicators.get('ma5', 0),
            'ma10': indicators.get('ma10', 0),
            'ma20': indicators.get('ma20', 0),
            'ma60': indicators.get('ma60', 0),
            
            # 布林带
            'bb_upper': indicators.get('bb_upper', 0),
            'bb_middle': indicators.get('bb_middle', 0),
            'bb_lower': indicators.get('bb_lower', 0),
            'bb_position': self._calculate_bb_position(indicators),
            
            # 筹码
            'profit_ratio': chips['profit_ratio'],
            'concentration': chips['concentration'],
            'single_peak': chips['single_peak'],
            
            # 资金
            'northbound': northbound.get('total_net_inflow', 0),
            'northbound_days': northbound.get('consecutive_days', 0),
            'main_funds': main_funds.get('net_inflow_5d', 0),

            # 周线KDJ
            'weekly_kdj_j': 0,
            'weekly_kdj_status': '未知',
        }

        # 计算周线KDJ
        try:
            df_weekly = self._weekly_client.get_weekly_data(ts_code)
            if df_weekly is not None and len(df_weekly) >= 5:
                df_weekly = calculate_weekly_kdj(df_weekly)
                kdj_status = check_weekly_kdj_oversold_detailed(
                    df_weekly,
                    threshold=config.WEEKLY_KDJ_THRESHOLD
                )
                result['weekly_kdj_j'] = kdj_status.get('j_value', 0)
                result['weekly_kdj_status'] = kdj_status.get('status', '未知')
        except Exception as e:
            pass

        # 评分
        
        # 计算评分
        result['score'] = self._calculate_score(result)
        
        return result
