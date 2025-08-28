"""Data models for notifications and insights."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import uuid


class Priority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class InsightType(str, Enum):
    """Types of insights that can trigger notifications."""
    REGULATORY_APPROVAL = "regulatory_approval"
    CLINICAL_TRIAL = "clinical_trial"
    MERGER_ACQUISITION = "merger_acquisition"
    FUNDING_ROUND = "funding_round"
    PARTNERSHIP = "partnership"
    CUSTOM = "custom"


class NotificationStatus(str, Enum):
    """Status of a notification."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"


class Company(BaseModel):
    """Company information model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    ticker: Optional[str] = None
    sector: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    

class InsightData(BaseModel):
    """Detailed insight data."""
    # Regulatory approval specific
    regulatory_body: Optional[str] = None  # FDA, EMA, etc.
    approval_type: Optional[str] = None  # NDA, BLA, etc.
    drug_name: Optional[str] = None
    indication: Optional[str] = None
    
    # Clinical trial specific
    trial_phase: Optional[str] = None
    trial_status: Optional[str] = None
    patient_count: Optional[int] = None
    primary_endpoint: Optional[str] = None
    
    # M&A specific
    acquirer: Optional[str] = None
    target: Optional[str] = None
    deal_value: Optional[float] = None
    deal_type: Optional[str] = None  # acquisition, merger, etc.
    
    # Funding specific
    funding_amount: Optional[float] = None
    funding_round: Optional[str] = None  # Series A, B, etc.
    lead_investor: Optional[str] = None
    valuation: Optional[float] = None
    
    # Partnership specific
    partner_companies: Optional[List[str]] = None
    partnership_type: Optional[str] = None
    deal_terms: Optional[str] = None
    
    # Additional flexible data
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Insight(BaseModel):
    """Main insight model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: InsightType
    priority: Priority = Priority.NORMAL
    
    # Core information
    title: str
    summary: str
    detailed_analysis: Optional[str] = None
    
    # Company information
    company: Company
    related_companies: Optional[List[Company]] = Field(default_factory=list)
    
    # Insight-specific data
    data: InsightData = Field(default_factory=InsightData)
    
    # Metadata
    source_url: Optional[str] = None
    published_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    @validator('priority', pre=True)
    def set_priority_based_on_type(cls, v, values):
        """Auto-set priority based on insight type if not provided."""
        if v is None and 'type' in values:
            priority_map = {
                InsightType.REGULATORY_APPROVAL: Priority.HIGH,
                InsightType.MERGER_ACQUISITION: Priority.HIGH,
                InsightType.CLINICAL_TRIAL: Priority.NORMAL,
                InsightType.FUNDING_ROUND: Priority.NORMAL,
                InsightType.PARTNERSHIP: Priority.NORMAL,
                InsightType.CUSTOM: Priority.NORMAL,
            }
            return priority_map.get(values['type'], Priority.NORMAL)
        return v


class NotificationRequest(BaseModel):
    """Request to send a notification."""
    insight: Insight
    channels: Optional[List[str]] = None  # Override default channels
    thread_ts: Optional[str] = None  # Reply in thread
    

class NotificationHistory(BaseModel):
    """Notification history record."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insight_id: str
    
    # Delivery information
    channel: str
    message_ts: Optional[str] = None  # Slack timestamp
    thread_ts: Optional[str] = None
    
    # Status tracking
    status: NotificationStatus = NotificationStatus.PENDING
    attempts: int = 0
    last_error: Optional[str] = None
    
    # User interaction
    read_by: Optional[List[str]] = Field(default_factory=list)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    

class SlackAction(BaseModel):
    """Slack interactive action."""
    action_id: str
    action_type: str  # button, select, etc.
    value: Optional[str] = None
    user_id: str
    user_name: str
    channel_id: str
    message_ts: str
    response_url: str
    

class SlackInteraction(BaseModel):
    """Slack interaction payload."""
    type: str  # block_actions, view_submission, etc.
    user: Dict[str, Any]
    channel: Dict[str, Any]
    message: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    response_url: Optional[str] = None
    trigger_id: Optional[str] = None
