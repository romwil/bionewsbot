"""Insight models for storing and categorizing analysis findings."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class InsightCategory(Base):
    """Model for insight categories."""

    __tablename__ = "insight_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    # Priority and importance
    is_high_priority = Column(Boolean, default=False)
    priority_score = Column(Integer, default=50)  # 0-100 scale

    # Category metadata
    keywords = Column(JSONB)  # Keywords that identify this category
    color_code = Column(String(7))  # Hex color for UI display
    icon_name = Column(String(50))  # Icon identifier for UI

    # Statistics
    total_insights_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    insights = relationship("Insight", back_populates="category")

    def __repr__(self):
        return f"<InsightCategory(id={self.id}, name={self.name})>"


class Insight(Base):
    """Model for storing individual insights from analysis."""

    __tablename__ = "insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    analysis_result_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("insight_categories.id"), nullable=False)

    # Insight content
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    full_content = Column(Text)

    # Priority and importance
    priority = Column(String(20), nullable=False, default="medium")  # high, medium, low
    confidence_score = Column(Float)  # 0.0 to 1.0
    impact_score = Column(Float)  # 0.0 to 1.0

    # Metadata
    source_urls = Column(JSONB)  # List of source URLs
    extracted_entities = Column(JSONB)  # Named entities (people, organizations, drugs, etc.)
    key_metrics = Column(JSONB)  # Numerical data extracted (funding amounts, trial phases, etc.)

    # Status tracking
    status = Column(String(50), default="new")  # new, reviewed, archived, dismissed
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Deduplication
    content_hash = Column(String(64), index=True)  # SHA-256 hash for deduplication
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(UUID(as_uuid=True), ForeignKey("insights.id"))

    # Timestamps
    event_date = Column(DateTime(timezone=True))  # When the event occurred
    published_date = Column(DateTime(timezone=True))  # When the news was published

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True))  # Soft delete

    # Relationships
    company = relationship("Company", backref="insights")
    category = relationship("InsightCategory", back_populates="insights")
    analysis_result = relationship("AnalysisResult", backref="insights")
    reviewed_by = relationship("User", backref="reviewed_insights")
    duplicate_of = relationship("Insight", remote_side=[id], backref="duplicates")

    # Unique constraint to prevent exact duplicates
    __table_args__ = (
        UniqueConstraint('company_id', 'content_hash', name='_company_content_uc'),
    )

    def __repr__(self):
        return f"<Insight(id={self.id}, company_id={self.company_id}, priority={self.priority})>"
