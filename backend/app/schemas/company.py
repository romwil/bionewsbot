"""Company schemas for life sciences companies."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
from uuid import UUID

from .base import BaseSchema, TimestampMixin


class CompanyBase(BaseSchema):
    """Base company schema."""
    name: str = Field(..., min_length=1, max_length=255)
    ticker_symbol: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None

    # Industry classification
    industry: str = "Biotechnology"
    sub_industry: Optional[str] = None
    therapeutic_areas: Optional[List[str]] = []

    # Company details
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    headquarters_location: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    employee_count: Optional[int] = Field(None, ge=0)
    market_cap: Optional[float] = Field(None, ge=0)

    # Monitoring settings
    monitoring_enabled: bool = True
    priority_level: str = Field("medium", regex="^(high|medium|low)$")
    analysis_frequency_hours: int = Field(24, ge=1, le=168)  # 1 hour to 1 week

    @validator('ticker_symbol')
    def uppercase_ticker(cls, v):
        return v.upper() if v else v


class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class CompanyUpdate(BaseSchema):
    """Schema for updating company information."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    ticker_symbol: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None

    # Industry classification
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    therapeutic_areas: Optional[List[str]] = None

    # Company details
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    headquarters_location: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    employee_count: Optional[int] = Field(None, ge=0)
    market_cap: Optional[float] = Field(None, ge=0)

    # Monitoring settings
    monitoring_enabled: Optional[bool] = None
    priority_level: Optional[str] = Field(None, regex="^(high|medium|low)$")
    analysis_frequency_hours: Optional[int] = Field(None, ge=1, le=168)

    # Additional data
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class CompanyInDB(CompanyBase, TimestampMixin):
    """Company schema with all database fields."""
    id: UUID
    is_active: bool = True

    # Analysis metadata
    last_analysis_at: Optional[datetime] = None
    total_insights_count: int = 0
    high_priority_insights_count: int = 0

    # Additional data
    metadata: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []


class CompanyResponse(CompanyInDB):
    """Company response schema."""
    pass


class CompanyWithInsights(CompanyResponse):
    """Company with recent insights summary."""
    recent_insights: List[Dict[str, Any]] = []
    insights_last_7_days: int = 0
    insights_last_30_days: int = 0


class CompanyFilter(BaseSchema):
    """Schema for filtering companies."""
    search: Optional[str] = Field(None, description="Search in name, ticker, description")
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    therapeutic_areas: Optional[List[str]] = None
    priority_level: Optional[str] = Field(None, regex="^(high|medium|low)$")
    monitoring_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    has_recent_insights: Optional[bool] = None
    min_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None
    tags: Optional[List[str]] = None


class CompanyBulkAction(BaseSchema):
    """Schema for bulk actions on companies."""
    company_ids: List[UUID]
    action: str = Field(..., regex="^(enable_monitoring|disable_monitoring|set_priority|delete)$")
    priority_level: Optional[str] = Field(None, regex="^(high|medium|low)$")


class CompanyStats(BaseSchema):
    """Company statistics."""
    total_companies: int
    active_companies: int
    monitored_companies: int
    companies_by_priority: Dict[str, int]
    companies_by_industry: Dict[str, int]
    companies_with_recent_insights: int
    average_insights_per_company: float
