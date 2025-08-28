"""Prometheus metrics for BioNewsBot Scheduler monitoring."""
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
from typing import Dict, Any, Optional
import time
import structlog
from datetime import datetime, timedelta


logger = structlog.get_logger(__name__)


class SchedulerMetrics:
    """Metrics collection for scheduler service."""

    def __init__(self, prefix: str = "bionewsbot_scheduler"):
        self.prefix = prefix
        self.registry = CollectorRegistry()

        # Task metrics
        self.task_counter = Counter(
            f"{prefix}_tasks_total",
            "Total number of tasks executed",
            ["task_name", "status"],
            registry=self.registry
        )

        self.task_duration = Histogram(
            f"{prefix}_task_duration_seconds",
            "Task execution duration in seconds",
            ["task_name"],
            buckets=(0.1, 0.5, 1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600),
            registry=self.registry
        )

        self.task_retries = Counter(
            f"{prefix}_task_retries_total",
            "Total number of task retries",
            ["task_name"],
            registry=self.registry
        )

        # Queue metrics
        self.queue_size = Gauge(
            f"{prefix}_queue_size",
            "Current queue size",
            ["queue_name"],
            registry=self.registry
        )

        self.queue_latency = Histogram(
            f"{prefix}_queue_latency_seconds",
            "Time spent in queue before processing",
            ["queue_name"],
            buckets=(0.1, 0.5, 1, 5, 10, 30, 60, 120, 300, 600),
            registry=self.registry
        )

        # Worker metrics
        self.active_workers = Gauge(
            f"{prefix}_active_workers",
            "Number of active workers",
            registry=self.registry
        )

        self.worker_memory_usage = Gauge(
            f"{prefix}_worker_memory_mb",
            "Worker memory usage in MB",
            ["worker_id"],
            registry=self.registry
        )

        self.worker_cpu_usage = Gauge(
            f"{prefix}_worker_cpu_percent",
            "Worker CPU usage percentage",
            ["worker_id"],
            registry=self.registry
        )

        # Job metrics
        self.scheduled_jobs = Gauge(
            f"{prefix}_scheduled_jobs",
            "Number of scheduled jobs",
            ["job_type"],
            registry=self.registry
        )

        self.job_executions = Counter(
            f"{prefix}_job_executions_total",
            "Total job executions",
            ["job_name", "status"],
            registry=self.registry
        )

        self.job_duration = Histogram(
            f"{prefix}_job_duration_seconds",
            "Job execution duration",
            ["job_name"],
            buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600, 7200),
            registry=self.registry
        )

        # Analysis metrics
        self.companies_analyzed = Counter(
            f"{prefix}_companies_analyzed_total",
            "Total companies analyzed",
            ["analysis_type"],
            registry=self.registry
        )

        self.analysis_errors = Counter(
            f"{prefix}_analysis_errors_total",
            "Total analysis errors",
            ["company", "error_type"],
            registry=self.registry
        )

        self.insights_generated = Counter(
            f"{prefix}_insights_generated_total",
            "Total insights generated",
            ["company", "insight_type"],
            registry=self.registry
        )

        # System metrics
        self.last_heartbeat = Gauge(
            f"{prefix}_last_heartbeat_timestamp",
            "Last heartbeat timestamp",
            registry=self.registry
        )

        self.system_info = Info(
            f"{prefix}_system",
            "System information",
            registry=self.registry
        )

        # Dead letter queue metrics
        self.dead_letter_messages = Counter(
            f"{prefix}_dead_letter_messages_total",
            "Total messages sent to dead letter queue",
            ["original_queue", "reason"],
            registry=self.registry
        )

        # Performance metrics
        self.api_response_time = Histogram(
            f"{prefix}_api_response_seconds",
            "API response time in seconds",
            ["endpoint", "method"],
            buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10),
            registry=self.registry
        )

        # Initialize system info
        self.system_info.info({
            "version": "1.0.0",
            "environment": "production"
        })

        # Track metric history for alerting
        self._metric_history: Dict[str, list] = {}
        self._alert_thresholds: Dict[str, float] = {
            "task_failure_rate": 0.1,  # 10% failure rate
            "queue_size_max": 1000,
            "job_duration_max": 3600,  # 1 hour
            "worker_memory_max": 1024,  # 1GB
            "api_response_max": 10,  # 10 seconds
        }

    def task_success(self, task_name: str):
        """Record successful task execution."""
        self.task_counter.labels(task_name=task_name, status="success").inc()

    def task_failure(self, task_name: str):
        """Record failed task execution."""
        self.task_counter.labels(task_name=task_name, status="failure").inc()

    def task_retry(self, task_name: str):
        """Record task retry."""
        self.task_retries.labels(task_name=task_name).inc()

    def record_task_duration(self, task_name: str, duration: float):
        """Record task execution duration."""
        self.task_duration.labels(task_name=task_name).observe(duration)

    def update_queue_size(self, queue_name: str, size: int):
        """Update queue size metric."""
        self.queue_size.labels(queue_name=queue_name).set(size)

    def record_queue_latency(self, queue_name: str, latency: float):
        """Record time spent in queue."""
        self.queue_latency.labels(queue_name=queue_name).observe(latency)

    def worker_started(self):
        """Increment active workers count."""
        self.active_workers.inc()

    def worker_stopped(self):
        """Decrement active workers count."""
        self.active_workers.dec()

    def update_worker_resources(self, worker_id: str, memory_mb: float, cpu_percent: float):
        """Update worker resource usage."""
        self.worker_memory_usage.labels(worker_id=worker_id).set(memory_mb)
        self.worker_cpu_usage.labels(worker_id=worker_id).set(cpu_percent)

    def job_executed(self, job_name: str, status: str, duration: float):
        """Record job execution."""
        self.job_executions.labels(job_name=job_name, status=status).inc()
        self.job_duration.labels(job_name=job_name).observe(duration)

    def company_analyzed(self, analysis_type: str):
        """Record company analysis."""
        self.companies_analyzed.labels(analysis_type=analysis_type).inc()

    def analysis_error(self, company: str, error_type: str):
        """Record analysis error."""
        self.analysis_errors.labels(company=company, error_type=error_type).inc()

    def insight_generated(self, company: str, insight_type: str):
        """Record generated insight."""
        self.insights_generated.labels(company=company, insight_type=insight_type).inc()

    def record_api_response(self, endpoint: str, method: str, duration: float):
        """Record API response time."""
        self.api_response_time.labels(endpoint=endpoint, method=method).observe(duration)

    def dead_letter_message(self, original_queue: str, reason: str):
        """Record message sent to dead letter queue."""
        self.dead_letter_messages.labels(
            original_queue=original_queue,
            reason=reason
        ).inc()

    def heartbeat(self):
        """Update heartbeat timestamp."""
        self.last_heartbeat.set(time.time())

    def get_metrics(self) -> bytes:
        """Generate Prometheus metrics."""
        return generate_latest(self.registry)

    def check_alerts(self) -> Dict[str, Any]:
        """Check metrics against alert thresholds."""
        alerts = {}

        # Check task failure rate
        # This would need to query the actual metrics
        # For now, returning empty dict

        return alerts

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        current_time = time.time()
        last_heartbeat = self.last_heartbeat._value.get()

        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "heartbeat": {
                    "status": "healthy" if current_time - last_heartbeat < 120 else "unhealthy",
                    "last_heartbeat": datetime.fromtimestamp(last_heartbeat).isoformat()
                },
                "workers": {
                    "status": "healthy" if self.active_workers._value.get() > 0 else "unhealthy",
                    "active_count": self.active_workers._value.get()
                }
            }
        }

        # Set overall status
        if any(check["status"] == "unhealthy" for check in health["checks"].values()):
            health["status"] = "unhealthy"

        return health


# Global metrics instance
metrics = SchedulerMetrics()
