from telegram.validation import (
    sanitize_log_message,
    validate_market_id,
    validate_numeric_value,
    validate_param_name,
    validate_strategy_name,
)


class TestValidateStrategyName:
    def test_valid_names(self) -> None:
        assert validate_strategy_name("vegas_value") is True
        assert validate_strategy_name("smart-money") is True
        assert validate_strategy_name("Strategy123") is True

    def test_invalid_names(self) -> None:
        assert validate_strategy_name("") is False
        assert validate_strategy_name("a" * 100) is False  # Too long
        assert validate_strategy_name("name with spaces") is False
        assert validate_strategy_name("name@special") is False
        assert validate_strategy_name("<script>") is False


class TestValidateMarketId:
    def test_valid_ids(self) -> None:
        assert validate_market_id("market-123") is True
        assert validate_market_id("abc_def_ghi") is True
        assert validate_market_id("MarketID") is True

    def test_invalid_ids(self) -> None:
        assert validate_market_id("") is False
        assert validate_market_id("a" * 200) is False  # Too long
        assert validate_market_id("id with space") is False
        assert validate_market_id("../../../etc") is False


class TestValidateParamName:
    def test_valid_params(self) -> None:
        assert validate_param_name("max_order_size") is True
        assert validate_param_name("strategy.vegas") is True
        assert validate_param_name("limit123") is True

    def test_invalid_params(self) -> None:
        assert validate_param_name("") is False
        assert validate_param_name("param with space") is False
        assert validate_param_name("param@special") is False


class TestValidateNumericValue:
    def test_valid_values(self) -> None:
        assert validate_numeric_value("10.5") == 10.5
        assert validate_numeric_value("100") == 100.0
        assert validate_numeric_value("0") == 0.0

    def test_invalid_values(self) -> None:
        assert validate_numeric_value("abc") is None
        assert validate_numeric_value("-10") is None  # Below min
        assert validate_numeric_value("1e20") is None  # Above max

    def test_custom_bounds(self) -> None:
        assert validate_numeric_value("5", min_val=1.0, max_val=10.0) == 5.0
        assert validate_numeric_value("0", min_val=1.0, max_val=10.0) is None
        assert validate_numeric_value("15", min_val=1.0, max_val=10.0) is None


class TestSanitizeLogMessage:
    def test_normal_message(self) -> None:
        assert sanitize_log_message("Hello World") == "Hello World"

    def test_truncates_long_message(self) -> None:
        long_msg = "a" * 600
        result = sanitize_log_message(long_msg)
        assert len(result) == 503  # 500 + "..."
        assert result.endswith("...")

    def test_removes_control_characters(self) -> None:
        msg = "Hello\x00World\x1b[31m"
        result = sanitize_log_message(msg)
        assert "\x00" not in result
        assert "\x1b" not in result

    def test_preserves_whitespace(self) -> None:
        msg = "Hello\nWorld\tTest"
        result = sanitize_log_message(msg)
        assert "\n" in result
        assert "\t" in result
