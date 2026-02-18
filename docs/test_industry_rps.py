#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试行业RPS功能"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.tushare_client import TushareClient


def main():
    # 测试Mock模式
    print("="*60)
    print("测试Mock模式")
    print("="*60)
    client = TushareClient(use_mock=True)
    print('Mock模式初始化成功')
    df = client.get_industry_rps()
    if df is not None:
        print('行业RPS获取成功:')
        print(df.head(10))
    else:
        print('行业RPS获取失败')


if __name__ == '__main__':
    main()
