"""Insight schemas for analysis findings and categorization."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

from .base import BaseSchema, TimestampMixin


class InsightCategoryBase(BaseSchema):
    """Base insight category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_high_priority: bool = False
    priority_score: int = Field(50, ge=0, le=100)
    keywords: Optional[List[str]] = []
    color_code: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    icon_name: Optional[str] = None


class InsightCategoryCreate(InsightCategoryBase):
    """Schema for creating insight category."""
    pass


class InsightCategoryUpdate(BaseSchema):
    """Schema for updating insight category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_high_priority: Optional[bool] = None
    priority_score: Optional[int] = Field(None, ge=0, le=100)
    keywords: Optional[List[str]] = None
    color_code: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    icon_name: Optional[str] = None


class InsightCategoryInDB(InsightCategoryBase, TimestampMixin):
    """Insight category with database fields."""
    id: UUID
    total_insights_count: int = 0


class InsightCategoryResponse(InsightCategoryInDB):
    """Insight category response."""
    pass


class InsightBase(BaseSchema):
    """Base insight schema."""
    company_id: UUID
    category_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    summary: str = Field(..., min_length=1)
    full_content: Optional[str] = None

    priority: str = Field("medium", regex="^(high|medium|low)$")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    impact_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    source_urls: Optional[List[str]] = []
    extracted_entities: Optional[Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="Named entities: people, organizations, drugs, etc."
    )
    key_metrics: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Numerical data: funding amounts, trial phases, etc."
    )

    event_date: Optional[datetime] = None
    published_date: Optional[datetime] = None


class InsightCreate(InsightBase):
    """Schema for creating insight."""
    analysis_result_id: UUID
    content_hash: Optional[str] = None

    @validator('priority')
    def validate_priority_based_on_category(cls, v, values):
        # This would be enhanced with actual category lookup
        return v


class InsightUpdate(BaseSchema):
    """Schema for updating insight."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    summary: Optional[str] = Field(None, min_length=1)
    full_content: Optional[str] = None

    priority: Optional[str] = Field(None, regex="^(high|medium|low)$")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    impact_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    status: Optional[str] = Field(None, regex="^(new|reviewed|archived|dismissed)$")

    source_urls: Optional[List[str]] = None
    extracted_entities: Optional[Dict[str, List[str]]] = None
    key_metrics: Optional[Dict[str, Any]] = None

    event_date: Optional[datetime] = None
    published_date: Optional[datetime] = None


class InsightReview(BaseSchema):
    """Schema for reviewing insight."""
    status: str = Field(..., regex="^(reviewed|archived|dismissed)$")
    review_notes: Optional[str] = None


class InsightInDB(InsightBase, TimestampMixin):
    """Insight with all database fields."""
    id: UUID
    analysis_result_id: UUID

    status: str = "new"
    reviewed_at: Optional[datetime] = None
    reviewed_by_id: Optional[UUID] = None

    content_hash: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of_id: Optional[UUID] = None


class InsightResponse(InsightInDB):
    """Insight response schema."""
    company_name: Optional[str] = None
    category_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None


class InsightWithRelated(InsightResponse):
    """Insight with related insights."""
    related_insights: List[Dict[str, Any]] = []
    duplicate_insights: List[Dict[str, Any]] = []


class InsightFilter(BaseSchema):
    """Schema for filtering insights."""
    company_ids: Optional[List[UUID]] = None
    category_ids: Optional[List[UUID]] = None
    priorities: Optional[List[str]] = None
    statuses: Optional[List[str]] = None

    search: Optional[str] = Field(None, description="Search in title and summary")

    min_confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_impact_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    event_date_from: Optional[datetime] = None
    event_date_to: Optional[datetime] = None
    created_date_from: Optional[datetime] = None
    created_date_to: Optional[datetime] = None

    has_duplicates: Optional[bool] = None
    reviewed_by_id: Optional[UUID] = None

    sort_by: str = Field(
        "created_at",
        regex="^(created_at|event_date|priority|confidence_score|impact_score)$"
    )
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class InsightBulkAction(BaseSchema):
    """Schema for bulk actions on insights."""
    insight_ids: List[UUID]
    action: str = Field(..., regex="^(review|archive|dismiss|change_priority)$")
    priority: Optional[str] = Field(None, regex="^(high|medium|low)$")
    review_notes: Optional[str] = None


class InsightStats(BaseSchema):
    """Insight statistics."""
    total_insights: int
    new_insights: int
    reviewed_insights: int
    high_priority_insights: int

    insights_by_category: Dict[str, int]
    insights_by_priority: Dict[str, int]
    insights_by_company: List[Dict[str, Any]]

    insights_last_24h: int
    insights_last_7d: int
    insights_last_30d: int

    average_confidence_score: float
    average_impact_score: float


class InsightExport(BaseSchema):
    """Schema for exporting insights."""
    format: str = Field("csv", regex="^(csv|json|excel)$")
    include_full_content: bool = False
    filters: Optional[InsightFilter] = None
