def cleanup_old_logs(days_to_keep: int) -> int:
    """Clean up old log files."""
    log_dir = config.log_directory
    if not os.path.exists(log_dir):
        return 0
    
    cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
    cleaned = 0
    
    for file in os.listdir(log_dir):
        if file.endswith('.log'):
            file_path = os.path.join(log_dir, file)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mtime < cutoff_time:
                    os.remove(file_path)
                    cleaned += 1
            except Exception as e:
                logger.warning("log_cleanup_error", file=file, error=str(e))
    
    return cleaned


def cleanup_redis_keys() -> int:
    """Clean up expired Redis keys."""
    try:
        from celery_app import redis_client
        
        cleaned = 0
        patterns = [
            "celery-task-meta-*",
            "_kombu.binding.*",
            "unacked_mutex_*"
        ]
        
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            if keys:
                cleaned += redis_client.delete(*keys)
        
        return cleaned
    except Exception as e:
        logger.error("redis_cleanup_error", error=str(e))
        return 0


def analyze_database_tables() -> Dict[str, Any]:
    """Analyze database tables for optimization."""
    try:
        response = requests.post(
            f"{config.api.base_url}/api/v1/maintenance/analyze-tables",
            timeout=300
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("analyze_tables_error", error=str(e))
        return {"tables_count": 0, "status": "error"}


def update_database_statistics() -> Dict[str, Any]:
    """Update database statistics."""
    try:
        response = requests.post(
            f"{config.api.base_url}/api/v1/maintenance/update-statistics",
            timeout=300
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("update_stats_error", error=str(e))
        return {"updated": False, "status": "error"}


def rebuild_fragmented_indexes() -> Dict[str, Any]:
    """Rebuild fragmented database indexes."""
    try:
        response = requests.post(
            f"{config.api.base_url}/api/v1/maintenance/rebuild-indexes",
            json={"fragmentation_threshold": 30},  # 30% fragmentation
            timeout=600
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("rebuild_indexes_error", error=str(e))
        return {"rebuilt_count": 0, "status": "error"}


def vacuum_full_if_needed() -> Dict[str, Any]:
    """Perform VACUUM FULL if needed."""
    try:
        response = requests.post(
            f"{config.api.base_url}/api/v1/maintenance/vacuum-full",
            json={"bloat_threshold": 50},  # 50% bloat
            timeout=1800  # 30 minutes
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("vacuum_full_error", error=str(e))
        return {"performed": False, "status": "error"}


def get_reports_to_archive(cutoff_date: datetime) -> List[Dict[str, Any]]:
    """Get reports that need archiving."""
    try:
        response = requests.get(
            f"{config.api.base_url}/api/v1/reports/to-archive",
            params={"before": cutoff_date.isoformat()},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("get_reports_error", error=str(e))
        return []


def archive_report(report: Dict[str, Any]) -> str:
    """Archive a single report."""
    archive_dir = os.path.join(config.archive_location, "reports")
    os.makedirs(archive_dir, exist_ok=True)
    
    # Create archive filename
    date_str = report['created_at'][:10]  # YYYY-MM-DD
    archive_file = os.path.join(
        archive_dir,
        f"report_{report['id']}_{date_str}.json.gz"
    )
    
    # Compress and save
    import gzip
    import json
    
    with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return archive_file


def delete_report(report_id: str) -> bool:
    """Delete a report from main storage."""
    try:
        response = requests.delete(
            f"{config.api.base_url}/api/v1/reports/{report_id}",
            timeout=30
        )
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error("delete_report_error", report_id=report_id, error=str(e))
        return False
