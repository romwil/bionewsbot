"""Analysis schemas for LLM analysis runs and results."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

from .base import BaseSchema, TimestampMixin


class AnalysisRunBase(BaseSchema):
    """Base analysis run schema."""
    run_type: str = Field(..., regex="^(scheduled|manual|triggered)$")
    configuration: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Model settings, prompts, etc."
    )


class AnalysisRunCreate(AnalysisRunBase):
    """Schema for creating a new analysis run."""
    company_ids: Optional[List[UUID]] = Field(
        None,
        description="Specific companies to analyze. If None, analyzes all active companies."
    )
    force_rerun: bool = Field(
        False,
        description="Force analysis even if recently analyzed"
    )


class AnalysisRunUpdate(BaseSchema):
    """Schema for updating analysis run status."""
    status: Optional[str] = Field(None, regex="^(pending|running|completed|failed)$")
    completed_at: Optional[datetime] = None
    error_details: Optional[Dict[str, Any]] = None


class AnalysisRunInDB(AnalysisRunBase, TimestampMixin):
    """Analysis run with all database fields."""
    id: UUID
    status: str = "pending"

    # Timing information
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    # Run statistics
    total_companies: int = 0
    processed_companies: int = 0
    failed_companies: int = 0
    insights_generated: int = 0
    high_priority_insights: int = 0

    # Error tracking
    error_count: int = 0
    error_details: Optional[Dict[str, Any]] = None

    # User who triggered the run
    triggered_by_id: Optional[UUID] = None


class AnalysisRunResponse(AnalysisRunInDB):
    """Analysis run response schema."""
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0)

    @validator('progress_percentage', always=True)
    def calculate_progress(cls, v, values):
        total = values.get('total_companies', 0)
        processed = values.get('processed_companies', 0)
        if total > 0:
            return (processed / total) * 100
        return 0.0


class AnalysisRunWithResults(AnalysisRunResponse):
    """Analysis run with summary of results."""
    results_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of analysis results by category"
    )
    top_insights: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top high-priority insights generated"
    )


class AnalysisResultBase(BaseSchema):
    """Base analysis result schema."""
    company_id: UUID
    analysis_run_id: UUID
    status: str = Field("pending", regex="^(pending|processing|completed|failed)$")


class AnalysisResultCreate(AnalysisResultBase):
    """Schema for creating analysis result."""
    prompt_template: str
    model_used: str
    temperature: float = Field(0.7, ge=0.0, le=2.0)


class AnalysisResultUpdate(BaseSchema):
    """Schema for updating analysis result."""
    status: Optional[str] = Field(None, regex="^(pending|processing|completed|failed)$")
    raw_response: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    validation_status: Optional[str] = Field(None, regex="^(valid|invalid|partial)$")
    validation_errors: Optional[List[str]] = None
    error_message: Optional[str] = None

    # Token usage
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    # Performance
    processing_time_seconds: Optional[float] = None


class AnalysisResultInDB(AnalysisResultBase, TimestampMixin):
    """Analysis result with all database fields."""
    id: UUID

    # LLM interaction data
    prompt_template: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model_used: Optional[str] = None
    temperature: Optional[float] = None

    # Results
    raw_response: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None

    # Validation
    validation_status: Optional[str] = None
    validation_errors: Optional[List[str]] = None

    # Performance
    processing_time_seconds: Optional[float] = None
    retry_count: int = 0

    # Error handling
    error_message: Optional[str] = None
    error_type: Optional[str] = None


class AnalysisResultResponse(AnalysisResultInDB):
    """Analysis result response schema."""
    company_name: Optional[str] = None
    insights_count: int = 0


class AnalysisStats(BaseSchema):
    """Analysis statistics."""
    total_runs: int
    successful_runs: int
    failed_runs: int
    average_duration_seconds: float
    total_insights_generated: int
    insights_by_category: Dict[str, int]
    runs_by_type: Dict[str, int]
    recent_runs: List[Dict[str, Any]]


class LLMPromptTemplate(BaseSchema):
    """LLM prompt template configuration."""
    name: str
    description: str
    template: str
    variables: List[str]
    model_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9
        }
    )
