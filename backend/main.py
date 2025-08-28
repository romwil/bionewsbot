"""Main FastAPI application."""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import engine
from app.db.base import Base

# Import routers
from app.api import auth, companies, analysis, insights, system

# Import services for cleanup
from app.services.llm_service import llm_service
from app.services.data_source_service import data_source_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting BioNewsBot API", version=settings.VERSION)

    # Create database tables
    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)

    # Initialize services
    logger.info("Initializing services")

    yield

    # Shutdown
    logger.info("Shutting down BioNewsBot API")

    # Cleanup services
    await data_source_service.close()

    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="BioNewsBot API - Life Sciences Company Intelligence Platform",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(
        "HTTP exception",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to BioNewsBot API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/system/health"
    }


# Include routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    companies.router,
    prefix="/api/v1/companies",
    tags=["Companies"]
)

app.include_router(
    analysis.router,
    prefix="/api/v1/analysis",
    tags=["Analysis"]
)

app.include_router(
    insights.router,
    prefix="/api/v1/insights",
    tags=["Insights"]
)

app.include_router(
    system.router,
    prefix="/api/v1/system",
    tags=["System"]
)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    # Skip logging for health checks
    if request.url.path == "/api/v1/system/health":
        return await call_next(request)

    logger.info(
        "Request received",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None
    )

    response = await call_next(request)

    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    )

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use our custom logging
    )
