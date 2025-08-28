"""Analysis management routes."""
from typing import Any, List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from ..core.deps import get_current_active_user, get_current_analyst_user
from ..core.logging import get_logger
from ..db.session import get_db
from ..models.user import User
from ..models.analysis import AnalysisRun, AnalysisResult
from ..models.company import Company
from ..schemas.analysis import (
    AnalysisRunCreate,
    AnalysisRunResponse,
    AnalysisResultResponse,
    AnalysisStatsResponse
)
from ..services.analysis_service import analysis_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/runs", response_model=AnalysisRunResponse)
async def create_analysis_run(
    run_data: AnalysisRunCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create and start a new analysis run."""
    logger.info(
        "Creating analysis run",
        user_id=current_user.id,
        run_type=run_data.run_type,
        company_ids=run_data.company_ids
    )

    # Validate companies exist
    if run_data.company_ids:
        companies = db.query(Company).filter(
            Company.id.in_(run_data.company_ids)
        ).all()

        if len(companies) != len(run_data.company_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more companies not found"
            )

    # Create analysis run
    analysis_run = await analysis_service.create_analysis_run(
        db=db,
        run_type=run_data.run_type,
        company_ids=run_data.company_ids,
        parameters=run_data.parameters or {},
        created_by_id=current_user.id
    )

    # Start analysis in background
    background_tasks.add_task(
        analysis_service.run_analysis,
        db=db,
        run_id=str(analysis_run.id)
    )

    return analysis_run


@router.get("/runs", response_model=List[AnalysisRunResponse])
async def list_analysis_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    run_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """List analysis runs with filtering."""
    logger.info(
        "Listing analysis runs",
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    # Build query
    query = db.query(AnalysisRun)

    # Apply filters
    if status:
        query = query.filter(AnalysisRun.status == status)

    if run_type:
        query = query.filter(AnalysisRun.run_type == run_type)

    # Order by created date
    query = query.order_by(AnalysisRun.created_at.desc())

    # Apply pagination
    runs = query.offset(skip).limit(limit).all()

    return runs


@router.get("/runs/{run_id}", response_model=AnalysisRunResponse)
async def get_analysis_run(
    run_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get analysis run details."""
    logger.info(
        "Getting analysis run",
        user_id=current_user.id,
        run_id=run_id
    )

    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found"
        )

    return run


@router.get("/runs/{run_id}/results", response_model=List[AnalysisResultResponse])
async def get_analysis_results(
    run_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get results for an analysis run."""
    logger.info(
        "Getting analysis results",
        user_id=current_user.id,
        run_id=run_id
    )

    # Verify run exists
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found"
        )

    # Get results
    results = db.query(AnalysisResult).filter(
        AnalysisResult.analysis_run_id == run_id
    ).all()

    return results


@router.post("/runs/{run_id}/cancel")
async def cancel_analysis_run(
    run_id: str,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Cancel a running analysis."""
    logger.info(
        "Cancelling analysis run",
        user_id=current_user.id,
        run_id=run_id
    )

    # Get run
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found"
        )

    if run.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel analysis in {run.status} status"
        )

    # Update status
    run.status = "cancelled"
    run.completed_at = datetime.utcnow()
    run.error_message = "Cancelled by user"

    db.commit()

    logger.info(
        "Analysis run cancelled",
        user_id=current_user.id,
        run_id=run_id
    )

    return {"message": "Analysis run cancelled"}


@router.get("/stats", response_model=AnalysisStatsResponse)
async def get_analysis_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get analysis statistics."""
    logger.info(
        "Getting analysis stats",
        user_id=current_user.id,
        days=days
    )

    stats = await analysis_service.get_analysis_stats(db, days)
    return stats


@router.post("/trigger-scheduled")
async def trigger_scheduled_analysis(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Manually trigger scheduled analysis for all monitored companies."""
    logger.info(
        "Triggering scheduled analysis",
        user_id=current_user.id
    )

    # Get all monitored companies
    monitored_companies = db.query(Company).filter(
        Company.monitoring_enabled == True,
        Company.is_active == True
    ).all()

    if not monitored_companies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No companies are currently being monitored"
        )

    company_ids = [str(company.id) for company in monitored_companies]

    # Create analysis run
    analysis_run = await analysis_service.create_analysis_run(
        db=db,
        run_type="scheduled",
        company_ids=company_ids,
        parameters={"triggered_manually": True},
        created_by_id=current_user.id
    )

    # Start analysis in background
    background_tasks.add_task(
        analysis_service.run_analysis,
        db=db,
        run_id=str(analysis_run.id)
    )

    logger.info(
        "Scheduled analysis triggered",
        user_id=current_user.id,
        run_id=analysis_run.id,
        company_count=len(company_ids)
    )

    return {
        "message": f"Analysis started for {len(company_ids)} companies",
        "run_id": str(analysis_run.id),
        "company_count": len(company_ids)
    }
