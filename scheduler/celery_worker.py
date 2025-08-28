#!/usr/bin/env python3
"""Celery worker for BioNewsBot task processing."""
import os
import sys
import signal
import structlog
from celery import Celery
from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun

from config.config import config
from monitoring.metrics import metrics
from celery_app import app

# Import all tasks to register them
from tasks.analysis import *
from tasks.reports import *
from tasks.cleanup import *


# Configure logging
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


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Handle worker ready signal."""
    logger.info(
        "worker_ready",
        hostname=sender.hostname,
        concurrency=sender.concurrency,
        queues=[q.name for q in sender.task_consumer.queues]
    )
    metrics.worker_started(sender.hostname)


@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """Handle worker shutdown signal."""
    logger.info("worker_shutdown", hostname=sender.hostname)
    metrics.worker_stopped(sender.hostname)


@task_prerun.connect
def on_task_prerun(sender, task_id, task, args, kwargs, **extra):
    """Handle task pre-run signal."""
    logger.info(
        "task_starting",
        task_id=task_id,
        task_name=task.name,
        args=args,
        kwargs=kwargs
    )
    metrics.task_started(task.name)


@task_postrun.connect
def on_task_postrun(sender, task_id, task, args, kwargs, retval, state, **extra):
    """Handle task post-run signal."""
    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=task.name,
        state=state,
        retval=str(retval)[:100]  # Truncate for logging
    )
    metrics.task_completed(task.name, state)


def main():
    """Main entry point for Celery worker."""
    logger.info(
        "starting_celery_worker",
        version=config.version,
        environment=config.environment
    )
    
    # Start metrics server on different port for workers
    metrics.start_http_server(port=9091)
    
    # Configure worker
    worker_args = [
        'worker',
        '--loglevel=info',
        f'--concurrency={config.celery.worker_concurrency}',
        '--pool=prefork',
        '--queues=default,high_priority,low_priority',
        '--max-tasks-per-child=100',
        '--time-limit=3600',  # 1 hour hard limit
        '--soft-time-limit=3300',  # 55 minutes soft limit
    ]
    
    # Add hostname if specified
    if os.environ.get('CELERY_HOSTNAME'):
        worker_args.append(f'--hostname={os.environ["CELERY_HOSTNAME"]}')
    
    # Start worker
    app.worker_main(argv=worker_args)


if __name__ == '__main__':
    main()
