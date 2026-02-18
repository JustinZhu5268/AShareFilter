#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AShareFilter 单股票测试运行器
自动设置UTF-8编码，解决PowerShell中文显示问题
用法: python run_single_test.py [股票代码]
示例: python run_single_test.py 300274
"""
import subprocess
import sys
import os

def main():
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 获取股票代码
    stock_code = sys.argv[1] if len(sys.argv) > 1 else '300274'
    
    # 运行单股票测试
    cmd = [sys.executable, 'run_single.py', stock_code]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
