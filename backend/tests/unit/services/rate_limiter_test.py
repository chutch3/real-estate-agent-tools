from unittest.mock import MagicMock

import pytest

from backend.services.rate_limiter import RateLimiter


class TestRateLimiter:
    @pytest.fixture
    def redis_client(self):
        client = MagicMock()
        pipe = MagicMock()
        client.pipeline.return_value = pipe
        pipe.__enter__ = MagicMock(return_value=pipe)
        pipe.__exit__ = MagicMock(return_value=False)
        return client, pipe

    @pytest.fixture
    def subject(self, redis_client):
        client, _ = redis_client
        return RateLimiter(redis_client=client, max_requests=5, window_seconds=60)

    def test_allows_request_when_under_limit(self, subject, redis_client):
        _, pipe = redis_client
        pipe.execute.return_value = [None, None, 3, None]

        assert subject.is_allowed("magic_session:1.2.3.4") is True

    def test_allows_request_at_exact_limit(self, subject, redis_client):
        _, pipe = redis_client
        pipe.execute.return_value = [None, None, 5, None]

        assert subject.is_allowed("magic_session:1.2.3.4") is True

    def test_blocks_request_when_over_limit(self, subject, redis_client):
        _, pipe = redis_client
        pipe.execute.return_value = [None, None, 6, None]

        assert subject.is_allowed("magic_session:1.2.3.4") is False

    def test_fails_open_when_redis_raises(self, subject, redis_client):
        client, _ = redis_client
        client.pipeline.side_effect = Exception("connection refused")

        assert subject.is_allowed("magic_session:1.2.3.4") is True

    def test_fails_open_when_redis_is_none(self):
        limiter = RateLimiter(redis_client=None, max_requests=5, window_seconds=60)

        assert limiter.is_allowed("magic_session:1.2.3.4") is True

    def test_uses_sliding_window_key(self, subject, redis_client):
        _, pipe = redis_client
        pipe.execute.return_value = [None, None, 1, None]

        subject.is_allowed("magic_session:10.0.0.1")

        pipe.zremrangebyscore.assert_called_once()
        pipe.zadd.assert_called_once()
        call_key = pipe.zremrangebyscore.call_args[0][0]
        assert call_key == "magic_session:10.0.0.1"
