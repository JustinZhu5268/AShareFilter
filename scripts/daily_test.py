#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
每日回归测试脚本
功能：
1. 运行所有单元测试
2. 生成测试报告
3. 发送通知（可选）

使用方法:
    python scripts/daily_test.py
    python scripts/daily_test.py --report  # 生成HTML报告
    python scripts/daily_test.py --notify  # 发送通知（需配置）
"""

import os
import sys
import subprocess
import datetime
import argparse
import json
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class DailyTestRunner:
    """每日测试运行器"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_dir = self.project_root / 'tests'
        self.report_dir = self.project_root / 'test_reports'
        self.report_dir.mkdir(exist_ok=True)

        # 测试结果
        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'total': 0,
            'duration': 0,
            'tests': []
        }

    def run_tests(self, markers=None, verbose=True):
        """运行测试"""
        print("=" * 60)
        print(f"🚀 AShareFilter 每日回归测试")
        print(f"📅 测试时间: {self.results['timestamp']}")
        print("=" * 60)

        # 构建pytest命令
        cmd = [
            sys.executable, '-m', 'pytest',
            str(self.test_dir),
            '-v',
            '--tb=short',
            '--strict-markers',
        ]

        # 添加标记过滤
        if markers:
            for marker in markers:
                cmd.extend(['-m', marker])

        # 添加覆盖率
        cmd.extend([
            '--cov=.',
            '--cov-report=term-missing',
            '--cov-report=html:' + str(self.report_dir / 'htmlcov'),
            '--cov-report=xml:' + str(self.report_dir / 'coverage.xml'),
            '--cov-branch',
        ])

        # 排除不需要测试覆盖率的文件
        cmd.extend([
            '--cov-config=.coveragerc',
        ])

        # 设置环境变量
        env = os.environ.copy()
        env['USE_MOCK_DATA'] = 'true'

        # 运行测试
        start_time = datetime.datetime.now()

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                env=env
            )

            end_time = datetime.datetime.now()
            self.results['duration'] = (end_time - start_time).total_seconds()

            # 解析输出
            self._parse_output(result.stdout + result.stderr)

            # 打印结果
            self._print_results(result.stdout + result.stderr)

            return result.returncode == 0

        except Exception as e:
            print(f"❌ 测试运行失败: {e}")
            return False

    def _parse_output(self, output: str):
        """解析pytest输出"""
        lines = output.split('\n')

        for line in lines:
            # 解析测试统计
            if 'passed' in line.lower():
                # 例如: "10 passed"
                import re
                passed_match = re.search(r'(\d+) passed', line)
                if passed_match:
                    self.results['passed'] = int(passed_match.group(1))

                failed_match = re.search(r'(\d+) failed', line)
                if failed_match:
                    self.results['failed'] = int(failed_match.group(1))

                skipped_match = re.search(r'(\d+) skipped', line)
                if skipped_match:
                    self.results['skipped'] = int(skipped_match.group(1))

                error_match = re.search(r'(\d+) error', line)
                if error_match:
                    self.results['errors'] = int(error_match.group(1))

            # 解析总测试数
            if '=====' in line and 'test' in line.lower():
                import re
                total_match = re.search(r'(\d+) test', line)
                if total_match:
                    self.results['total'] = int(total_match.group(1))

    def _print_results(self, output: str):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        print(f"✅ 通过: {self.results['passed']}")
        print(f"❌ 失败: {self.results['failed']}")
        print(f"⏭️  跳过: {self.results['skipped']}")
        print(f"⚠️  错误: {self.results['errors']}")
        print(f"📈 总计: {self.results['total']}")
        print(f"⏱️  耗时: {self.results['duration']:.2f}秒")
        print("=" * 60)

        # 打印报告路径
        html_report = self.report_dir / 'htmlcov' / 'index.html'
        if html_report.exists():
            print(f"📄 HTML覆盖率报告: {html_report}")

        xml_report = self.report_dir / 'coverage.xml'
        if xml_report.exists():
            print(f"📄 XML覆盖率报告: {xml_report}")

    def save_report(self):
        """保存测试报告"""
        report_file = self.report_dir / f"test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"📄 测试报告已保存: {report_file}")
        return report_file

    def send_notification(self, success: bool):
        """发送通知（可选）"""
        # 这里可以集成邮件、钉钉、Slack等通知
        # 示例：打印通知
        if success:
            print("\n✅ 所有测试通过！")
        else:
            print("\n❌ 有测试失败，请检查！")


def main():
    parser = argparse.ArgumentParser(description='AShareFilter 每日回归测试')
    parser.add_argument('--markers', '-m', nargs='+', help='测试标记过滤')
    parser.add_argument('--report', '-r', action='store_true', help='生成详细报告')
    parser.add_argument('--notify', '-n', action='store_true', help='发送通知')
    parser.add_argument('--save', '-s', action='store_true', help='保存测试报告')

    args = parser.parse_args()

    # 创建测试运行器
    runner = DailyTestRunner()

    # 运行测试
    success = runner.run_tests(markers=args.markers)

    # 保存报告
    if args.save:
        runner.save_report()

    # 发送通知
    if args.notify:
        runner.send_notification(success)

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
