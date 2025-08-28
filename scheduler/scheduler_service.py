#!/usr/bin/env python3
"""Main scheduler service for BioNewsBot."""
import os
import sys
import signal
import time
from datetime import datetime
import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from config.config import config
from monitoring.metrics import metrics
from monitoring.health import health_server
from celery_app import app as celery_app

# Import tasks
from tasks.analysis import (
    daily_company_analysis,
    hourly_quick_scan
)
from tasks.reports import weekly_comprehensive_report
from tasks.cleanup import (
    cleanup_old_analysis_data,
    cleanup_temporary_files,
    optimize_database,
    archive_reports
)


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


class BioNewsBotScheduler:
    """Main scheduler service class."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = None
        self.running = False
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("shutdown_signal_received", signal=signum)
        self.stop()
        
    def initialize_scheduler(self):
        """Initialize APScheduler with Redis job store."""
        logger.info("initializing_scheduler")
        
        # Configure job stores
        jobstores = {
            'default': RedisJobStore(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.scheduler_db,
                password=config.redis.password
            )
        }
        
        # Configure executors
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }
        
        # Configure job defaults
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        # Create scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self.job_executed,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self.job_error,
            EVENT_JOB_ERROR
        )
        
        logger.info("scheduler_initialized")
        
    def job_executed(self, event):
        """Handle job execution events."""
        logger.info(
            "job_executed",
            job_id=event.job_id,
            scheduled_run_time=event.scheduled_run_time,
            retval=str(event.retval)[:100]  # Truncate for logging
        )
        metrics.job_executed(event.job_id, "success", 0)
        
    def job_error(self, event):
        """Handle job error events."""
        logger.error(
            "job_error",
            job_id=event.job_id,
            scheduled_run_time=event.scheduled_run_time,
            exception=str(event.exception),
            traceback=event.traceback
        )
        metrics.job_executed(event.job_id, "error", 0)
        
    def schedule_jobs(self):
        """Schedule all recurring jobs."""
        logger.info("scheduling_jobs")
        
        # Daily company analysis
        self.scheduler.add_job(
            self.run_daily_analysis,
            'cron',
            hour=config.schedules.daily_analysis_hour,
            minute=0,
            id='daily_company_analysis',
            name='Daily Company Analysis',
            replace_existing=True
        )
        
        # Hourly quick scan
        self.scheduler.add_job(
            self.run_hourly_scan,
            'cron',
            minute=0,
            id='hourly_quick_scan',
            name='Hourly Quick Scan',
            replace_existing=True
        )
        
        # Weekly comprehensive report
        self.scheduler.add_job(
            self.run_weekly_report,
            'cron',
            day_of_week=config.schedules.weekly_report_day,
            hour=config.schedules.weekly_report_hour,
            minute=0,
            id='weekly_comprehensive_report',
            name='Weekly Comprehensive Report',
            replace_existing=True
        )
        
        # Daily cleanup
        self.scheduler.add_job(
            self.run_cleanup,
            'cron',
            hour=3,  # 3 AM UTC
            minute=0,
            id='daily_cleanup',
            name='Daily Cleanup',
            replace_existing=True
        )
        
        # Weekly database optimization
        self.scheduler.add_job(
            self.run_optimization,
            'cron',
            day_of_week='sun',
            hour=2,
            minute=0,
            id='weekly_optimization',
            name='Weekly Database Optimization',
            replace_existing=True
        )
        
        # Monthly report archival
        self.scheduler.add_job(
            self.run_archival,
            'cron',
            day=1,  # First day of month
            hour=1,
            minute=0,
            id='monthly_archival',
            name='Monthly Report Archival',
            replace_existing=True
        )
        
        # Log scheduled jobs
        jobs = self.scheduler.get_jobs()
        logger.info(
            "jobs_scheduled",
            count=len(jobs),
            jobs=[{"id": job.id, "name": job.name, "next_run": job.next_run_time} for job in jobs]
        )
        
    def run_daily_analysis(self):
        """Trigger daily company analysis."""
        logger.info("triggering_daily_analysis")
        try:
            result = daily_company_analysis.delay()
            logger.info("daily_analysis_triggered", task_id=result.id)
        except Exception as e:
            logger.error("daily_analysis_trigger_error", error=str(e))
            raise
            
    def run_hourly_scan(self):
        """Trigger hourly quick scan."""
        logger.info("triggering_hourly_scan")
        try:
            result = hourly_quick_scan.delay(priority_only=True)
            logger.info("hourly_scan_triggered", task_id=result.id)
        except Exception as e:
            logger.error("hourly_scan_trigger_error", error=str(e))
            raise
            
    def run_weekly_report(self):
        """Trigger weekly comprehensive report."""
        logger.info("triggering_weekly_report")
        try:
            result = weekly_comprehensive_report.delay()
            logger.info("weekly_report_triggered", task_id=result.id)
        except Exception as e:
            logger.error("weekly_report_trigger_error", error=str(e))
            raise
            
    def run_cleanup(self):
        """Trigger cleanup tasks."""
        logger.info("triggering_cleanup")
        try:
            # Run cleanup tasks
            cleanup_old_analysis_data.delay(days_to_keep=90)
            cleanup_temporary_files.delay(hours_old=24)
            logger.info("cleanup_triggered")
        except Exception as e:
            logger.error("cleanup_trigger_error", error=str(e))
            raise
            
    def run_optimization(self):
        """Trigger database optimization."""
        logger.info("triggering_optimization")
        try:
            result = optimize_database.delay()
            logger.info("optimization_triggered", task_id=result.id)
        except Exception as e:
            logger.error("optimization_trigger_error", error=str(e))
            raise
            
    def run_archival(self):
        """Trigger report archival."""
        logger.info("triggering_archival")
        try:
            result = archive_reports.delay(days_to_keep=30)
            logger.info("archival_triggered", task_id=result.id)
        except Exception as e:
            logger.error("archival_trigger_error", error=str(e))
            raise
            
    def start(self):
        """Start the scheduler service."""
        logger.info("starting_scheduler_service")
        
        try:
            # Initialize scheduler
            self.initialize_scheduler()
            
            # Schedule jobs
            self.schedule_jobs()
            
            # Start scheduler
            self.scheduler.start()
            self.running = True
            
            # Start health check server
            health_server.start()
            
            # Start metrics server
            metrics.start_http_server()
            
            logger.info(
                "scheduler_service_started",
                jobs_count=len(self.scheduler.get_jobs())
            )
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logger.error("scheduler_start_error", error=str(e))
            self.stop()
            raise
            
    def stop(self):
        """Stop the scheduler service."""
        logger.info("stopping_scheduler_service")
        
        self.running = False
        
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            
        # Stop health check server
        health_server.stop()
        
        logger.info("scheduler_service_stopped")
        

def main():
    """Main entry point."""
    logger.info(
        "bionewsbot_scheduler_starting",
        version=config.version,
        environment=config.environment
    )
    
    # Create and start scheduler
    scheduler = BioNewsBotScheduler()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    except Exception as e:
        logger.error("scheduler_error", error=str(e))
        sys.exit(1)
    finally:
        scheduler.stop()
        

if __name__ == "__main__":
    main()
