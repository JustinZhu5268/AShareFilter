#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AShareFilter 测试运行器
自动设置UTF-8编码，解决PowerShell中文显示问题
"""
import subprocess
import sys
import os

def main():
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 运行测试
    cmd = [sys.executable, '-m', 'unittest', 'discover', 'tests', '-v']
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
