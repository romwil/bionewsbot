"""Configuration settings for the notification service."""

from typing import Dict, List, Optional
from pydantic import BaseSettings, Field, validator
from functools import lru_cache
import os


class SlackSettings(BaseSettings):
    """Slack-specific configuration."""
    
    bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    app_token: str = Field(..., env="SLACK_APP_TOKEN")
    signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    client_id: Optional[str] = Field(None, env="SLACK_CLIENT_ID")
    client_secret: Optional[str] = Field(None, env="SLACK_CLIENT_SECRET")
    
    # Channel mappings
    high_priority_channel: str = Field("#alerts", env="SLACK_HIGH_PRIORITY_CHANNEL")
    normal_priority_channel: str = Field("#updates", env="SLACK_NORMAL_PRIORITY_CHANNEL")
    
    # Channel mappings by insight type
    channel_mappings: Dict[str, str] = Field(
        default_factory=lambda: {
            "regulatory_approval": "#regulatory-alerts",
            "clinical_trial": "#clinical-updates",
            "merger_acquisition": "#ma-alerts",
            "funding_round": "#funding-news",
            "partnership": "#partnerships",
            "custom": "#general-alerts"
        }
    )
    
    class Config:
        env_prefix = "SLACK_"
        case_sensitive = False


class RedisSettings(BaseSettings):
    """Redis configuration for caching and rate limiting."""
    
    host: str = Field("localhost", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")
    password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    db: int = Field(0, env="REDIS_DB")
    
    # Rate limiting settings
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(10, env="RATE_LIMIT_BURST")
    
    @property
    def url(self) -> str:
        """Get Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    host: str = Field("localhost", env="DB_HOST")
    port: int = Field(5432, env="DB_PORT")
    name: str = Field("bionewsbot", env="DB_NAME")
    user: str = Field("postgres", env="DB_USER")
    password: str = Field(..., env="DB_PASSWORD")
    
    @property
    def url(self) -> str:
        """Get database connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    class Config:
        env_prefix = "DB_"


class APISettings(BaseSettings):
    """Backend API configuration."""
    
    base_url: str = Field("http://localhost:8000", env="API_BASE_URL")
    api_key: Optional[str] = Field(None, env="API_KEY")
    webhook_secret: Optional[str] = Field(None, env="WEBHOOK_SECRET")
    
    # Polling settings
    poll_interval_seconds: int = Field(30, env="POLL_INTERVAL_SECONDS")
    poll_batch_size: int = Field(10, env="POLL_BATCH_SIZE")
    
    class Config:
        env_prefix = "API_"


class NotificationSettings(BaseSettings):
    """General notification settings."""
    
    # Retry configuration
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay_seconds: int = Field(5, env="RETRY_DELAY_SECONDS")
    
    # Message formatting
    max_message_length: int = Field(3000, env="MAX_MESSAGE_LENGTH")
    include_preview_image: bool = Field(True, env="INCLUDE_PREVIEW_IMAGE")
    
    # Monitoring
    metrics_port: int = Field(9090, env="METRICS_PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_prefix = "NOTIFICATION_"


class Settings(BaseSettings):
    """Main settings aggregator."""
    
    # Service name
    service_name: str = Field("bionewsbot-notifications", env="SERVICE_NAME")
    environment: str = Field("development", env="ENVIRONMENT")
    
    # Sub-configurations
    slack: SlackSettings = Field(default_factory=SlackSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Example .env file content
EXAMPLE_ENV = """
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bionewsbot
DB_USER=postgres
DB_PASSWORD=your-db-password

# API Configuration
API_BASE_URL=http://localhost:8000
API_KEY=your-api-key
WEBHOOK_SECRET=your-webhook-secret

# Notification Settings
NOTIFICATION_LOG_LEVEL=INFO
NOTIFICATION_MAX_RETRIES=3
"""

if __name__ == "__main__":
    # Create example .env file if it doesn't exist
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.example")
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write(EXAMPLE_ENV)
        print(f"Created example .env file at {env_path}")
