"""Main FastAPI application for the notification service."""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config.settings import get_settings
from .api.webhooks import router as webhook_router
from .services.notification_manager import get_notification_manager
from .utils.metrics import get_metrics_collector


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting notification service")
    
    # Initialize services
    settings = get_settings()
    notification_manager = await get_notification_manager()
    
    # Start notification manager
    await notification_manager.start()
    
    logger.info(
        "Notification service started",
        environment=settings.environment,
        service_name=settings.service_name
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down notification service")
    
    # Stop services
    await notification_manager.stop()
    
    logger.info("Notification service stopped")


# Create FastAPI app
app = FastAPI(
    title="BioNewsBot Notification Service",
    description="Real-time Slack notifications for life sciences intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    metrics = get_metrics_collector()
    
    # Log request
    logger.info(
        "Incoming request",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None
    )
    
    # Process request
    response = await call_next(request)
    
    # Update metrics
    metrics.increment(
        "api_requests",
        labels={
            "method": request.method,
            "endpoint": request.url.path,
            "status": str(response.status_code)
        }
    )
    
    return response


# Include routers
app.include_router(webhook_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "BioNewsBot Notification Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/status")
async def get_status():
    """Get service status."""
    manager = await get_notification_manager()
    metrics = get_metrics_collector()
    
    status = {
        "service": "BioNewsBot Notification Service",
        "version": "1.0.0",
        "queues": {
            "high_priority": manager.high_priority_queue.qsize(),
            "normal_priority": manager.normal_priority_queue.qsize()
        },
        "connections": {
            "slack": manager.slack_service is not None,
            "database": True,  # TODO: Implement actual check
            "redis": True  # TODO: Implement actual check
        }
    }
    
    return status


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(
        "Unhandled exception",
        method=request.method,
        path=request.url.path,
        error=str(exc),
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Different port from main API
        reload=settings.environment == "development",
        log_level=settings.notification.log_level.lower()
    )
