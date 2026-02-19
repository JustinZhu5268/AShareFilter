"""
单股票测试程序
用于测试300274阳光电源的完整选股逻辑
"""

import sys
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
    """测试单只股票 - 300274 阳光电源"""
    start_time = time.time()
    
    # 检查是否使用Mock模式
    use_mock = '--mock' in sys.argv or config.USE_MOCK_DATA
    
    # 打印缓存状态
    print_cache_status()
    
    print("\n" + "="*60)
    print("🔬 单股票测试 - 300274 阳光电源")
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
    
    # 测试股票代码
    test_stock = config.TEST_STOCK_CODE  # '300274'
    ts_code = f"{test_stock}.SZ" if not test_stock.endswith('.SZ') and not test_stock.endswith('.SH') else test_stock
    
    # 如果代码是纯数字，添加交易所后缀
    if '.' not in ts_code:
        # 根据代码判断交易所
        if ts_code.startswith('6'):
            ts_code = f"{ts_code}.SH"
        else:
            ts_code = f"{ts_code}.SZ"
    
    print(f"\n📊 目标股票: {ts_code}")
    
    # 分析单只股票
    result = filter_obj.analyze_single_stock(ts_code)
    
    if result:
        print("\n" + "="*60)
        print("📈 分析结果")
        print("="*60)
        
        # 打印基本信息
        print(f"\n【基本信息】")
        print(f"  代码: {result['code']}")
        print(f"  名称: {result['name']}")
        print(f"  行业: {result['industry']}")
        print(f"  现价: {result['price']:.2f} 元")
        print(f"  市值: {result['market_cap']:.0f} 亿")
        
        print(f"\n【财务数据】")
        print(f"  ROE(TTM): {result['roe']:.1f}%")
        print(f"  扣非净利润: {result['net_profit']/1e8:.2f} 亿元")
        print(f"  营收: {result['revenue']/1e8:.2f} 亿元")
        
        print(f"\n【技术指标】")
        print(f"  MA60乖离率: {result['ma_bias']:.1f}%")
        print(f"  KDJ: {result['kdj']}")
        print(f"  量比: {result['volume_ratio']:.2f}")
        print(f"  MACD: {result.get('macd_divergence', 'N/A')}")
        
        print(f"\n【均线位置】")
        print(f"  MA5: {result.get('ma5', 0):.2f}")
        print(f"  MA10: {result.get('ma10', 0):.2f}")
        print(f"  MA20: {result.get('ma20', 0):.2f}")
        print(f"  MA60: {result.get('ma60', 0):.2f}")
        
        print(f"\n【布林带】")
        print(f"  上轨: {result.get('bb_upper', 0):.2f}")
        print(f"  中轨: {result.get('bb_middle', 0):.2f}")
        print(f"  下轨: {result.get('bb_lower', 0):.2f}")
        print(f"  位置: {result.get('bb_position', 'N/A')}")
        
        print(f"\n【筹码分析】")
        print(f"  获利盘: {result['profit_ratio']:.1f}%")
        print(f"  集中度: {result['concentration']:.1f}%")
        print(f"  单峰密集: {'是' if result['single_peak'] else '否'}")
        
        print(f"\n【资金流向】")
        print(f"  北向资金: {result['northbound']:.0f} 万元")
        print(f"  北向连续天数: {result['northbound_days']} 天")
        print(f"  主力资金: {result['main_funds']:.0f} 万元")
        
        print(f"\n【综合评分】")
        print(f"  评分: {result['score']}/100")
        
        # 生成详细报告
        report = generate_stock_report(result)
        print(report)
        
        # 保存结果
        save_result(result)
        
    else:
        print("\n❌ 分析失败")
    
    # 打印耗时
    elapsed = time.time() - start_time
    print(f"\n⏱️ 耗时: {elapsed:.1f}秒")


def save_result(result: dict):
    """保存分析结果"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存CSV
    df = pd.DataFrame([result])
    csv_file = f"单股票测试_{timestamp}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 结果已保存: {csv_file}")


if __name__ == "__main__":
    main()
