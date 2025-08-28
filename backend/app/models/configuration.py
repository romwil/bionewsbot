"""System configuration model for application settings."""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class SystemConfiguration(Base):
    """Model for storing system-wide configuration."""

    __tablename__ = "system_configuration"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(JSONB, nullable=False)

    # Configuration metadata
    category = Column(String(100), nullable=False)  # llm, analysis, notification, security, etc.
    data_type = Column(String(50), nullable=False)  # string, integer, boolean, json, etc.
    description = Column(Text)

    # Validation and constraints
    is_sensitive = Column(Boolean, default=False)  # For sensitive configs like API keys
    is_readonly = Column(Boolean, default=False)  # System configs that shouldn't be changed
    validation_rules = Column(JSONB)  # JSON schema or custom validation rules

    # Default and limits
    default_value = Column(JSONB)
    min_value = Column(JSONB)
    max_value = Column(JSONB)
    allowed_values = Column(JSONB)  # For enum-like configs

    # Audit fields
    last_modified_by_id = Column(UUID(as_uuid=True))
    last_modified_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<SystemConfiguration(key={self.key}, category={self.category})>"
