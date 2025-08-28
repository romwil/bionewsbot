"""Metrics collection for monitoring with Prometheus."""

from typing import Dict, Optional, Any
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
import structlog
from functools import wraps
import time
import asyncio


logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and exposes metrics for Prometheus monitoring."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        
        # Define metrics
        self._define_metrics()
    
    def _define_metrics(self):
        """Define all Prometheus metrics."""
        # Notification metrics
        self.notifications_sent = Counter(
            'bionewsbot_notifications_sent_total',
            'Total number of notifications sent',
            ['channel', 'type', 'priority'],
            registry=self.registry
        )
        
        self.notifications_failed = Counter(
            'bionewsbot_notifications_failed_total',
            'Total number of failed notifications',
            ['channel', 'error', 'type'],
            registry=self.registry
        )
        
        self.notification_send_duration = Histogram(
            'bionewsbot_notification_send_duration_seconds',
            'Time taken to send notifications',
            ['channel', 'type'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        # User interaction metrics
        self.user_actions = Counter(
            'bionewsbot_user_actions_total',
            'Total number of user actions',
            ['action', 'user_id'],
            registry=self.registry
        )
        
        self.notifications_read = Counter(
            'bionewsbot_notifications_read_total',
            'Total number of notifications marked as read',
            ['channel'],
            registry=self.registry
        )
        
        self.notifications_acknowledged = Counter(
            'bionewsbot_notifications_acknowledged_total',
            'Total number of notifications acknowledged',
            ['channel', 'user_id'],
            registry=self.registry
        )
        
        # Rate limiting metrics
        self.rate_limit_hits = Counter(
            'bionewsbot_rate_limit_hits_total',
            'Total number of rate limit hits',
            ['channel'],
            registry=self.registry
        )
        
        self.rate_limit_tokens = Gauge(
            'bionewsbot_rate_limit_tokens_remaining',
            'Remaining rate limit tokens',
            ['channel'],
            registry=self.registry
        )
        
        # API metrics
        self.api_requests = Counter(
            'bionewsbot_api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'bionewsbot_api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        # Insight processing metrics
        self.insights_processed = Counter(
            'bionewsbot_insights_processed_total',
            'Total number of insights processed',
            ['type', 'priority'],
            registry=self.registry
        )
        
        self.insight_processing_duration = Summary(
            'bionewsbot_insight_processing_duration_seconds',
            'Time taken to process insights',
            ['type'],
            registry=self.registry
        )
        
        # System health metrics
        self.slack_connection_status = Gauge(
            'bionewsbot_slack_connection_status',
            'Slack connection status (1=connected, 0=disconnected)',
            registry=self.registry
        )
        
        self.redis_connection_status = Gauge(
            'bionewsbot_redis_connection_status',
            'Redis connection status (1=connected, 0=disconnected)',
            registry=self.registry
        )
        
        self.active_notifications = Gauge(
            'bionewsbot_active_notifications',
            'Number of notifications currently being processed',
            registry=self.registry
        )
        
        # Queue metrics
        self.notification_queue_size = Gauge(
            'bionewsbot_notification_queue_size',
            'Current size of notification queue',
            ['priority'],
            registry=self.registry
        )
        
        self.notification_queue_wait_time = Histogram(
            'bionewsbot_notification_queue_wait_seconds',
            'Time notifications spend in queue',
            ['priority'],
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
            registry=self.registry
        )
    
    def increment(self, metric_name: str, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        try:
            metric = getattr(self, metric_name.replace('.', '_'))
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)
        except AttributeError:
            logger.warning(f"Metric {metric_name} not found")
        except Exception as e:
            logger.error(f"Error incrementing metric {metric_name}: {e}")
    
    def observe(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value for histogram/summary metrics."""
        try:
            metric = getattr(self, metric_name.replace('.', '_'))
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
        except AttributeError:
            logger.warning(f"Metric {metric_name} not found")
        except Exception as e:
            logger.error(f"Error observing metric {metric_name}: {e}")
    
    def set(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        try:
            metric = getattr(self, metric_name.replace('.', '_'))
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)
        except AttributeError:
            logger.warning(f"Metric {metric_name} not found")
        except Exception as e:
            logger.error(f"Error setting metric {metric_name}: {e}")
    
    def time(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        return TimingContext(self, metric_name, labels)
    
    def track_async(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Decorator for tracking async function execution time."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.observe(metric_name, duration, labels)
            return wrapper
        return decorator
    
    def track_sync(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Decorator for tracking sync function execution time."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.observe(metric_name, duration, labels)
            return wrapper
        return decorator
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry)
    
    async def update_health_metrics(self, slack_connected: bool, redis_connected: bool):
        """Update system health metrics."""
        self.set('slack_connection_status', 1 if slack_connected else 0)
        self.set('redis_connection_status', 1 if redis_connected else 0)


class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, metrics: MetricsCollector, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metrics = metrics
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.observe(self.metric_name, duration, self.labels)


# Global metrics instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# Convenience functions
def increment_metric(name: str, value: float = 1, **labels):
    """Increment a metric."""
    get_metrics_collector().increment(name, value, labels)


def observe_metric(name: str, value: float, **labels):
    """Observe a metric value."""
    get_metrics_collector().observe(name, value, labels)


def set_metric(name: str, value: float, **labels):
    """Set a gauge metric."""
    get_metrics_collector().set(name, value, labels)
