"""Analysis tasks for BioNewsBot Scheduler."""
from celery import Task, group, chain
from celery.utils.log import get_task_logger
from typing import List, Dict, Any, Optional
import requests
import time
from datetime import datetime, timedelta
import json
from celery_app import app
from config.config import config
from monitoring.metrics import metrics
import structlog


logger = structlog.get_logger(__name__)
task_logger = get_task_logger(__name__)


class RetryableTask(Task):
    """Base task with exponential backoff retry."""
    autoretry_for = (requests.RequestException, ConnectionError, TimeoutError)
    retry_kwargs = {
        'max_retries': 3,
        'countdown': 60,  # Initial retry delay
    }
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True


@app.task(base=RetryableTask, bind=True, name='scheduler.tasks.analysis.daily_company_analysis')
def daily_company_analysis(self, company_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run daily analysis for all configured companies."""
    start_time = time.time()
    logger.info("starting_daily_analysis", company_ids=company_ids)

    try:
        # Get list of companies to analyze
        if not company_ids:
            companies = get_active_companies()
            company_ids = [c['id'] for c in companies]

        logger.info("analyzing_companies", count=len(company_ids))

        # Create subtasks for each company
        job = group(
            analyze_single_company.s(company_id, analysis_type="daily")
            for company_id in company_ids
        )

        # Execute all analyses in parallel
        result = job.apply_async()
        results = result.get(timeout=3600)  # 1 hour timeout

        # Aggregate results
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'error')

        duration = time.time() - start_time

        # Record metrics
        metrics.job_executed(
            "daily_company_analysis",
            "success" if failed == 0 else "partial",
            duration
        )

        summary = {
            "status": "success" if failed == 0 else "partial",
            "timestamp": datetime.utcnow().isoformat(),
            "companies_analyzed": successful,
            "companies_failed": failed,
            "duration_seconds": duration,
            "results": results
        }

        logger.info(
            "daily_analysis_complete",
            successful=successful,
            failed=failed,
            duration=duration
        )

        return summary

    except Exception as e:
        logger.error("daily_analysis_error", error=str(e))
        metrics.job_executed("daily_company_analysis", "error", time.time() - start_time)
        raise


@app.task(base=RetryableTask, bind=True, name='scheduler.tasks.analysis.hourly_quick_scan')
def hourly_quick_scan(self, priority_only: bool = True) -> Dict[str, Any]:
    """Run hourly quick scan for priority companies or recent events."""
    start_time = time.time()
    logger.info("starting_hourly_scan", priority_only=priority_only)

    try:
        # Get companies for quick scan
        if priority_only:
            company_ids = config.priority_companies
        else:
            # Get companies with recent activity
            company_ids = get_companies_with_recent_activity(hours=24)

        if not company_ids:
            logger.info("no_companies_for_quick_scan")
            return {
                "status": "success",
                "message": "No companies require quick scan",
                "timestamp": datetime.utcnow().isoformat()
            }

        logger.info("quick_scanning_companies", count=len(company_ids))

        # Create subtasks with higher priority
        job = group(
            analyze_single_company.s(
                company_id,
                analysis_type="quick_scan",
                priority=8
            )
            for company_id in company_ids
        )

        # Execute with shorter timeout
        result = job.apply_async(priority=8)
        results = result.get(timeout=1800)  # 30 minutes timeout

        # Check for significant findings
        significant_findings = [
            r for r in results
            if r.get('status') == 'success' and r.get('has_significant_updates', False)
        ]

        duration = time.time() - start_time

        # Record metrics
        metrics.job_executed(
            "hourly_quick_scan",
            "success",
            duration
        )

        summary = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "companies_scanned": len(company_ids),
            "significant_findings": len(significant_findings),
            "duration_seconds": duration,
            "findings": significant_findings
        }

        # Trigger alerts for significant findings
        if significant_findings:
            trigger_alerts.delay(significant_findings)

        logger.info(
            "hourly_scan_complete",
            scanned=len(company_ids),
            significant=len(significant_findings),
            duration=duration
        )

        return summary

    except Exception as e:
        logger.error("hourly_scan_error", error=str(e))
        metrics.job_executed("hourly_quick_scan", "error", time.time() - start_time)
        raise


@app.task(base=RetryableTask, bind=True, name='scheduler.tasks.analysis.analyze_single_company')
def analyze_single_company(
    self,
    company_id: str,
    analysis_type: str = "daily",
    priority: int = 5
) -> Dict[str, Any]:
    """Analyze a single company."""
    start_time = time.time()
    logger.info(
        "analyzing_company",
        company_id=company_id,
        analysis_type=analysis_type
    )

    try:
        # Call backend API to trigger analysis
        response = requests.post(
            f"{config.api.analysis_endpoint}/companies/{company_id}/analyze",
            json={
                "analysis_type": analysis_type,
                "priority": priority,
                "requested_by": "scheduler",
                "metadata": {
                    "task_id": self.request.id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            timeout=config.api.timeout
        )
        response.raise_for_status()

        analysis_result = response.json()

        # Wait for analysis to complete (with polling)
        analysis_id = analysis_result.get('analysis_id')
        if analysis_id:
            final_result = poll_analysis_status(analysis_id, timeout=600)
        else:
            final_result = analysis_result

        duration = time.time() - start_time

        # Record metrics
        metrics.company_analyzed(analysis_type)
        metrics.record_task_duration(
            f"analyze_company_{analysis_type}",
            duration
        )

        # Check for significant updates
        has_significant_updates = check_significant_updates(final_result)

        result = {
            "status": "success",
            "company_id": company_id,
            "analysis_type": analysis_type,
            "analysis_id": analysis_id,
            "has_significant_updates": has_significant_updates,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "insights": final_result.get('insights', []),
            "metrics": final_result.get('metrics', {})
        }

        # Generate insights if significant updates found
        if has_significant_updates:
            insights = generate_insights(company_id, final_result)
            for insight in insights:
                metrics.insight_generated(company_id, insight['type'])

        logger.info(
            "company_analysis_complete",
            company_id=company_id,
            duration=duration,
            significant=has_significant_updates
        )

        return result

    except requests.RequestException as e:
        logger.error(
            "company_analysis_api_error",
            company_id=company_id,
            error=str(e)
        )
        metrics.analysis_error(company_id, "api_error")
        raise
    except Exception as e:
        logger.error(
            "company_analysis_error",
            company_id=company_id,
            error=str(e)
        )
        metrics.analysis_error(company_id, "unknown_error")
        return {
            "status": "error",
            "company_id": company_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.task(name='scheduler.tasks.analysis.trigger_alerts')
def trigger_alerts(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Trigger alerts for significant findings."""
    logger.info("triggering_alerts", count=len(findings))

    try:
        # Group findings by severity
        critical = [f for f in findings if f.get('severity') == 'critical']
        high = [f for f in findings if f.get('severity') == 'high']
        medium = [f for f in findings if f.get('severity') == 'medium']

        alerts_sent = 0

        # Send alerts via API
        for finding in findings:
            response = requests.post(
                f"{config.api.base_url}/api/v1/alerts",
                json={
                    "company_id": finding['company_id'],
                    "type": "analysis_finding",
                    "severity": finding.get('severity', 'medium'),
                    "title": finding.get('title', 'New Finding'),
                    "description": finding.get('description', ''),
                    "data": finding,
                    "source": "scheduler"
                },
                timeout=10
            )
            if response.status_code == 201:
                alerts_sent += 1

        logger.info(
            "alerts_triggered",
            total=len(findings),
            sent=alerts_sent,
            critical=len(critical),
            high=len(high),
            medium=len(medium)
        )

        return {
            "status": "success",
            "alerts_sent": alerts_sent,
            "by_severity": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium)
            }
        }

    except Exception as e:
        logger.error("alert_trigger_error", error=str(e))
        return {"status": "error", "error": str(e)}


# Helper functions

def get_active_companies() -> List[Dict[str, Any]]:
    """Get list of active companies from API."""
    try:
        response = requests.get(
            f"{config.api.companies_endpoint}/active",
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("get_companies_error", error=str(e))
        # Fallback to config file
        companies_config = config.load_companies()
        return companies_config.get('companies', [])


def get_companies_with_recent_activity(hours: int = 24) -> List[str]:
    """Get companies with recent activity."""
    try:
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        response = requests.get(
            f"{config.api.companies_endpoint}/recent-activity",
            params={"since": since},
            timeout=30
        )
        response.raise_for_status()
        companies = response.json()
        return [c['id'] for c in companies]
    except Exception as e:
        logger.error("get_recent_activity_error", error=str(e))
        return []


def poll_analysis_status(analysis_id: str, timeout: int = 600) -> Dict[str, Any]:
    """Poll analysis status until complete or timeout."""
    start_time = time.time()
    poll_interval = 5  # seconds

    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{config.api.analysis_endpoint}/{analysis_id}/status",
                timeout=10
            )
            response.raise_for_status()
            status_data = response.json()

            if status_data['status'] in ['completed', 'failed']:
                return status_data

            time.sleep(poll_interval)

        except Exception as e:
            logger.warning("poll_status_error", error=str(e))
            time.sleep(poll_interval)

    raise TimeoutError(f"Analysis {analysis_id} timed out after {timeout} seconds")


def check_significant_updates(analysis_result: Dict[str, Any]) -> bool:
    """Check if analysis contains significant updates."""
    # Check various indicators of significance
    indicators = [
        analysis_result.get('has_breaking_news', False),
        analysis_result.get('sentiment_change', 0) > 0.3,
        len(analysis_result.get('new_partnerships', [])) > 0,
        len(analysis_result.get('regulatory_updates', [])) > 0,
        analysis_result.get('stock_movement', 0) > 5.0,
        analysis_result.get('risk_score_change', 0) > 0.2,
    ]

    return any(indicators)


def generate_insights(company_id: str, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate insights from analysis results."""
    insights = []

    try:
        # Post insights to API
        for insight_data in analysis_result.get('insights', []):
            response = requests.post(
                f"{config.api.insights_endpoint}",
                json={
                    "company_id": company_id,
                    "type": insight_data.get('type', 'general'),
                    "title": insight_data.get('title'),
                    "description": insight_data.get('description'),
                    "confidence": insight_data.get('confidence', 0.8),
                    "data": insight_data.get('data', {}),
                    "source": "scheduler_analysis"
                },
                timeout=10
            )
            if response.status_code == 201:
                insights.append(response.json())

    except Exception as e:
        logger.error("generate_insights_error", error=str(e))

    return insights
