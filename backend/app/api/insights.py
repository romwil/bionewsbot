"""Insights management routes."""
from typing import Any, List, Optional
from datetime import datetime, timedelta
import uuid
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.deps import get_current_active_user, get_current_analyst_user
from ..core.logging import get_logger
from ..db.session import get_db
from ..models.user import User
from ..models.insight import Insight, InsightCategory
from ..models.company import Company
from ..schemas.insight import (
    InsightResponse,
    InsightListResponse,
    InsightUpdate,
    InsightCategoryResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=InsightListResponse)
async def list_insights(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    company_id: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|priority|confidence_score|impact_score)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """List insights with filtering and pagination."""
    logger.info(
        "Listing insights",
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters={
            "company_id": company_id,
            "category_id": category_id,
            "priority": priority,
            "status": status
        }
    )

    # Build query
    query = db.query(Insight).join(Company).join(InsightCategory)

    # Apply filters
    if company_id:
        query = query.filter(Insight.company_id == company_id)

    if category_id:
        query = query.filter(Insight.category_id == category_id)

    if priority:
        query = query.filter(Insight.priority == priority)

    if status:
        query = query.filter(Insight.status == status)

    if date_from:
        query = query.filter(Insight.created_at >= date_from)

    if date_to:
        query = query.filter(Insight.created_at <= date_to)

    if search:
        search_filter = or_(
            Insight.title.ilike(f"%{search}%"),
            Insight.summary.ilike(f"%{search}%"),
            Company.name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Apply sorting
    if sort_order == "desc":
        query = query.order_by(getattr(Insight, sort_by).desc())
    else:
        query = query.order_by(getattr(Insight, sort_by).asc())

    # Get total count
    total = query.count()

    # Apply pagination
    insights = query.offset(skip).limit(limit).all()

    return {
        "insights": insights,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/categories", response_model=List[InsightCategoryResponse])
async def list_insight_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all insight categories."""
    logger.info("Listing insight categories", user_id=current_user.id)

    categories = db.query(InsightCategory).order_by(
        InsightCategory.priority_score.desc()
    ).all()

    return categories


@router.get("/high-priority", response_model=InsightListResponse)
async def list_high_priority_insights(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """List high-priority insights from recent days."""
    logger.info(
        "Listing high-priority insights",
        user_id=current_user.id,
        days=days
    )

    # Calculate date cutoff
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query high-priority insights
    query = db.query(Insight).join(InsightCategory).filter(
        Insight.priority == "high",
        Insight.created_at >= cutoff_date,
        Insight.status != "dismissed"
    ).order_by(
        Insight.impact_score.desc(),
        Insight.confidence_score.desc()
    )

    # Get total count
    total = query.count()

    # Apply pagination
    insights = query.offset(skip).limit(limit).all()

    return {
        "insights": insights,
        "total": total,
        "skip": skip,
        "limit": limit
    }



@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get insight details."""
    logger.info(
        "Getting insight",
        user_id=current_user.id,
        insight_id=insight_id
    )

    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )

    # Mark as viewed
    if insight.status == "new":
        insight.status = "viewed"
        insight.viewed_at = datetime.utcnow()
        insight.viewed_by_id = current_user.id
        db.commit()

    return insight


@router.patch("/{insight_id}", response_model=InsightResponse)
async def update_insight(
    insight_id: str,
    update_data: InsightUpdate,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update insight status or notes."""
    logger.info(
        "Updating insight",
        user_id=current_user.id,
        insight_id=insight_id
    )

    # Get insight
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )

    # Update fields
    if update_data.status:
        old_status = insight.status
        insight.status = update_data.status

        # Set status change metadata
        if update_data.status == "reviewed":
            insight.reviewed_at = datetime.utcnow()
            insight.reviewed_by_id = current_user.id
        elif update_data.status == "actioned":
            insight.actioned_at = datetime.utcnow()
            insight.actioned_by_id = current_user.id

        logger.info(
            "Insight status changed",
            insight_id=insight_id,
            old_status=old_status,
            new_status=update_data.status
        )

    if update_data.analyst_notes is not None:
        insight.analyst_notes = update_data.analyst_notes

    if update_data.tags is not None:
        insight.tags = update_data.tags

    insight.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(insight)

    return insight


@router.post("/{insight_id}/mark-reviewed")
async def mark_insight_reviewed(
    insight_id: str,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Mark an insight as reviewed."""
    logger.info(
        "Marking insight as reviewed",
        user_id=current_user.id,
        insight_id=insight_id
    )

    # Get insight
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )

    # Update status
    insight.status = "reviewed"
    insight.reviewed_at = datetime.utcnow()
    insight.reviewed_by_id = current_user.id

    db.commit()

    return {"message": "Insight marked as reviewed"}


@router.post("/bulk-update")
async def bulk_update_insights(
    insight_ids: List[str],
    update_data: InsightUpdate,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Bulk update multiple insights."""
    logger.info(
        "Bulk updating insights",
        user_id=current_user.id,
        count=len(insight_ids)
    )

    # Get insights
    insights = db.query(Insight).filter(
        Insight.id.in_(insight_ids)
    ).all()

    if len(insights) != len(insight_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more insights not found"
        )

    # Update each insight
    updated_count = 0
    for insight in insights:
        if update_data.status:
            insight.status = update_data.status
            if update_data.status == "reviewed":
                insight.reviewed_at = datetime.utcnow()
                insight.reviewed_by_id = current_user.id
            elif update_data.status == "actioned":
                insight.actioned_at = datetime.utcnow()
                insight.actioned_by_id = current_user.id

        if update_data.analyst_notes is not None:
            insight.analyst_notes = update_data.analyst_notes

        if update_data.tags is not None:
            insight.tags = update_data.tags

        insight.updated_at = datetime.utcnow()
        updated_count += 1

    db.commit()

    logger.info(
        "Bulk update completed",
        user_id=current_user.id,
        updated_count=updated_count
    )

    return {
        "message": f"Updated {updated_count} insights",
        "updated_count": updated_count
    }


@router.get("/export/csv")
async def export_insights_csv(
    company_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Export insights to CSV format."""
    logger.info(
        "Exporting insights to CSV",
        user_id=current_user.id,
        company_id=company_id
    )

    # Build query
    query = db.query(Insight).join(Company).join(InsightCategory)

    if company_id:
        query = query.filter(Insight.company_id == company_id)

    if date_from:
        query = query.filter(Insight.created_at >= date_from)

    if date_to:
        query = query.filter(Insight.created_at <= date_to)

    insights = query.all()

    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "ID", "Company", "Category", "Title", "Summary",
        "Priority", "Status", "Confidence Score", "Impact Score",
        "Event Date", "Created At", "Reviewed By", "Analyst Notes"
    ])

    # Write data
    for insight in insights:
        writer.writerow([
            str(insight.id),
            insight.company.name,
            insight.category.name,
            insight.title,
            insight.summary,
            insight.priority,
            insight.status,
            insight.confidence_score,
            insight.impact_score,
            insight.event_date.isoformat() if insight.event_date else "",
            insight.created_at.isoformat(),
            insight.reviewed_by.full_name if insight.reviewed_by else "",
            insight.analyst_notes or ""
        ])

    # Return CSV file
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=insights_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/stats/summary")
async def get_insights_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get insights summary statistics."""
    logger.info(
        "Getting insights summary",
        user_id=current_user.id,
        days=days
    )

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get total insights
    total_insights = db.query(Insight).filter(
        Insight.created_at >= cutoff_date
    ).count()

    # Get insights by priority
    high_priority = db.query(Insight).filter(
        Insight.created_at >= cutoff_date,
        Insight.priority == "high"
    ).count()

    medium_priority = db.query(Insight).filter(
        Insight.created_at >= cutoff_date,
        Insight.priority == "medium"
    ).count()

    low_priority = db.query(Insight).filter(
        Insight.created_at >= cutoff_date,
        Insight.priority == "low"
    ).count()

    # Get insights by status
    new_insights = db.query(Insight).filter(
        Insight.created_at >= cutoff_date,
        Insight.status == "new"
    ).count()

    reviewed_insights = db.query(Insight).filter(
        Insight.created_at >= cutoff_date,
        Insight.status == "reviewed"
    ).count()

    actioned_insights = db.query(Insight).filter(
        Insight.created_at >= cutoff_date,
        Insight.status == "actioned"
    ).count()

    # Get top categories
    from sqlalchemy import func

    top_categories = db.query(
        InsightCategory.name,
        func.count(Insight.id).label("count")
    ).join(
        Insight
    ).filter(
        Insight.created_at >= cutoff_date
    ).group_by(
        InsightCategory.name
    ).order_by(
        func.count(Insight.id).desc()
    ).limit(5).all()

    return {
        "period_days": days,
        "total_insights": total_insights,
        "by_priority": {
            "high": high_priority,
            "medium": medium_priority,
            "low": low_priority
        },
        "by_status": {
            "new": new_insights,
            "reviewed": reviewed_insights,
            "actioned": actioned_insights
        },
        "top_categories": [
            {"name": cat[0], "count": cat[1]}
            for cat in top_categories
        ]
    }
