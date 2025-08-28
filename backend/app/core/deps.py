"""Common dependencies for API routes."""
from typing import Optional
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings
from .logging import get_logger
from ..db.session import get_db
from ..models.user import User

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")

        if email is None or user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_analyst_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with analyst or admin role."""
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


class RateLimiter:
    """Rate limiting dependency."""

    def __init__(self, calls: int = 10, period: int = 60):
        """Initialize rate limiter.

        Args:
            calls: Number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.call_times = {}

    async def __call__(self, user: User = Depends(get_current_active_user)):
        """Check rate limit for user."""
        user_id = str(user.id)
        now = datetime.utcnow()

        # Clean old entries
        if user_id in self.call_times:
            self.call_times[user_id] = [
                call_time for call_time in self.call_times[user_id]
                if (now - call_time).total_seconds() < self.period
            ]
        else:
            self.call_times[user_id] = []

        # Check rate limit
        if len(self.call_times[user_id]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Add current call
        self.call_times[user_id].append(now)


# Common rate limiters
rate_limiter_strict = RateLimiter(calls=5, period=60)  # 5 calls per minute
rate_limiter_normal = RateLimiter(calls=30, period=60)  # 30 calls per minute
rate_limiter_relaxed = RateLimiter(calls=100, period=60)  # 100 calls per minute
