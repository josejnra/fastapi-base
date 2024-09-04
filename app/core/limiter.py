import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, TypeVar, cast

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response
from redis.asyncio import Redis, from_url
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logger import logger
from app.core.telemetry import tracer

F = TypeVar("F", bound=Callable[..., Any])
# slowapi limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["2/5seconds"])


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, rate_limit_per_minute: int) -> None:
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.redis_client: Redis | None = None

    @tracer.start_as_current_span("middleware - redis rate limit")
    async def dispatch(self, request: Request, call_next: F) -> Response:
        """
        Rate limit requests per user
        """
        if self.redis_client is None:
            logger.debug("creating redis client")
            # TODO: not really async, need to find a way to do it
            # aioredis is only supported until python 3.10
            self.redis_client = await from_url(get_settings().REDIS_URL)

        user = request.headers.get("x-user")
        if user:
            rate_limit_exceeded_response = await self.rate_limit_user(
                user=user, rate_limit=self.rate_limit
            )
            if rate_limit_exceeded_response:
                return rate_limit_exceeded_response

        return await call_next(request)

    @tracer.start_as_current_span("middleware - checking user rate limit")
    async def rate_limit_user(self, user: str, rate_limit: int) -> JSONResponse | None:
        """
        Apply rate limiting per user, per minute
        """
        # Increment our most recent redis key
        username_hash = hashlib.sha256(bytes(user, "utf-8")).hexdigest()
        now = datetime.now(UTC)
        current_minute = now.strftime("%Y-%m-%dT%H:%M")

        redis_key = f"rate_limit_{username_hash}_{current_minute}"
        current_count = await cast(Redis, self.redis_client).incr(redis_key)

        logger.debug(f"rate_limit_user: {user} current_count: {current_count}")
        # If we just created a new key (count is 1) set an expiration
        if current_count == 1:
            logger.debug(f"rate_limit_user {user} setting expiration")
            await cast(Redis, self.redis_client).expireat(
                name=redis_key, when=now + timedelta(minutes=1)
            )

        # Check rate limit
        if current_count > rate_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "User Rate Limit Exceeded"},
                headers={
                    "Retry-After": f"{60 - now.second}",
                    "X-Rate-Limit": f"{rate_limit}",
                },
            )

        return None
