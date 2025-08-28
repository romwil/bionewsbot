"""Company model for life sciences companies."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class Company(Base):
    """Company model for tracking life sciences companies."""

    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    ticker_symbol = Column(String(20), unique=True, index=True)
    description = Column(Text)

    # Industry classification
    industry = Column(String(100), nullable=False, default="Biotechnology")
    sub_industry = Column(String(100))
    therapeutic_areas = Column(JSONB)  # List of therapeutic areas

    # Company details
    founded_year = Column(Integer)
    headquarters_location = Column(String(255))
    website_url = Column(String(500))
    employee_count = Column(Integer)
    market_cap = Column(Float)

    # Monitoring settings
    is_active = Column(Boolean, default=True, nullable=False)
    monitoring_enabled = Column(Boolean, default=True, nullable=False)
    priority_level = Column(String(20), default="medium")  # high, medium, low

    # Analysis metadata
    last_analysis_at = Column(DateTime(timezone=True))
    analysis_frequency_hours = Column(Integer, default=24)
    total_insights_count = Column(Integer, default=0)
    high_priority_insights_count = Column(Integer, default=0)

    # Additional data
    metadata = Column(JSONB)  # Flexible storage for additional company data
    tags = Column(JSONB)  # List of tags for categorization

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True))  # Soft delete

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, ticker={self.ticker_symbol})>"
