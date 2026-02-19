#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
监控指标收集模块
功能：
1. API调用耗时统计
2. 缓存命中率统计
3. 筛选性能数据收集
4. 内存使用情况监控
"""

import time
import threading
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MetricPoint:
    """指标数据点"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器 - 线程安全"""

    def __init__(self):
        self._lock = threading.Lock()
        self._metrics: List[MetricPoint] = []
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, float] = {}
        if HAS_PSUTIL:
            try:
                self._process = psutil.Process(os.getpid())
            except Exception:
                self._process = None
        else:
            self._process = None

    def increment(self, name: str, value: int = 1):
        """计数器递增"""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def record_time(self, name: str, duration: float):
        """记录时间指标"""
        with self._lock:
            self._metrics.append(MetricPoint(
                name=name,
                value=duration,
                timestamp=datetime.now()
            ))

    def start_timer(self, name: str):
        """开始计时"""
        self._timers[name] = time.time()

    def stop_timer(self, name: str) -> Optional[float]:
        """停止计时并记录"""
        if name not in self._timers:
            return None
        duration = time.time() - self._timers[name]
        self.record_time(name, duration)
        del self._timers[name]
        return duration

    def get_counter(self, name: str) -> int:
        """获取计数器值"""
        with self._lock:
            return self._counters.get(name, 0)

    def get_all_metrics(self) -> List[MetricPoint]:
        """获取所有指标"""
        with self._lock:
            return self._metrics.copy()

    def get_metrics_by_name(self, name: str) -> List[MetricPoint]:
        """根据名称获取指标"""
        with self._lock:
            return [m for m in self._metrics if m.name == name]

    def get_average_time(self, name: str) -> Optional[float]:
        """获取平均时间"""
        metrics = self.get_metrics_by_name(name)
        if not metrics:
            return None
        return sum(m.value for m in metrics) / len(metrics)

    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        if self._process is None:
            return {'mb': 0, 'percent': 0}
        try:
            mem_info = self._process.memory_info()
            return {
                'mb': mem_info.rss / 1024 / 1024,
                'percent': self._process.memory_percent()
            }
        except:
            return {'mb': 0, 'percent': 0}

    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        with self._lock:
            # 按名称分组计算统计
            stats = {}
            for metric in self._metrics:
                if metric.name not in stats:
                    stats[metric.name] = {
                        'count': 0,
                        'total': 0,
                        'min': float('inf'),
                        'max': 0
                    }
                stats[metric.name]['count'] += 1
                stats[metric.name]['total'] += metric.value
                stats[metric.name]['min'] = min(stats[metric.name]['min'], metric.value)
                stats[metric.name]['max'] = max(stats[metric.name]['max'], metric.value)

            # 计算平均值
            for name in stats:
                if stats[name]['count'] > 0:
                    stats[name]['avg'] = stats[name]['total'] / stats[name]['count']

            return {
                'counters': self._counters.copy(),
                'metrics': stats,
                'memory': self.get_memory_usage()
            }

    def clear(self):
        """清空所有指标"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._timers.clear()


# 全局指标收集器实例
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# ==========================================
# 便捷函数
# ==========================================

def record_api_call(api_name: str, duration: float, success: bool = True):
    """记录API调用"""
    collector = get_metrics_collector()
    collector.increment(f'api.{api_name}.total')
    if success:
        collector.increment(f'api.{api_name}.success')
    collector.record_time(f'api.{api_name}.duration', duration)


def record_cache_operation(cache_name: str, hit: bool):
    """记录缓存操作"""
    collector = get_metrics_collector()
    collector.increment(f'cache.{cache_name}.total')
    if hit:
        collector.increment(f'cache.{cache_name}.hit')
    else:
        collector.increment(f'cache.{cache_name}.miss')


def get_cache_hit_rate(cache_name: str) -> float:
    """获取缓存命中率"""
    collector = get_metrics_collector()
    total = collector.get_counter(f'cache.{cache_name}.total')
    hits = collector.get_counter(f'cache.{cache_name}.hit')
    if total == 0:
        return 0.0
    return hits / total * 100


def record_filter_performance(filter_name: str, duration: float, result_count: int):
    """记录筛选性能"""
    collector = get_metrics_collector()
    collector.record_time(f'filter.{filter_name}.duration', duration)
    collector.increment(f'filter.{filter_name}.results', result_count)


def get_metrics_summary() -> Dict[str, Any]:
    """获取指标摘要"""
    return get_metrics_collector().get_summary()


def clear_metrics():
    """清空指标"""
    get_metrics_collector().clear()


if __name__ == '__main__':
    # 测试代码
    collector = get_metrics_collector()

    # 测试计时器
    collector.start_timer('test_operation')
    time.sleep(0.1)
    collector.stop_timer('test_operation')

    # 测试计数器
    collector.increment('test_counter', 5)
    collector.increment('test_counter', 3)

    # 测试缓存记录
    record_cache_operation('stock_list', hit=True)
    record_cache_operation('stock_list', hit=True)
    record_cache_operation('stock_list', hit=False)

    # 打印摘要
    summary = get_metrics_summary()
    print("=== Metrics Summary ===")
    print(json.dumps(summary, indent=2, default=str))
