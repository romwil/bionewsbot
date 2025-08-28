"""Configuration module for BioNewsBot Scheduler Service."""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import timedelta
import json


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    @property
    def url(self) -> str:
        """Get Redis URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class CeleryConfig:
    """Celery configuration."""
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list = field(default_factory=lambda: ["json"])
    timezone: str = "UTC"
    enable_utc: bool = True
    task_track_started: bool = True
    task_time_limit: int = 3600  # 1 hour
    task_soft_time_limit: int = 3300  # 55 minutes
    worker_prefetch_multiplier: int = 1
    worker_max_tasks_per_child: int = 1000
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True

    # Retry configuration
    task_default_retry_delay: int = 60  # 1 minute
    task_max_retries: int = 3

    # Queue configuration
    task_default_queue: str = "default"
    task_routes: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "scheduler.tasks.analysis.*": {"queue": "analysis"},
        "scheduler.tasks.reports.*": {"queue": "reports"},
        "scheduler.tasks.cleanup.*": {"queue": "maintenance"},
    })

    # Priority queue settings
    task_inherit_parent_priority: bool = True
    task_default_priority: int = 5
    task_queue_max_priority: int = 10

    # Dead letter queue
    task_dead_letter_queue: str = "dead_letter"
    task_dead_letter_exchange: str = "dead_letter"
    task_dead_letter_routing_key: str = "dead_letter"


@dataclass
class APIConfig:
    """Backend API configuration."""
    base_url: str = "http://localhost:8000"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1

    @property
    def analysis_endpoint(self) -> str:
        return f"{self.base_url}/api/v1/analysis"

    @property
    def companies_endpoint(self) -> str:
        return f"{self.base_url}/api/v1/companies"

    @property
    def insights_endpoint(self) -> str:
        return f"{self.base_url}/api/v1/insights"


@dataclass
class ScheduleConfig:
    """Scheduling configuration."""
    # Daily analysis schedule (cron format)
    daily_analysis_cron: str = "0 2 * * *"  # 2 AM daily
    daily_analysis_enabled: bool = True

    # Hourly quick scan schedule
    hourly_scan_cron: str = "0 * * * *"  # Every hour
    hourly_scan_enabled: bool = True

    # Weekly comprehensive report
    weekly_report_cron: str = "0 9 * * 1"  # Monday 9 AM
    weekly_report_enabled: bool = True

    # Cleanup old data
    cleanup_cron: str = "0 3 * * *"  # 3 AM daily
    cleanup_enabled: bool = True
    cleanup_retention_days: int = 90

    # Dynamic schedule updates check interval
    schedule_refresh_interval: int = 300  # 5 minutes

    # Job configuration
    max_instances: int = 3  # Max concurrent instances of same job
    misfire_grace_time: int = 300  # 5 minutes
    coalesce: bool = True  # Coalesce missed jobs


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    prometheus_port: int = 9090
    health_check_interval: int = 60  # 1 minute
    metrics_prefix: str = "bionewsbot_scheduler"

    # Alert thresholds
    job_failure_threshold: int = 3
    job_duration_threshold: int = 3600  # 1 hour
    queue_size_threshold: int = 1000


@dataclass
class Config:
    """Main configuration class."""
    # Environment
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Sub-configurations
    redis: RedisConfig = field(default_factory=RedisConfig)
    celery: CeleryConfig = field(default_factory=CeleryConfig)
    api: APIConfig = field(default_factory=APIConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Company configuration
    companies_config_file: str = "companies.json"
    priority_companies: list = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

        # Redis configuration
        config.redis.host = os.getenv("REDIS_HOST", config.redis.host)
        config.redis.port = int(os.getenv("REDIS_PORT", str(config.redis.port)))
        config.redis.password = os.getenv("REDIS_PASSWORD")
        config.redis.db = int(os.getenv("REDIS_DB", str(config.redis.db)))

        # Update Celery URLs
        config.celery.broker_url = config.redis.url
        config.celery.result_backend = config.redis.url

        # API configuration
        config.api.base_url = os.getenv("API_BASE_URL", config.api.base_url)
        config.api.timeout = int(os.getenv("API_TIMEOUT", str(config.api.timeout)))

        # Schedule configuration
        config.schedule.daily_analysis_cron = os.getenv(
            "DAILY_ANALYSIS_CRON", config.schedule.daily_analysis_cron
        )
        config.schedule.daily_analysis_enabled = os.getenv(
            "DAILY_ANALYSIS_ENABLED", "true"
        ).lower() == "true"

        config.schedule.hourly_scan_cron = os.getenv(
            "HOURLY_SCAN_CRON", config.schedule.hourly_scan_cron
        )
        config.schedule.hourly_scan_enabled = os.getenv(
            "HOURLY_SCAN_ENABLED", "true"
        ).lower() == "true"

        config.schedule.weekly_report_cron = os.getenv(
            "WEEKLY_REPORT_CRON", config.schedule.weekly_report_cron
        )
        config.schedule.weekly_report_enabled = os.getenv(
            "WEEKLY_REPORT_ENABLED", "true"
        ).lower() == "true"

        config.schedule.cleanup_cron = os.getenv(
            "CLEANUP_CRON", config.schedule.cleanup_cron
        )
        config.schedule.cleanup_enabled = os.getenv(
            "CLEANUP_ENABLED", "true"
        ).lower() == "true"
        config.schedule.cleanup_retention_days = int(
            os.getenv("CLEANUP_RETENTION_DAYS", str(config.schedule.cleanup_retention_days))
        )

        # Monitoring configuration
        config.monitoring.prometheus_port = int(
            os.getenv("PROMETHEUS_PORT", str(config.monitoring.prometheus_port))
        )

        # Priority companies
        priority_companies_str = os.getenv("PRIORITY_COMPANIES", "")
        if priority_companies_str:
            config.priority_companies = [
                c.strip() for c in priority_companies_str.split(",") if c.strip()
            ]

        return config

    def load_companies(self) -> Dict[str, Any]:
        """Load companies configuration from file."""
        if os.path.exists(self.companies_config_file):
            with open(self.companies_config_file, "r") as f:
                return json.load(f)
        return {}


# Global configuration instance
config = Config.from_env()
