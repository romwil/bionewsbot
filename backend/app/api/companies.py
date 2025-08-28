"""Company management routes."""
from typing import Any, List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from ..core.deps import get_current_active_user, get_current_analyst_user
from ..core.logging import get_logger
from ..db.session import get_db
from ..models.company import Company
from ..schemas.company import (
from ..models.user import User
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    therapeutic_area: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    monitoring_enabled: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """List companies with filtering and pagination."""
    logger.info(
        "Listing companies",
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search
    )

    # Build query
    query = db.query(Company)

    # Apply filters
    if search:
        search_filter = or_(
            Company.name.ilike(f"%{search}%"),
            Company.ticker_symbol.ilike(f"%{search}%"),
            Company.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if industry:
        query = query.filter(Company.industry == industry)

    if therapeutic_area:
        query = query.filter(
            Company.therapeutic_areas.contains([therapeutic_area])
        )

    if is_active is not None:
        query = query.filter(Company.is_active == is_active)

    if monitoring_enabled is not None:
        query = query.filter(Company.monitoring_enabled == monitoring_enabled)

    # Get total count
    total = query.count()

    # Apply pagination
    companies = query.offset(skip).limit(limit).all()

    return {
        "companies": companies,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get company by ID."""
    logger.info("Getting company", user_id=current_user.id, company_id=company_id)

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return company


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new company."""
    logger.info(
        "Creating company",
        user_id=current_user.id,
        company_name=company_data.name
    )

    # Check if company with same name exists
    existing = db.query(Company).filter(
        Company.name == company_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company with this name already exists"
        )

    # Create company
    company = Company(
        **company_data.dict(),
        created_by_id=current_user.id
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    logger.info(
        "Company created",
        user_id=current_user.id,
        company_id=company.id,
        company_name=company.name
    )

    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update company information."""
    logger.info(
        "Updating company",
        user_id=current_user.id,
        company_id=company_id
    )

    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Update fields
    update_data = company_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    company.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(company)

    logger.info(
        "Company updated",
        user_id=current_user.id,
        company_id=company.id,
        updated_fields=list(update_data.keys())
    )

    return company


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a company (soft delete)."""
    logger.info(
        "Deleting company",
        user_id=current_user.id,
        company_id=company_id
    )

    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Soft delete
    company.deleted_at = datetime.utcnow()
    company.is_active = False
    company.monitoring_enabled = False

    db.commit()

    logger.info(
        "Company deleted",
        user_id=current_user.id,
        company_id=company.id,
        company_name=company.name
    )

    return {"message": "Company deleted successfully"}


@router.post("/{company_id}/toggle-monitoring")
async def toggle_monitoring(
    company_id: str,
    current_user: User = Depends(get_current_analyst_user),
    db: Session = Depends(get_db)
) -> Any:
    """Toggle monitoring for a company."""
    logger.info(
        "Toggling company monitoring",
        user_id=current_user.id,
        company_id=company_id
    )

    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Toggle monitoring
    company.monitoring_enabled = not company.monitoring_enabled
    company.updated_at = datetime.utcnow()

    db.commit()

    logger.info(
        "Company monitoring toggled",
        user_id=current_user.id,
        company_id=company.id,
        monitoring_enabled=company.monitoring_enabled
    )

    return {
        "message": f"Monitoring {'enabled' if company.monitoring_enabled else 'disabled'}",
        "monitoring_enabled": company.monitoring_enabled
    }


@router.get("/{company_id}/stats")
async def get_company_stats(
    company_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get company statistics."""
    logger.info(
        "Getting company stats",
        user_id=current_user.id,
        company_id=company_id
    )

    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Get insights count by category
    from ..models.insight import Insight, InsightCategory

    insights_by_category = {}
    categories = db.query(InsightCategory).all()

    for category in categories:
        count = db.query(Insight).filter(
            Insight.company_id == company.id,
            Insight.category_id == category.id
        ).count()
        if count > 0:
            insights_by_category[category.name] = count

    # Get recent analysis runs
    from ..models.analysis import AnalysisResult

    recent_analyses = db.query(AnalysisResult).filter(
        AnalysisResult.company_id == company.id
    ).order_by(AnalysisResult.created_at.desc()).limit(5).all()

    return {
        "company_id": str(company.id),
        "name": company.name,
        "total_insights": company.total_insights_count,
        "high_priority_insights": company.high_priority_insights_count,
        "insights_by_category": insights_by_category,
        "last_analysis_at": company.last_analysis_at.isoformat() if company.last_analysis_at else None,
        "recent_analyses": [
            {
                "id": str(analysis.id),
                "created_at": analysis.created_at.isoformat(),
                "insights_generated": analysis.insights_generated,
                "confidence_score": analysis.confidence_score
            }
            for analysis in recent_analyses
        ]
    }
