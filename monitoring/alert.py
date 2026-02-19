#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
告警模块
功能：
1. 性能阈值告警
2. 数据异常告警
3. 支持日志/控制台输出
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

# 尝试导入配置
try:
    from config import config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertRule:
    """告警规则"""

    def __init__(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        operator: str = ">",  # >, <, >=, <=, ==
        level: AlertLevel = AlertLevel.WARNING,
        enabled: bool = True
    ):
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.operator = operator
        self.level = level
        self.enabled = enabled

    def check(self, value: float) -> bool:
        """检查是否触发告警"""
        if not self.enabled:
            return False

        if self.operator == ">":
            return value > self.threshold
        elif self.operator == "<":
            return value < self.threshold
        elif self.operator == ">=":
            return value >= self.threshold
        elif self.operator == "<=":
            return value <= self.threshold
        elif self.operator == "==":
            return value == self.threshold
        return False


class Alert:
    """告警实例"""

    def __init__(
        self,
        rule: AlertRule,
        value: float,
        message: str,
        timestamp: datetime = None
    ):
        self.rule = rule
        self.value = value
        self.message = message
        self.timestamp = timestamp or datetime.now()
        self.level = rule.level
        self.name = rule.name

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'level': self.level.value,
            'message': self.message,
            'value': self.value,
            'threshold': self.rule.threshold,
            'timestamp': self.timestamp.isoformat()
        }


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self._lock = threading.Lock()
        self._rules: List[AlertRule] = []
        self._alerts: List[Alert] = []
        self._handlers: List[Callable[[Alert], None]] = []
        self._logger = logging.getLogger('monitoring.alert')

        # 默认告警处理器
        self._add_default_handlers()

        # 初始化默认规则
        self._init_default_rules()

    def _add_default_handlers(self):
        """添加默认处理器"""
        # 控制台输出处理器
        self.add_handler(self._console_handler)

    def _console_handler(self, alert: Alert):
        """控制台告警处理器"""
        level_str = alert.level.value.upper()
        print(f"[{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{level_str}] {alert.message}")

    def _init_default_rules(self):
        """初始化默认告警规则"""
        # API响应时间告警 (> 1秒) - 精确匹配
        self.add_rule(AlertRule(
            name="api_response_time",
            metric_name="api.duration",
            threshold=1.0,
            operator=">",
            level=AlertLevel.WARNING
        ))

        # 缓存命中率过低 (< 50%)
        self.add_rule(AlertRule(
            name="cache_hit_rate",
            metric_name="cache.*.hit_rate",
            threshold=50.0,
            operator="<",
            level=AlertLevel.WARNING
        ))

        # 筛选性能过慢 (> 10秒)
        self.add_rule(AlertRule(
            name="filter_performance",
            metric_name="filter.*.duration",
            threshold=10.0,
            operator=">",
            level=AlertLevel.WARNING
        ))

        # 内存使用过高 (> 500MB)
        self.add_rule(AlertRule(
            name="memory_usage",
            metric_name="memory.mb",
            threshold=500.0,
            operator=">",
            level=AlertLevel.WARNING
        ))

        # 连续失败告警
        self.add_rule(AlertRule(
            name="api_failure",
            metric_name="api.*.failure_rate",
            threshold=0.2,
            operator=">",
            level=AlertLevel.ERROR
        ))

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self._lock:
            self._rules.append(rule)

    def remove_rule(self, name: str):
        """移除告警规则"""
        with self._lock:
            self._rules = [r for r in self._rules if r.name != name]

    def get_rules(self) -> List[AlertRule]:
        """获取所有告警规则"""
        with self._lock:
            return self._rules.copy()

    def add_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        with self._lock:
            self._handlers.append(handler)

    def check_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None) -> List[Alert]:
        """检查指标并触发告警"""
        triggered_alerts = []

        with self._lock:
            rules_to_check = [r for r in self._rules if r.enabled]

        for rule in rules_to_check:
            # 支持通配符匹配
            if self._match_metric(rule.metric_name, metric_name):
                if rule.check(value):
                    alert = Alert(
                        rule=rule,
                        value=value,
                        message=f"{rule.name}: {metric_name}={value} (threshold: {rule.threshold})"
                    )
                    triggered_alerts.append(alert)
                    self._trigger_alert(alert)

        return triggered_alerts

    def _match_metric(self, pattern: str, metric_name: str) -> bool:
        """匹配指标名称（支持通配符）
        支持多种匹配方式：
        1. 精确匹配
        2. pattern是具体名称前缀，metric_name可以是pattern加上任意后缀
        3. pattern包含通配符，使用正则表达式匹配
        4. 反向：pattern中任意一段与metric_name的任意一段匹配
        """
        # 精确匹配
        if pattern == metric_name:
            return True

        # pattern是具体名称前缀，检查metric_name是否以pattern为前缀
        if metric_name.startswith(pattern):
            # 如果pattern后面紧跟着一个点，或者metric_name就是pattern
            if len(metric_name) > len(pattern):
                if metric_name[len(pattern)] == '.':
                    return True
            elif len(metric_name) == len(pattern):
                pass  # 完全相等的情况已经在上面处理了

        # pattern包含通配符，使用正则表达式匹配
        if "*" in pattern:
            import re
            # 先替换*为占位符，再替换.，然后把占位符替换成正则
            temp_placeholder = "__ASTERISK__"
            temp = pattern.replace("*", temp_placeholder)
            temp = temp.replace(".", r"\.")
            regex_pattern = temp.replace(temp_placeholder, r"[^.]*")
            try:
                if re.match(f"^{regex_pattern}$", metric_name):
                    return True
            except re.error:
                pass

        # 反向匹配：检查metric_name的每一段是否与pattern的任一段匹配
        # 例如: pattern="api.duration", metric_name="api.stock_list.duration"
        # -> pattern段: ["api", "duration"], metric段: ["api", "stock_list", "duration"]
        # -> "api"匹配"api", "duration"匹配"duration"
        # 注意：只有当pattern是metric的前缀（第一段匹配）时才使用反向匹配
        pattern_parts = pattern.split('.')
        metric_parts = metric_name.split('.')

        # 反向匹配只适用于pattern比metric分段更多
        if len(pattern_parts) >= len(metric_parts):
            return False

        # 检查第一段是否匹配（必须是前缀）
        if pattern_parts[0] != metric_parts[0]:
            return False

        # 现在检查pattern的每一段是否在metric_parts中（允许跨段匹配）
        for pp in pattern_parts:
            for mp in metric_parts:
                if pp == mp:
                    return True

        return False

    def _trigger_alert(self, alert: Alert):
        """触发告警"""
        with self._lock:
            self._alerts.append(alert)

        # 调用所有处理器
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                self._logger.error(f"Alert handler error: {e}")

        # 根据级别记录日志
        if alert.level == AlertLevel.CRITICAL or alert.level == AlertLevel.ERROR:
            self._logger.error(alert.message)
        elif alert.level == AlertLevel.WARNING:
            self._logger.warning(alert.message)
        else:
            self._logger.info(alert.message)

    def get_alerts(self, level: AlertLevel = None, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        with self._lock:
            alerts = self._alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        return alerts[-limit:]

    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        with self._lock:
            total = len(self._alerts)
            by_level = {}
            for alert in self._alerts:
                level = alert.level.value
                by_level[level] = by_level.get(level, 0) + 1

            return {
                'total': total,
                'by_level': by_level,
                'rules_count': len(self._rules),
                'active_rules': sum(1 for r in self._rules if r.enabled)
            }

    def clear_alerts(self):
        """清空告警历史"""
        with self._lock:
            self._alerts.clear()


# 全局告警管理器实例
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """获取全局告警管理器"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


# ==========================================
# 便捷函数
# ==========================================

def check_api_response_time(api_name: str, duration: float):
    """检查API响应时间"""
    get_alert_manager().check_metric(f'api.{api_name}.duration', duration)


def check_cache_hit_rate(cache_name: str, hit_rate: float):
    """检查缓存命中率"""
    get_alert_manager().check_metric(f'cache.{cache_name}.hit_rate', hit_rate)


def check_filter_performance(filter_name: str, duration: float):
    """检查筛选性能"""
    get_alert_manager().check_metric(f'filter.{filter_name}.duration', duration)


def check_memory_usage(memory_mb: float):
    """检查内存使用"""
    get_alert_manager().check_metric('memory.mb', memory_mb)


def add_custom_rule(
    name: str,
    metric_name: str,
    threshold: float,
    operator: str = ">",
    level: AlertLevel = AlertLevel.WARNING
):
    """添加自定义告警规则"""
    rule = AlertRule(name, metric_name, threshold, operator, level)
    get_alert_manager().add_rule(rule)


def get_alert_summary() -> Dict[str, Any]:
    """获取告警摘要"""
    return get_alert_manager().get_alert_summary()


def clear_alerts():
    """清空告警历史"""
    get_alert_manager().clear_alerts()


if __name__ == '__main__':
    # 测试代码
    print("=== Alert System Test ===")

    # 创建一个测试告警
    manager = get_alert_manager()

    # 触发一个API响应时间告警
    alerts = manager.check_metric('api.stock_list.duration', 1.5)
    print(f"Triggered {len(alerts)} alerts")

    # 触发一个缓存命中率告警
    alerts = manager.check_metric('cache.stock_list.hit_rate', 30.0)
    print(f"Triggered {len(alerts)} alerts")

    # 打印告警摘要
    summary = get_alert_summary()
    print(f"\nAlert Summary: {summary}")
