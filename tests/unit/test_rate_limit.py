
from telegram.rate_limit import RateLimiter


class TestRateLimiter:
    def test_allows_first_request(self) -> None:
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.is_allowed(user_id=123) is True

    def test_allows_up_to_max_requests(self) -> None:
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.is_allowed(user_id=123) is True
        assert limiter.is_allowed(user_id=123) is True
        assert limiter.is_allowed(user_id=123) is True
        assert limiter.is_allowed(user_id=123) is False  # 4th request blocked

    def test_different_users_tracked_separately(self) -> None:
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed(user_id=1) is True
        assert limiter.is_allowed(user_id=1) is True
        assert limiter.is_allowed(user_id=1) is False

        # Different user should still be allowed
        assert limiter.is_allowed(user_id=2) is True

    def test_reset_clears_user_requests(self) -> None:
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed(user_id=123)
        limiter.is_allowed(user_id=123)
        assert limiter.is_allowed(user_id=123) is False

        limiter.reset(user_id=123)
        assert limiter.is_allowed(user_id=123) is True

    def test_remaining_returns_correct_count(self) -> None:
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.remaining(user_id=123) == 5

        limiter.is_allowed(user_id=123)
        assert limiter.remaining(user_id=123) == 4

        limiter.is_allowed(user_id=123)
        limiter.is_allowed(user_id=123)
        assert limiter.remaining(user_id=123) == 2
