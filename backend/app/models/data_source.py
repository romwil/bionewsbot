"""Data source models for tracking information sources."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class DataSource(Base):
    """Model for external data sources."""

    __tablename__ = "data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    source_type = Column(String(50), nullable=False)  # news, regulatory, clinical_trials, financial, scientific

    # Connection details
    base_url = Column(String(500))
    api_endpoint = Column(String(500))
    authentication_type = Column(String(50))  # none, api_key, oauth, basic

    # Configuration
    configuration = Column(JSONB)  # API keys, headers, query parameters, etc.
    rate_limit_requests = Column(Integer)
    rate_limit_period = Column(Integer)  # seconds

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_premium = Column(Boolean, default=False)  # Premium/paid sources
    reliability_score = Column(Float, default=0.8)  # 0.0 to 1.0

    # Monitoring
    last_checked_at = Column(DateTime(timezone=True))
    last_error_at = Column(DateTime(timezone=True))
    error_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)

    # Metadata
    description = Column(Text)
    documentation_url = Column(String(500))
    tags = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company_sources = relationship("CompanyDataSource", back_populates="data_source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DataSource(id={self.id}, name={self.name}, type={self.source_type})>"


class CompanyDataSource(Base):
    """Junction table for company-specific data source configurations."""

    __tablename__ = "company_data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False)

    # Company-specific configuration
    is_active = Column(Boolean, default=True, nullable=False)
    custom_query_parameters = Column(JSONB)  # Company-specific search terms, filters, etc.

    # Monitoring settings
    check_frequency_hours = Column(Integer, default=24)
    last_checked_at = Column(DateTime(timezone=True))

    # Statistics
    total_items_found = Column(Integer, default=0)
    relevant_items_found = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", backref="data_sources")
    data_source = relationship("DataSource", back_populates="company_sources")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('company_id', 'data_source_id', name='_company_source_uc'),
    )

    def __repr__(self):
        return f"<CompanyDataSource(company_id={self.company_id}, source_id={self.data_source_id})>"
