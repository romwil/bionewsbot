"""Audit log model for tracking system changes."""
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class AuditLog(Base):
    """Model for audit logging of system changes."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What was changed
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # create, update, delete, login, logout, etc.

    # Who made the change
    user_id = Column(UUID(as_uuid=True), index=True)
    user_email = Column(String(255))  # Denormalized for historical accuracy
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)

    # What changed
    old_values = Column(JSONB)  # Previous state
    new_values = Column(JSONB)  # New state
    changed_fields = Column(JSONB)  # List of fields that changed

    # Additional context
    request_id = Column(String(100))  # For correlating with logs
    session_id = Column(String(100))
    api_endpoint = Column(String(255))
    http_method = Column(String(10))

    # Response information
    response_status = Column(Integer)
    error_message = Column(Text)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, table={self.table_name}, action={self.action})>"
