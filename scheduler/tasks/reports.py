"""Report generation tasks for BioNewsBot Scheduler."""
from celery import Task
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
from io import BytesIO
import pandas as pd


logger = structlog.get_logger(__name__)
task_logger = get_task_logger(__name__)


@app.task(bind=True, name='scheduler.tasks.reports.weekly_comprehensive_report')
def weekly_comprehensive_report(self, company_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Generate weekly comprehensive report for all companies."""
    start_time = time.time()
    logger.info("starting_weekly_report_generation")
    
    try:
        # Get date range for the week
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Get companies to report on
        if not company_ids:
            companies = get_active_companies_for_reporting()
            company_ids = [c['id'] for c in companies]
        
        logger.info(
            "generating_weekly_report",
            companies=len(company_ids),
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Collect data for each company
        company_reports = []
        for company_id in company_ids:
            try:
                company_data = generate_company_report(
                    company_id,
                    start_date,
                    end_date
                )
                company_reports.append(company_data)
            except Exception as e:
                logger.error(
                    "company_report_error",
                    company_id=company_id,
                    error=str(e)
                )
        
        # Aggregate report data
        report_data = {
            "report_type": "weekly_comprehensive",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": generate_executive_summary(company_reports),
            "companies": company_reports,
            "insights_summary": aggregate_insights(company_reports),
            "risk_assessment": calculate_portfolio_risk(company_reports),
            "recommendations": generate_recommendations(company_reports)
        }
        
        # Generate formatted reports
        report_formats = generate_report_formats(report_data)
        
        # Save report via API
        response = requests.post(
            f"{config.api.base_url}/api/v1/reports",
            json={
                "type": "weekly_comprehensive",
                "data": report_data,
                "formats": report_formats,
                "metadata": {
                    "task_id": self.request.id,
                    "companies_count": len(company_reports),
                    "period_days": 7
                }
            },
            timeout=60
        )
        response.raise_for_status()
        
        report_id = response.json().get('id')
        
        # Send report notifications
        send_report_notifications.delay(report_id, "weekly_comprehensive")
        
        duration = time.time() - start_time
        
        # Record metrics
        metrics.job_executed(
            "weekly_comprehensive_report",
            "success",
            duration
        )
        
        logger.info(
            "weekly_report_complete",
            report_id=report_id,
            companies=len(company_reports),
            duration=duration
        )
        
        return {
            "status": "success",
            "report_id": report_id,
            "companies_reported": len(company_reports),
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("weekly_report_error", error=str(e))
        metrics.job_executed(
            "weekly_comprehensive_report",
            "error",
            time.time() - start_time
        )
        raise

def calculate_portfolio_risk(company_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate overall portfolio risk assessment."""
    risk_scores = [r.get('summary', {}).get('risk_score', 0) for r in company_reports]
    
    if not risk_scores:
        return {"overall_risk": "low", "score": 0}
    
    avg_risk = sum(risk_scores) / len(risk_scores)
    max_risk = max(risk_scores)
    high_risk_count = sum(1 for score in risk_scores if score > 0.7)
    
    # Determine overall risk level
    if max_risk > 0.8 or high_risk_count > len(risk_scores) * 0.3:
        risk_level = "high"
    elif avg_risk > 0.5:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "overall_risk": risk_level,
        "average_score": round(avg_risk, 2),
        "max_score": round(max_risk, 2),
        "high_risk_companies": high_risk_count,
        "risk_distribution": {
            "low": sum(1 for score in risk_scores if score <= 0.3),
            "medium": sum(1 for score in risk_scores if 0.3 < score <= 0.7),
            "high": sum(1 for score in risk_scores if score > 0.7)
        }
    }


def generate_recommendations(company_reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate portfolio-wide recommendations."""
    recommendations = []
    
    # Check for high-risk companies
    high_risk = [r for r in company_reports if r.get('summary', {}).get('risk_score', 0) > 0.7]
    if high_risk:
        recommendations.append({
            "priority": "high",
            "type": "risk_mitigation",
            "title": "Immediate Risk Assessment Required",
            "description": f"{len(high_risk)} companies showing elevated risk levels require immediate attention",
            "companies": [r['company_id'] for r in high_risk]
        })
    
    # Check for positive trends
    positive_trends = [r for r in company_reports if any(t.get('direction') == 'improving' for t in r.get('trends', []))]
    if positive_trends:
        recommendations.append({
            "priority": "medium",
            "type": "opportunity",
            "title": "Capitalize on Positive Momentum",
            "description": f"{len(positive_trends)} companies showing positive trends present growth opportunities",
            "companies": [r['company_id'] for r in positive_trends]
        })
    
    # Check for low activity
    low_activity = [r for r in company_reports if r.get('summary', {}).get('activity_level') == 'low']
    if low_activity:
        recommendations.append({
            "priority": "low",
            "type": "monitoring",
            "title": "Increase Monitoring Frequency",
            "description": f"{len(low_activity)} companies have low activity levels and may need increased monitoring",
            "companies": [r['company_id'] for r in low_activity]
        })
    
    return recommendations


def generate_company_recommendations(
    company_info: Dict[str, Any],
    metrics: Dict[str, Any],
    trends: List[Dict[str, Any]]
) -> List[str]:
    """Generate recommendations for a specific company."""
    recommendations = []
    
    # Risk-based recommendations
    if metrics.get('risk_score', 0) > 0.7:
        recommendations.append("Conduct immediate risk assessment and mitigation planning")
    elif metrics.get('risk_score', 0) > 0.5:
        recommendations.append("Monitor risk factors closely and prepare contingency plans")
    
    # Sentiment-based recommendations
    sentiment_trend = next((t for t in trends if t['type'] == 'sentiment'), None)
    if sentiment_trend:
        if sentiment_trend['direction'] == 'improving':
            recommendations.append("Leverage positive sentiment for strategic initiatives")
        elif sentiment_trend['direction'] == 'declining':
            recommendations.append("Investigate sentiment drivers and develop response strategy")
    
    # Activity-based recommendations
    if metrics.get('activity_level') == 'high':
        recommendations.append("Deep dive into high activity areas for strategic insights")
    elif metrics.get('activity_level') == 'low':
        recommendations.append("Increase monitoring frequency to capture emerging trends")
    
    return recommendations


def generate_report_formats(report_data: Dict[str, Any]) -> Dict[str, str]:
    """Generate report in multiple formats."""
    formats = {}
    
    # Generate HTML format
    html_content = generate_html_report(report_data)
    formats['html'] = html_content
    
    # Generate markdown format
    markdown_content = generate_markdown_report(report_data)
    formats['markdown'] = markdown_content
    
    # Generate JSON format (already have the data)
    formats['json'] = json.dumps(report_data, indent=2)
    
    return formats


def generate_html_report(report_data: Dict[str, Any]) -> str:
    """Generate HTML formatted report."""
    html = f"""
    <html>
    <head>
        <title>BioNewsBot Weekly Report - {report_data['generated_at']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
            .company {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
            .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e0e0e0; }}
        </style>
    </head>
    <body>
        <h1>BioNewsBot Weekly Comprehensive Report</h1>
        <div class="summary">
            <h2>Executive Summary</h2>
            <p>Period: {report_data['period']['start']} to {report_data['period']['end']}</p>
            <div class="metrics">
                <div class="metric">Companies Analyzed: {report_data['summary']['total_companies_analyzed']}</div>
                <div class="metric">Total Analyses: {report_data['summary']['total_analyses_performed']}</div>
                <div class="metric">Insights Generated: {report_data['summary']['total_insights_generated']}</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def generate_markdown_report(report_data: Dict[str, Any]) -> str:
    """Generate Markdown formatted report."""
    md = f"""
# BioNewsBot Weekly Comprehensive Report

Generated: {report_data['generated_at']}

## Executive Summary

**Period**: {report_data['period']['start']} to {report_data['period']['end']}

### Key Metrics
- Companies Analyzed: {report_data['summary']['total_companies_analyzed']}
- Total Analyses: {report_data['summary']['total_analyses_performed']}
- Insights Generated: {report_data['summary']['total_insights_generated']}
- Average Portfolio Sentiment: {report_data['summary']['average_portfolio_sentiment']}

### Risk Assessment
- Overall Risk Level: {report_data['risk_assessment']['overall_risk']}
- High Risk Companies: {report_data['risk_assessment']['high_risk_companies']}

## Recommendations
"""
    
    for rec in report_data['recommendations']:
        md += f"\n### {rec['title']} (Priority: {rec['priority']})\n"
        md += f"{rec['description']}\n"
    
    return md


def get_report_recipients(report_type: str) -> List[str]:
    """Get list of report recipients based on report type."""
    # This would typically fetch from a database or config
    # For now, return from config
    recipients = config.report_recipients.get(report_type, [])
    return recipients
