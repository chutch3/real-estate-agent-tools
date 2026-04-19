import logging
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding-window rate limiter backed by Redis sorted sets.

    Fails open when Redis is unavailable so legitimate consumers are never
    locked out by an infrastructure issue.
    """

    def __init__(self, redis_client, max_requests: int, window_seconds: int) -> None:
        self._redis = redis_client
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    def is_allowed(self, key: str) -> bool:
        if self._redis is None:
            logger.warning("Rate limiter: Redis not configured — failing open for key=%s", key)
            return True
        try:
            now = int(time.time())
            window_start = now - self._window_seconds
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self._window_seconds + 1)
            results = pipe.execute()
            count = results[2]
            return count <= self._max_requests
        except Exception:
            logger.warning("Rate limiter: Redis error — failing open for key=%s", key)
            return True
