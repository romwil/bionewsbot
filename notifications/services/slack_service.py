"""Slack service for sending notifications using Bolt SDK."""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import structlog
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config.settings import get_settings, SlackSettings
from ..models.notification import (
    Insight, NotificationHistory, NotificationStatus, 
    SlackAction, SlackInteraction, Priority
)
from ..templates.slack_messages import SlackMessageTemplates
from ..utils.rate_limiter import RateLimiter
from ..utils.metrics import MetricsCollector


logger = structlog.get_logger(__name__)


class SlackService:
    """Main Slack service for sending notifications."""
    
    def __init__(self, settings: Optional[SlackSettings] = None):
        self.settings = settings or get_settings().slack
        self.templates = SlackMessageTemplates()
        self.metrics = MetricsCollector()
        
        # Initialize Slack app
        self.app = AsyncApp(
            token=self.settings.bot_token,
            signing_secret=self.settings.signing_secret
        )
        
        # Socket mode handler for real-time events
        self.socket_handler = AsyncSocketModeHandler(
            self.app,
            self.settings.app_token
        )
        
        # Web client for API calls
        self.client = self.app.client
        
        # Redis for caching and rate limiting
        self.redis_client: Optional[redis.Redis] = None
        self.rate_limiter: Optional[RateLimiter] = None
        
        # Register event handlers
        self._register_handlers()
        
        # Callback handlers
        self.action_handlers: Dict[str, Callable] = {}
        
    async def initialize(self):
        """Initialize async resources."""
        # Initialize Redis
        redis_settings = get_settings().redis
        self.redis_client = await redis.from_url(
            redis_settings.url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            self.redis_client,
            rate_limit=redis_settings.rate_limit_per_minute,
            burst=redis_settings.rate_limit_burst
        )
        
        logger.info("Slack service initialized")
    
    async def start(self):
        """Start the Slack service."""
        await self.initialize()
        await self.socket_handler.start_async()
        logger.info("Slack service started")
    
    async def stop(self):
        """Stop the Slack service."""
        await self.socket_handler.close_async()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Slack service stopped")
    
    def _register_handlers(self):
        """Register Slack event handlers."""
        # Button actions
        @self.app.action("mark_reviewed")
        async def handle_mark_reviewed(ack, body, action):
            await ack()
            await self._handle_action("mark_reviewed", body, action)
        
        @self.app.action("view_details")
        async def handle_view_details(ack, body, action):
            await ack()
            await self._handle_action("view_details", body, action)
        
        # OAuth flow
        @self.app.event("app_home_opened")
        async def handle_app_home_opened(event, client):
            await self._update_home_tab(event["user"], client)
    
    async def _handle_action(self, action_id: str, body: Dict, action: Dict):
        """Handle interactive actions."""
        try:
            # Extract action data
            slack_action = SlackAction(
                action_id=action_id,
                action_type=action.get("type", "button"),
                value=action.get("value"),
                user_id=body["user"]["id"],
                user_name=body["user"]["username"],
                channel_id=body["channel"]["id"],
                message_ts=body["message"]["ts"],
                response_url=body.get("response_url")
            )
            
            # Call registered handler if exists
            if action_id in self.action_handlers:
                await self.action_handlers[action_id](slack_action)
            
            # Update metrics
            self.metrics.increment("slack_actions_total", labels={"action": action_id})
            
        except Exception as e:
            logger.error("Error handling action", action_id=action_id, error=str(e))
    
    def register_action_handler(self, action_id: str, handler: Callable):
        """Register a custom action handler."""
        self.action_handlers[action_id] = handler
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(SlackApiError)
    )
    async def send_notification(
        self, 
        insight: Insight, 
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> NotificationHistory:
        """Send a notification to Slack."""
        start_time = datetime.utcnow()
        
        # Determine channel
        if not channel:
            channel = self._get_channel_for_insight(insight)
        
        # Check rate limit
        if self.rate_limiter:
            allowed = await self.rate_limiter.check_rate_limit(channel)
            if not allowed:
                raise Exception("Rate limit exceeded for channel")
        
        # Generate message
        message = self.templates.generate_message(insight)
        
        # Create notification history record
        notification = NotificationHistory(
            insight_id=insight.id,
            channel=channel,
            thread_ts=thread_ts,
            status=NotificationStatus.PENDING
        )
        
        try:
            # Send message
            response = await self.client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                **message
            )
            
            # Update notification with response
            notification.message_ts = response["ts"]
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            # Send thread reply with details for high priority
            if insight.priority in [Priority.HIGH, Priority.CRITICAL] and not thread_ts:
                thread_message = self.templates.generate_thread_reply(insight)
                await self.client.chat_postMessage(
                    channel=channel,
                    thread_ts=response["ts"],
                    **thread_message
                )
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.observe("slack_send_duration_seconds", duration)
            self.metrics.increment("slack_notifications_sent_total", 
                                 labels={"channel": channel, "type": insight.type.value})
            
            logger.info(
                "Notification sent successfully",
                insight_id=insight.id,
                channel=channel,
                message_ts=notification.message_ts
            )
            
        except SlackApiError as e:
            notification.status = NotificationStatus.FAILED
            notification.last_error = str(e)
            notification.attempts += 1
            
            self.metrics.increment("slack_notifications_failed_total", 
                                 labels={"channel": channel, "error": e.response["error"]})
            
            logger.error(
                "Failed to send notification",
                insight_id=insight.id,
                channel=channel,
                error=str(e)
            )
            raise
        
        return notification
    
    def _get_channel_for_insight(self, insight: Insight) -> str:
        """Determine the appropriate channel for an insight."""
        # Check type-specific mapping first
        if insight.type.value in self.settings.channel_mappings:
            return self.settings.channel_mappings[insight.type.value]
        
        # Fall back to priority-based routing
        if insight.priority in [Priority.HIGH, Priority.CRITICAL]:
            return self.settings.high_priority_channel
        else:
            return self.settings.normal_priority_channel
    
    async def update_notification_status(
        self,
        notification_id: str,
        status: NotificationStatus,
        user_id: Optional[str] = None
    ):
        """Update the status of a notification."""
        # This would typically update the database
        # For now, just log and update metrics
        logger.info(
            "Updating notification status",
            notification_id=notification_id,
            status=status.value,
            user_id=user_id
        )
        
        if status == NotificationStatus.READ and user_id:
            self.metrics.increment("slack_notifications_read_total")
        elif status == NotificationStatus.ACKNOWLEDGED and user_id:
            self.metrics.increment("slack_notifications_acknowledged_total")
    
    async def get_channel_list(self) -> List[Dict[str, str]]:
        """Get list of available Slack channels."""
        try:
            response = await self.client.conversations_list(
                types="public_channel,private_channel"
            )
            
            channels = []
            for channel in response["channels"]:
                if not channel.get("is_archived", False):
                    channels.append({
                        "id": channel["id"],
                        "name": channel["name"],
                        "is_private": channel.get("is_private", False)
                    })
            
            return channels
            
        except SlackApiError as e:
            logger.error("Failed to get channel list", error=str(e))
            return []
    
    async def _update_home_tab(self, user_id: str, client: AsyncWebClient):
        """Update the app home tab for a user."""
        try:
            # Build home tab view
            view = {
                "type": "home",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🧬 BioNewsBot Notifications"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Welcome to BioNewsBot! I'll keep you updated on the latest life sciences intelligence."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Notification Channels:*\n" +
                                   f"• High Priority: {self.settings.high_priority_channel}\n" +
                                   f"• Normal Priority: {self.settings.normal_priority_channel}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Configure Channels"
                                },
                                "action_id": "configure_channels"
                            }
                        ]
                    }
                ]
            }
            
            await client.views_publish(user_id=user_id, view=view)
            
        except SlackApiError as e:
            logger.error("Failed to update home tab", user_id=user_id, error=str(e))


# Singleton instance
_slack_service: Optional[SlackService] = None


async def get_slack_service() -> SlackService:
    """Get or create the Slack service singleton."""
    global _slack_service
    if _slack_service is None:
        _slack_service = SlackService()
        await _slack_service.initialize()
    return _slack_service
