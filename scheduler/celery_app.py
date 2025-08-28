"""Celery application configuration for BioNewsBot Scheduler."""
from celery import Celery, Task
from celery.signals import worker_ready, worker_shutdown, task_failure, task_success, task_retry
from typing import Any, Dict
import structlog
from config.config import config
from monitoring.metrics import metrics


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class LoggingTask(Task):
    """Custom task class with enhanced logging and metrics."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful task execution."""
        logger.info(
            "task_success",
            task_name=self.name,
            task_id=task_id,
            args=args,
            kwargs=kwargs
        )
        metrics.task_success(self.name)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure."""
        logger.error(
            "task_failure",
            task_name=self.name,
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            exception=str(exc),
            traceback=str(einfo)
        )
        metrics.task_failure(self.name)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(
            "task_retry",
            task_name=self.name,
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            exception=str(exc),
            retry_count=self.request.retries
        )
        metrics.task_retry(self.name)


# Create Celery application
app = Celery("bionewsbot_scheduler")

# Configure Celery from config object
app.config_from_object(config.celery)

# Set custom task class
app.Task = LoggingTask

# Configure task routing
app.conf.task_routes = {
    "scheduler.tasks.analysis.daily_company_analysis": {"queue": "analysis", "priority": 5},
    "scheduler.tasks.analysis.hourly_quick_scan": {"queue": "analysis", "priority": 8},
    "scheduler.tasks.analysis.analyze_single_company": {"queue": "analysis", "priority": 6},
    "scheduler.tasks.reports.weekly_comprehensive_report": {"queue": "reports", "priority": 4},
    "scheduler.tasks.reports.generate_company_report": {"queue": "reports", "priority": 5},
    "scheduler.tasks.cleanup.cleanup_old_data": {"queue": "maintenance", "priority": 2},
    "scheduler.tasks.cleanup.vacuum_database": {"queue": "maintenance", "priority": 1},
}

# Configure queues with priorities
from kombu import Queue, Exchange

app.conf.task_queues = [
    Queue(
        "analysis",
        Exchange("analysis"),
        routing_key="analysis",
        queue_arguments={
            "x-max-priority": 10,
            "x-message-ttl": 86400000,  # 24 hours
        }
    ),
    Queue(
        "reports",
        Exchange("reports"),
        routing_key="reports",
        queue_arguments={
            "x-max-priority": 10,
            "x-message-ttl": 172800000,  # 48 hours
        }
    ),
    Queue(
        "maintenance",
        Exchange("maintenance"),
        routing_key="maintenance",
        queue_arguments={
            "x-max-priority": 10,
            "x-message-ttl": 43200000,  # 12 hours
        }
    ),
    Queue(
        "dead_letter",
        Exchange("dead_letter"),
        routing_key="dead_letter",
        queue_arguments={
            "x-message-ttl": 604800000,  # 7 days
        }
    ),
]

# Auto-discover tasks
app.autodiscover_tasks(["scheduler.tasks"])


# Signal handlers
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal."""
    logger.info("worker_ready", hostname=sender.hostname if sender else "unknown")
    metrics.worker_started()


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handle worker shutdown signal."""
    logger.info("worker_shutdown", hostname=sender.hostname if sender else "unknown")
    metrics.worker_stopped()


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Handle task success signal."""
    if sender:
        metrics.task_duration(
            sender.name,
            kwargs.get("runtime", 0)
        )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Handle task failure signal."""
    if sender:
        logger.error(
            "task_failed_signal",
            task_name=sender.name,
            task_id=task_id,
            exception=str(exception)
        )


@task_retry.connect
def task_retry_handler(sender=None, reason=None, **kwargs):
    """Handle task retry signal."""
    if sender:
        logger.warning(
            "task_retry_signal",
            task_name=sender.name,
            reason=str(reason),
            retry_count=kwargs.get("retries", 0)
        )


if __name__ == "__main__":
    app.start()
