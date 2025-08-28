"""Rate limiting utilities for Slack API calls."""

import asyncio
from typing import Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
import structlog


logger = structlog.get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        rate_limit: int = 60,  # requests per minute
        burst: int = 10,  # burst capacity
        prefix: str = "ratelimit"
    ):
        self.redis = redis_client
        self.rate_limit = rate_limit
        self.burst = burst
        self.prefix = prefix
        self.refill_rate = rate_limit / 60.0  # tokens per second
    
    async def check_rate_limit(self, key: str) -> bool:
        """Check if request is allowed under rate limit."""
        bucket_key = f"{self.prefix}:{key}"
        now = datetime.utcnow().timestamp()
        
        # Lua script for atomic token bucket operation
        lua_script = """
        local key = KEYS[1]
        local rate_limit = tonumber(ARGV[1])
        local burst = tonumber(ARGV[2])
        local refill_rate = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        local cost = tonumber(ARGV[5])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or burst
        local last_refill = tonumber(bucket[2]) or now
        
        -- Calculate tokens to add based on time passed
        local time_passed = now - last_refill
        local new_tokens = tokens + (time_passed * refill_rate)
        if new_tokens > burst then
            new_tokens = burst
        end
        
        -- Check if we have enough tokens
        if new_tokens >= cost then
            new_tokens = new_tokens - cost
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 300)  -- 5 minute expiry
            return 1
        else
            -- Not enough tokens, just update the refill time
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 300)
            return 0
        end
        """
        
        try:
            # Register script if not already done
            if not hasattr(self, '_script_sha'):
                self._script_sha = await self.redis.script_load(lua_script)
            
            # Execute script
            result = await self.redis.evalsha(
                self._script_sha,
                keys=[bucket_key],
                args=[self.rate_limit, self.burst, self.refill_rate, now, 1]
            )
            
            allowed = bool(result)
            
            if not allowed:
                logger.warning(
                    "Rate limit exceeded",
                    key=key,
                    rate_limit=self.rate_limit
                )
            
            return allowed
            
        except redis.NoScriptError:
            # Script not in cache, reload it
            self._script_sha = await self.redis.script_load(lua_script)
            return await self.check_rate_limit(key)
        
        except Exception as e:
            logger.error("Rate limiter error", error=str(e))
            # Fail open - allow request if rate limiter fails
            return True
    
    async def get_remaining_tokens(self, key: str) -> float:
        """Get remaining tokens for a key."""
        bucket_key = f"{self.prefix}:{key}"
        now = datetime.utcnow().timestamp()
        
        try:
            bucket = await self.redis.hmget(bucket_key, 'tokens', 'last_refill')
            tokens = float(bucket[0]) if bucket[0] else self.burst
            last_refill = float(bucket[1]) if bucket[1] else now
            
            # Calculate current tokens
            time_passed = now - last_refill
            current_tokens = min(tokens + (time_passed * self.refill_rate), self.burst)
            
            return current_tokens
            
        except Exception as e:
            logger.error("Error getting remaining tokens", error=str(e))
            return self.burst
    
    async def reset_limit(self, key: str):
        """Reset rate limit for a key."""
        bucket_key = f"{self.prefix}:{key}"
        try:
            await self.redis.delete(bucket_key)
            logger.info("Rate limit reset", key=key)
        except Exception as e:
            logger.error("Error resetting rate limit", error=str(e))


class ChannelRateLimiter:
    """Specialized rate limiter for Slack channels with different limits."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
        # Different rate limits for different channel types
        self.limiters = {
            "high_priority": RateLimiter(
                redis_client,
                rate_limit=120,  # 2 per second for urgent alerts
                burst=20,
                prefix="slack:high"
            ),
            "normal": RateLimiter(
                redis_client,
                rate_limit=60,  # 1 per second for normal
                burst=10,
                prefix="slack:normal"
            ),
            "default": RateLimiter(
                redis_client,
                rate_limit=30,  # 0.5 per second default
                burst=5,
                prefix="slack:default"
            )
        }
    
    def _get_channel_type(self, channel: str) -> str:
        """Determine channel type based on name."""
        if channel in ["#alerts", "#critical-alerts", "#regulatory-alerts"]:
            return "high_priority"
        elif channel in ["#updates", "#clinical-updates", "#funding-news"]:
            return "normal"
        else:
            return "default"
    
    async def check_rate_limit(self, channel: str) -> bool:
        """Check rate limit for a specific channel."""
        channel_type = self._get_channel_type(channel)
        limiter = self.limiters[channel_type]
        return await limiter.check_rate_limit(channel)
    
    async def get_remaining_tokens(self, channel: str) -> float:
        """Get remaining tokens for a channel."""
        channel_type = self._get_channel_type(channel)
        limiter = self.limiters[channel_type]
        return await limiter.get_remaining_tokens(channel)
