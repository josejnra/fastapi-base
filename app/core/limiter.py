import hashlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from fastapi import Request, status
from fastapi.responses import ORJSONResponse, Response
from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.core.logger import logger
from app.core.telemetry import tracer

F = Callable[..., Awaitable[Any]]
# slowapi limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["2/5seconds"])


class IRateLimiter(Protocol):
    async def is_rate_limited(self, user: str) -> ORJSONResponse | None: ...


class RedisUserRateLimiter(IRateLimiter):
    def __init__(self, redis_client: Redis, rate_limit_per_minute: int):
        self.redis_client = redis_client
        self.rate_limit = rate_limit_per_minute

    @tracer.start_as_current_span("middleware - checking user rate limit")
    async def is_rate_limited(self, user: str) -> ORJSONResponse | None:
        """
        Checks if a user has exceeded their allowed number of requests per minute.

        This method applies rate limiting on a per-user, per-minute basis using Redis as a backend.
        It increments a counter for the user for the current minute and sets an expiration for the key.
        If the user exceeds the configured rate limit, an HTTP 429 response is returned.

        Args:
            user (str): The unique identifier for the user (e.g., username or user ID).

        Returns:
            ORJSONResponse | None: Returns an ORJSONResponse with HTTP 429 status if the rate limit is exceeded,
            otherwise returns None.

        Raises:
            None

        Side Effects:
            Increments a Redis key for the user and sets an expiration if the key is new.
        """
        # Increment our most recent redis key
        username_hash = hashlib.sha256(user.encode("utf-8")).hexdigest()
        now = datetime.now(UTC)
        current_minute = now.strftime("%Y-%m-%dT%H:%M")
        # Use a key that combines the username hash and the current minute
        # This way, we can track the number of requests per user per minute
        redis_key = f"rate_limit_{username_hash}_{current_minute}"
        current_count = await self.redis_client.incr(redis_key)

        logger.debug(f"rate_limit_user: {user} current_count: {current_count}")
        # If we just created a new key (count is 1) set an expiration
        if current_count == 1:
            logger.debug(f"rate_limit_user {user} setting expiration")
            await self.redis_client.expireat(
                name=redis_key, when=now + timedelta(minutes=1)
            )

        # Check rate limit
        if current_count > self.rate_limit:
            return ORJSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "User Rate Limit Exceeded"},
                headers={
                    "Retry-After": f"{60 - now.second}",
                    "X-Rate-Limit": f"{self.rate_limit}",
                },
            )
        return None


# TODO: implement middleware based on Pure ASGI Midleware, better performance
# https://www.starlette.io/middleware/#pure-asgi-middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        rate_limiter_factory: Callable[[], Awaitable[IRateLimiter]],
    ) -> None:
        super().__init__(app)
        self._rate_limiter_factory = rate_limiter_factory
        self._rate_limiter: IRateLimiter | None = None

    @tracer.start_as_current_span("middleware - redis rate limit")
    async def dispatch(self, request: Request, call_next: F) -> Response:
        """
        Handles incoming HTTP requests and applies rate limiting based on user identity.
        Args:
            request (Request): The incoming HTTP request object.
            call_next (F): The next middleware or route handler to call.
        Returns:
            Response: The HTTP response, either a rate limit response if the user is rate limited,
                      or the result of the next handler in the middleware chain.
        Raises:
            None
        Notes:
            - The user is identified via the "x-user" header in the request.
            - If the rate limiter instance is not initialized, it will be created using the provided factory.
            - If the user exceeds the allowed rate limit, an appropriate response is returned immediately.
            - Otherwise, the request is passed to the next handler.
        """

        if self._rate_limiter is None:
            logger.debug("creating rate limiter instance")
            self._rate_limiter = await self._rate_limiter_factory()

        user = request.headers.get("x-user")
        if user and self._rate_limiter:
            rate_limit_response = await self._rate_limiter.is_rate_limited(user)
            if rate_limit_response:
                return rate_limit_response

        return await call_next(request)


async def redis_user_rate_limiter_factory() -> IRateLimiter:
    logger.debug("creating redis client")
    # TODO: not really async, need to find a way to do it
    # aioredis is only supported until python 3.10
    # https://aioredis.readthedocs.io/en/latest/
    redis_client = await Redis.from_url(get_settings().REDIS_URL)
    return RedisUserRateLimiter(
        redis_client=redis_client,
        rate_limit_per_minute=get_settings().RATE_LIMIT,
    )
