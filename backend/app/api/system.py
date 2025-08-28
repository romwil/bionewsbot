"""System configuration and health check routes."""
from typing import Any, Dict
from datetime import datetime, timedelta
import os
import psutil
import platform

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.deps import get_current_active_user, get_current_admin_user
from ..core.config import settings
from ..core.logging import get_logger
from ..db.session import get_db
from ..models.user import User
from ..models.system_config import SystemConfig
from ..schemas.system import (
    SystemConfigResponse,
    SystemConfigUpdate,
    HealthCheckResponse,
    SystemMetricsResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)) -> Any:
    """Basic health check endpoint."""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"

    # Check OpenAI API key
    llm_status = "healthy" if settings.OPENAI_API_KEY else "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" and llm_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "services": {
            "database": db_status,
            "llm": llm_status
        }
    }


@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get system metrics and resource usage."""
    logger.info("Getting system metrics", user_id=current_user.id)

    # Get CPU and memory usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Get database metrics
    from ..models.company import Company
    from ..models.insight import Insight
    from ..models.analysis import AnalysisRun

    total_companies = db.query(Company).count()
    monitored_companies = db.query(Company).filter(
        Company.monitoring_enabled == True
    ).count()

    total_insights = db.query(Insight).count()
    recent_insights = db.query(Insight).filter(
        Insight.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()

    total_analyses = db.query(AnalysisRun).count()
    running_analyses = db.query(AnalysisRun).filter(
        AnalysisRun.status == "running"
    ).count()

    # Get uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.utcnow() - boot_time

    return {
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024 ** 3),
            "memory_total_gb": memory.total / (1024 ** 3),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024 ** 3),
            "disk_total_gb": disk.total / (1024 ** 3),
            "uptime_hours": uptime.total_seconds() / 3600,
            "python_version": platform.python_version(),
            "platform": platform.platform()
        },
        "application": {
            "total_companies": total_companies,
            "monitored_companies": monitored_companies,
            "total_insights": total_insights,
            "recent_insights_7d": recent_insights,
            "total_analyses": total_analyses,
            "running_analyses": running_analyses,
            "version": settings.VERSION
        }
    }


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get system configuration."""
    logger.info("Getting system config", user_id=current_user.id)

    # Get or create default config
    config = db.query(SystemConfig).filter(
        SystemConfig.key == "default"
    ).first()

    if not config:
        # Create default config
        config = SystemConfig(
            key="default",
            value={
                "analysis_schedule": "0 6 * * *",  # Daily at 6 AM
                "max_concurrent_analyses": 5,
                "insight_retention_days": 90,
                "high_priority_threshold": 0.8,
                "llm_model": "gpt-4",
                "llm_temperature": 0.7,
                "llm_max_tokens": 2000,
                "rate_limits": {
                    "api_calls_per_minute": 60,
                    "analysis_runs_per_hour": 10
                },
                "notifications": {
                    "email_enabled": False,
                    "slack_enabled": False,
                    "webhook_enabled": False
                }
            },
            description="Default system configuration"
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


@router.put("/config", response_model=SystemConfigResponse)
async def update_system_config(
    config_update: SystemConfigUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update system configuration."""
    logger.info("Updating system config", user_id=current_user.id)

    # Get existing config
    config = db.query(SystemConfig).filter(
        SystemConfig.key == "default"
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System configuration not found"
        )

    # Update config
    if config_update.value:
        # Merge with existing config
        current_value = config.value or {}
        current_value.update(config_update.value)
        config.value = current_value

    if config_update.description:
        config.description = config_update.description

    config.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(config)

    logger.info(
        "System config updated",
        user_id=current_user.id,
        updated_keys=list(config_update.value.keys()) if config_update.value else []
    )

    return config


@router.post("/maintenance/cleanup")
async def cleanup_old_data(
    days: int = 90,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Clean up old data from the system."""
    logger.info(
        "Starting data cleanup",
        user_id=current_user.id,
        days=days
    )

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Clean up old insights
    from ..models.insight import Insight

    old_insights = db.query(Insight).filter(
        Insight.created_at < cutoff_date,
        Insight.status.in_(["dismissed", "archived"])
    ).count()

    if old_insights > 0:
        db.query(Insight).filter(
            Insight.created_at < cutoff_date,
            Insight.status.in_(["dismissed", "archived"])
        ).delete()

    # Clean up old analysis runs
    from ..models.analysis import AnalysisRun, AnalysisResult

    old_runs = db.query(AnalysisRun).filter(
        AnalysisRun.created_at < cutoff_date,
        AnalysisRun.status.in_(["failed", "cancelled"])
    ).count()

    if old_runs > 0:
        # Delete associated results first
        old_run_ids = db.query(AnalysisRun.id).filter(
            AnalysisRun.created_at < cutoff_date,
            AnalysisRun.status.in_(["failed", "cancelled"])
        ).subquery()

        db.query(AnalysisResult).filter(
            AnalysisResult.analysis_run_id.in_(old_run_ids)
        ).delete(synchronize_session=False)

        # Then delete runs
        db.query(AnalysisRun).filter(
            AnalysisRun.created_at < cutoff_date,
            AnalysisRun.status.in_(["failed", "cancelled"])
        ).delete()

    db.commit()

    logger.info(
        "Data cleanup completed",
        user_id=current_user.id,
        old_insights_deleted=old_insights,
        old_runs_deleted=old_runs
    )

    return {
        "message": "Cleanup completed",
        "old_insights_deleted": old_insights,
        "old_runs_deleted": old_runs
    }


@router.get("/logs/recent")
async def get_recent_logs(
    lines: int = 100,
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Get recent application logs."""
    logger.info(
        "Getting recent logs",
        user_id=current_user.id,
        lines=lines
    )

    # In production, this would read from actual log files
    # For now, return a placeholder
    return {
        "message": "Log retrieval not implemented in development mode",
        "logs": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "This is a placeholder log entry"
            }
        ]
    }


@router.post("/test/llm")
async def test_llm_connection(
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Test LLM connection and configuration."""
    logger.info("Testing LLM connection", user_id=current_user.id)

    from ..services.llm_service import llm_service

    try:
        # Test with a simple prompt
        test_prompt = "Respond with 'OK' if you can read this."
        response = await llm_service._call_openai(
            messages=[{"role": "user", "content": test_prompt}],
            temperature=0.1,
            max_tokens=10
        )

        return {
            "status": "success",
            "message": "LLM connection successful",
            "response": response,
            "model": settings.OPENAI_MODEL
        }
    except Exception as e:
        logger.error("LLM connection test failed", error=str(e))
        return {
            "status": "error",
            "message": "LLM connection failed",
            "error": str(e)
        }
