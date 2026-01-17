import pytest

from utils.retry import RetryError, retry


class TestRetry:
    def test_returns_on_first_success(self) -> None:
        call_count = 0

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = retry(operation, attempts=3)
        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure(self) -> None:
        call_count = 0

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "success"

        result = retry(operation, attempts=3, base_delay_s=0.01, jitter=False)
        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_attempts(self) -> None:
        call_count = 0

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")

        with pytest.raises(RetryError) as exc_info:
            retry(operation, attempts=3, base_delay_s=0.01, jitter=False)

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_error, ValueError)

    def test_respects_retryable_exceptions(self) -> None:
        call_count = 0

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("retryable")
            if call_count == 2:
                raise TypeError("not retryable")
            return "success"

        with pytest.raises(TypeError):
            retry(
                operation,
                attempts=3,
                base_delay_s=0.01,
                jitter=False,
                retryable_exceptions=(ValueError,),
            )

        assert call_count == 2

    def test_exponential_backoff(self) -> None:
        # Just verify it doesn't crash with exponential=True
        call_count = 0

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "success"

        result = retry(
            operation,
            attempts=3,
            base_delay_s=0.01,
            max_delay_s=1.0,
            exponential=True,
            jitter=False,
        )
        assert result == "success"

    def test_fixed_delay(self) -> None:
        call_count = 0

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "success"

        result = retry(
            operation,
            attempts=3,
            base_delay_s=0.01,
            exponential=False,
            jitter=False,
        )
        assert result == "success"


class TestRetryError:
    def test_error_attributes(self) -> None:
        original = ValueError("original error")
        error = RetryError("Failed", attempts=3, last_error=original)
        assert error.attempts == 3
        assert error.last_error is original
        assert "Failed" in str(error)
