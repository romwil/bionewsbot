"""User schemas for authentication and user management."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

from .base import BaseSchema, TimestampMixin


class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserUpdate(BaseSchema):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseSchema):
    """Schema for updating user password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('new_password')
    def validate_password(cls, v, values):
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        # Apply same validation as UserCreate
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserInDB(UserBase, TimestampMixin):
    """User schema with all database fields."""
    id: UUID
    is_verified: bool = False
    is_superuser: bool = False
    permissions: Optional[List[str]] = None
    last_login: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None


class UserResponse(UserInDB):
    """User response schema (excludes sensitive data)."""
    pass


class UserLogin(BaseSchema):
    """Schema for user login."""
    username: str  # Can be username or email
    password: str


class TokenResponse(BaseSchema):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseSchema):
    """JWT token payload."""
    sub: str  # user_id
    exp: datetime
    type: str  # access or refresh
    role: Optional[str] = None
    permissions: Optional[List[str]] = None


class UserProfile(UserResponse):
    """Extended user profile with statistics."""
    total_insights_reviewed: int = 0
    total_analysis_triggered: int = 0
    companies_followed: int = 0
