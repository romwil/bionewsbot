"""Webhook endpoints for receiving notifications from backend."""

from typing import Optional, Dict, Any
from datetime import datetime
import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks
import structlog

from ..config.settings import get_settings
from ..models.notification import Insight, NotificationRequest, Priority
from ..services.notification_manager import get_notification_manager
from ..utils.metrics import get_metrics_collector


logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature using HMAC."""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, f"sha256={expected_signature}")


@router.post("/insights")
async def receive_insight_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: Optional[str] = Header(None)
):
    """Receive new insight webhook from backend."""
    settings = get_settings()
    metrics = get_metrics_collector()
    
    # Get request body
    body = await request.body()
    
    # Verify signature if configured
    if settings.api.webhook_secret:
        if not x_webhook_signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        
        if not verify_webhook_signature(body, x_webhook_signature, settings.api.webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Parse request
    try:
        data = await request.json()
    except Exception as e:
        logger.error("Invalid webhook payload", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Validate insight data
    try:
        insight = Insight(**data.get("insight", {}))
    except Exception as e:
        logger.error("Invalid insight data", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid insight data")
    
    # Create notification request
    notification_request = NotificationRequest(
        insight=insight,
        channels=data.get("channels"),
        thread_ts=data.get("thread_ts")
    )
    
    # Process notification in background
    background_tasks.add_task(
        process_webhook_notification,
        notification_request
    )
    
    # Update metrics
    metrics.increment(
        "api_requests",
        labels={
            "method": "POST",
            "endpoint": "/webhooks/insights",
            "status": "200"
        }
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "insight_id": insight.id,
            "message": "Notification queued for processing"
        }
    )


async def process_webhook_notification(request: NotificationRequest):
    """Process webhook notification in background."""
    try:
        manager = await get_notification_manager()
        await manager.send_notification(request)
        
        logger.info(
            "Webhook notification processed",
            insight_id=request.insight.id
        )
        
    except Exception as e:
        logger.error(
            "Failed to process webhook notification",
            insight_id=request.insight.id,
            error=str(e)
        )


@router.post("/slack/interactions")
async def handle_slack_interaction(
    request: Request,
    x_slack_signature: Optional[str] = Header(None),
    x_slack_request_timestamp: Optional[str] = Header(None)
):
    """Handle Slack interactive components (buttons, menus, etc)."""
    settings = get_settings()
    
    # Verify Slack signature
    if not x_slack_signature or not x_slack_request_timestamp:
        raise HTTPException(status_code=401, detail="Missing Slack headers")
    
    body = await request.body()
    
    # Verify signature
    base_string = f"v0:{x_slack_request_timestamp}:{body.decode()}"
    expected_signature = "v0=" + hmac.new(
        settings.slack.signing_secret.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(x_slack_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")
    
    # Parse payload
    try:
        form_data = await request.form()
        payload = form_data.get("payload")
        if payload:
            data = json.loads(payload)
        else:
            data = await request.json()
    except Exception as e:
        logger.error("Invalid Slack payload", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    # Process interaction
    # Note: This is handled by the Slack Bolt app in the service
    # This endpoint is here for completeness and custom handling if needed
    
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    manager = await get_notification_manager()
    
    # Check service health
    slack_connected = manager.slack_service is not None
    redis_connected = False
    
    if manager.slack_service and manager.slack_service.redis_client:
        try:
            await manager.slack_service.redis_client.ping()
            redis_connected = True
        except:
            pass
    
    health_status = {
        "status": "healthy" if slack_connected and redis_connected else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "slack": "connected" if slack_connected else "disconnected",
            "redis": "connected" if redis_connected else "disconnected"
        }
    }
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    metrics = get_metrics_collector()
    
    return Response(
        content=metrics.get_metrics(),
        media_type="text/plain; version=0.0.4"
    )
