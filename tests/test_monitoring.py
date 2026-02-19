#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
监控模块单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import time
from datetime import datetime


class TestMetricsCollector(unittest.TestCase):
    """测试指标收集器"""

    def setUp(self):
        """设置测试"""
        from monitoring import metrics
        metrics.clear_metrics()
        self.collector = metrics.get_metrics_collector()

    def test_increment_counter(self):
        """测试计数器递增"""
        self.collector.increment('test.counter', 5)
        self.collector.increment('test.counter', 3)

        count = self.collector.get_counter('test.counter')
        self.assertEqual(count, 8)

    def test_record_time(self):
        """测试时间记录"""
        self.collector.record_time('test.operation', 0.5)

        metrics_list = self.collector.get_metrics_by_name('test.operation')
        self.assertEqual(len(metrics_list), 1)
        self.assertEqual(metrics_list[0].value, 0.5)

    def test_timer(self):
        """测试计时器"""
        self.collector.start_timer('test.timer')
        time.sleep(0.1)
        duration = self.collector.stop_timer('test.timer')

        self.assertIsNotNone(duration)
        self.assertGreater(duration, 0.05)

    def test_get_average_time(self):
        """测试获取平均时间"""
        self.collector.record_time('test.avg', 0.1)
        self.collector.record_time('test.avg', 0.2)
        self.collector.record_time('test.avg', 0.3)

        avg = self.collector.get_average_time('test.avg')
        self.assertAlmostEqual(avg, 0.2)

    def test_get_summary(self):
        """测试获取摘要"""
        self.collector.increment('test.counter', 5)
        self.collector.record_time('test.operation', 0.5)

        summary = self.collector.get_summary()

        self.assertIn('counters', summary)
        self.assertIn('metrics', summary)
        self.assertEqual(summary['counters']['test.counter'], 5)

    def test_clear(self):
        """测试清空指标"""
        self.collector.increment('test.counter', 5)
        self.collector.record_time('test.operation', 0.5)

        self.collector.clear()

        summary = self.collector.get_summary()
        self.assertEqual(len(summary['counters']), 0)
        self.assertEqual(len(summary['metrics']), 0)


class TestMetricsConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    def setUp(self):
        """设置测试"""
        from monitoring import metrics
        metrics.clear_metrics()

    def test_record_api_call(self):
        """测试记录API调用"""
        from monitoring.metrics import record_api_call

        record_api_call('stock_list', 0.5, success=True)
        record_api_call('stock_list', 0.8, success=True)
        record_api_call('stock_list', 1.2, success=False)

        from monitoring.metrics import get_metrics_collector
        collector = get_metrics_collector()

        self.assertEqual(collector.get_counter('api.stock_list.total'), 3)
        self.assertEqual(collector.get_counter('api.stock_list.success'), 2)

    def test_record_cache_operation(self):
        """测试记录缓存操作"""
        from monitoring.metrics import record_cache_operation

        record_cache_operation('stock_list', hit=True)
        record_cache_operation('stock_list', hit=True)
        record_cache_operation('stock_list', hit=False)

        from monitoring.metrics import get_cache_hit_rate
        hit_rate = get_cache_hit_rate('stock_list')

        self.assertAlmostEqual(hit_rate, 66.67, places=2)

    def test_record_filter_performance(self):
        """测试记录筛选性能"""
        from monitoring.metrics import record_filter_performance

        record_filter_performance('step1', 0.5, 100)
        record_filter_performance('step2', 1.2, 50)

        from monitoring.metrics import get_metrics_collector
        collector = get_metrics_collector()

        self.assertEqual(collector.get_counter('filter.step1.results'), 100)
        self.assertEqual(collector.get_counter('filter.step2.results'), 50)


class TestAlertRule(unittest.TestCase):
    """测试告警规则"""

    def test_greater_than_operator(self):
        """测试大于操作符"""
        from monitoring.alert import AlertRule, AlertLevel

        rule = AlertRule(
            name="test",
            metric_name="test.metric",
            threshold=10.0,
            operator=">",
            level=AlertLevel.WARNING
        )

        self.assertTrue(rule.check(15.0))
        self.assertFalse(rule.check(10.0))
        self.assertFalse(rule.check(5.0))

    def test_less_than_operator(self):
        """测试小于操作符"""
        from monitoring.alert import AlertRule, AlertLevel

        rule = AlertRule(
            name="test",
            metric_name="test.metric",
            threshold=10.0,
            operator="<",
            level=AlertLevel.WARNING
        )

        self.assertTrue(rule.check(5.0))
        self.assertFalse(rule.check(10.0))
        self.assertFalse(rule.check(15.0))

    def test_disabled_rule(self):
        """测试禁用的规则"""
        from monitoring.alert import AlertRule, AlertLevel

        rule = AlertRule(
            name="test",
            metric_name="test.metric",
            threshold=10.0,
            operator=">",
            level=AlertLevel.WARNING,
            enabled=False
        )

        self.assertFalse(rule.check(15.0))


class TestAlertManager(unittest.TestCase):
    """测试告警管理器"""

    def setUp(self):
        """设置测试"""
        from monitoring import alert
        alert.clear_alerts()
        self.manager = alert.get_alert_manager()

    def test_add_rule(self):
        """测试添加规则"""
        from monitoring.alert import AlertRule, AlertLevel

        initial_count = len(self.manager.get_rules())

        rule = AlertRule(
            name="custom_rule",
            metric_name="custom.metric",
            threshold=100.0,
            level=AlertLevel.INFO
        )
        self.manager.add_rule(rule)

        self.assertEqual(len(self.manager.get_rules()), initial_count + 1)

    def test_remove_rule(self):
        """测试移除规则"""
        from monitoring.alert import AlertRule, AlertLevel

        rule = AlertRule(
            name="temp_rule",
            metric_name="temp.metric",
            threshold=100.0,
            level=AlertLevel.INFO
        )
        self.manager.add_rule(rule)
        self.manager.remove_rule("temp_rule")

        rules = self.manager.get_rules()
        self.assertFalse(any(r.name == "temp_rule" for r in rules))

    def test_check_metric_trigger(self):
        """测试指标检查触发告警"""
        alerts = self.manager.check_metric('api.duration', 2.0)

        # 阈值是1.0，2.0 > 1.0 应该触发告警
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].name, "api_response_time")

    def test_check_metric_no_trigger(self):
        """测试指标检查不触发告警"""
        alerts = self.manager.check_metric('api.duration', 0.5)

        # 阈值是1.0，0.5 < 1.0 不应该触发告警
        self.assertEqual(len(alerts), 0)

    def test_get_alerts(self):
        """测试获取告警"""
        self.manager.check_metric('api.duration', 2.0)
        self.manager.check_metric('api.duration', 3.0)

        alerts = self.manager.get_alerts()
        self.assertEqual(len(alerts), 2)

    def test_get_alert_summary(self):
        """测试获取告警摘要"""
        self.manager.check_metric('api.duration', 2.0)
        self.manager.check_metric('api.duration', 3.0)

        summary = self.manager.get_alert_summary()

        self.assertIn('total', summary)
        self.assertIn('by_level', summary)
        self.assertEqual(summary['total'], 2)

    def test_clear_alerts(self):
        """测试清空告警"""
        self.manager.check_metric('api.duration', 2.0)
        self.manager.clear_alerts()

        alerts = self.manager.get_alerts()
        self.assertEqual(len(alerts), 0)


class TestAlertConvenienceFunctions(unittest.TestCase):
    """测试告警便捷函数"""

    def setUp(self):
        """设置测试"""
        from monitoring import alert
        alert.clear_alerts()

    def test_check_api_response_time(self):
        """测试API响应时间检查"""
        from monitoring.alert import check_api_response_time

        check_api_response_time('stock_list', 2.0)

        from monitoring.alert import get_alert_summary
        summary = get_alert_summary()

        self.assertEqual(summary['total'], 1)

    def test_check_cache_hit_rate(self):
        """测试缓存命中率检查"""
        from monitoring.alert import check_cache_hit_rate

        check_cache_hit_rate('stock_list', 30.0)

        from monitoring.alert import get_alert_summary
        summary = get_alert_summary()

        self.assertEqual(summary['total'], 1)

    def test_check_filter_performance(self):
        """测试筛选性能检查"""
        from monitoring.alert import check_filter_performance

        check_filter_performance('full_filter', 15.0)

        from monitoring.alert import get_alert_summary
        summary = get_alert_summary()

        self.assertEqual(summary['total'], 1)


class TestAlertWildcardMatching(unittest.TestCase):
    """测试告警通配符匹配"""

    def setUp(self):
        """设置测试"""
        from monitoring import alert
        alert.clear_alerts()
        self.manager = alert.get_alert_manager()

    def test_wildcard_matching(self):
        """测试通配符匹配"""
        # 使用通配符的规则应该匹配多个指标
        alerts = self.manager.check_metric('cache.stock_list.hit_rate', 30.0)

        # cache.*.hit_rate 应该匹配 cache.stock_list.hit_rate
        self.assertGreater(len(alerts), 0)


if __name__ == '__main__':
    unittest.main()
