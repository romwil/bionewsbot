"""Analysis models for tracking LLM analysis runs and results."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class AnalysisRun(Base):
    """Model for tracking analysis runs."""

    __tablename__ = "analysis_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_type = Column(String(50), nullable=False)  # scheduled, manual, triggered
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed

    # Timing information
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Run statistics
    total_companies = Column(Integer, default=0)
    processed_companies = Column(Integer, default=0)
    failed_companies = Column(Integer, default=0)
    insights_generated = Column(Integer, default=0)
    high_priority_insights = Column(Integer, default=0)

    # Error tracking
    error_count = Column(Integer, default=0)
    error_details = Column(JSONB)

    # Run configuration
    configuration = Column(JSONB)  # Model settings, prompts used, etc.

    # User who triggered the run (if manual)
    triggered_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    triggered_by = relationship("User", backref="analysis_runs")
    results = relationship("AnalysisResult", back_populates="analysis_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnalysisRun(id={self.id}, status={self.status}, started_at={self.started_at})>"


class AnalysisResult(Base):
    """Model for storing individual company analysis results."""

    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    # Analysis status
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed

    # LLM interaction data
    prompt_template = Column(Text)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    model_used = Column(String(100))
    temperature = Column(Float)

    # Raw LLM response
    raw_response = Column(Text)

    # Parsed analysis data
    parsed_data = Column(JSONB)  # Structured data extracted from LLM response

    # Validation results
    validation_status = Column(String(50))  # valid, invalid, partial
    validation_errors = Column(JSONB)

    # Performance metrics
    processing_time_seconds = Column(Float)
    retry_count = Column(Integer, default=0)

    # Error handling
    error_message = Column(Text)
    error_type = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="results")
    company = relationship("Company", backref="analysis_results")

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, company_id={self.company_id}, status={self.status})>"
