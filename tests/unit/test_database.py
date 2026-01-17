import os
import tempfile

import pytest

from storage.db import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = Database(db_path)
    yield db
    db.close()
    os.unlink(db_path)


class TestDatabaseRiskState:
    def test_trading_disabled_by_default(self, temp_db: Database) -> None:
        assert temp_db.get_trading_enabled() is False

    def test_set_trading_enabled(self, temp_db: Database) -> None:
        temp_db.set_trading_enabled(True)
        assert temp_db.get_trading_enabled() is True

        temp_db.set_trading_enabled(False)
        assert temp_db.get_trading_enabled() is False

    def test_paper_mode_on_by_default(self, temp_db: Database) -> None:
        assert temp_db.get_paper_mode() is True

    def test_set_paper_mode(self, temp_db: Database) -> None:
        temp_db.set_paper_mode(False)
        assert temp_db.get_paper_mode() is False


class TestDatabaseIdempotency:
    def test_new_key_not_found(self, temp_db: Database) -> None:
        assert temp_db.check_idempotency_key("new-key") is False

    def test_added_key_is_found(self, temp_db: Database) -> None:
        temp_db.add_idempotency_key("my-key")
        assert temp_db.check_idempotency_key("my-key") is True

    def test_different_keys_tracked_separately(self, temp_db: Database) -> None:
        temp_db.add_idempotency_key("key-1")
        assert temp_db.check_idempotency_key("key-1") is True
        assert temp_db.check_idempotency_key("key-2") is False


class TestDatabaseOrders:
    def test_no_open_orders_initially(self, temp_db: Database) -> None:
        orders = temp_db.get_open_orders()
        assert orders == []

    def test_save_and_retrieve_order(self, temp_db: Database) -> None:
        temp_db.save_order(
            order_id="order-1",
            market_id="market-1",
            outcome_id="yes",
            side="buy",
            price=0.55,
            size=10.0,
            status="paper",
            strategy="test_strategy",
        )
        orders = temp_db.get_open_orders()
        assert len(orders) == 1
        assert orders[0]["order_id"] == "order-1"
        assert orders[0]["price"] == 0.55

    def test_update_order_status(self, temp_db: Database) -> None:
        temp_db.save_order(
            order_id="order-1",
            market_id="market-1",
            outcome_id="yes",
            side="buy",
            price=0.55,
            size=10.0,
            status="submitted",
        )
        temp_db.update_order_status("order-1", "filled")
        # Filled orders are not in "open" orders
        orders = temp_db.get_open_orders()
        assert len(orders) == 0

    def test_count_open_positions(self, temp_db: Database) -> None:
        assert temp_db.count_open_positions() == 0

        temp_db.save_order(
            order_id="order-1",
            market_id="market-1",
            outcome_id="yes",
            side="buy",
            price=0.55,
            size=10.0,
            status="paper",
        )
        assert temp_db.count_open_positions() == 1


class TestDatabaseAuditLog:
    def test_log_action(self, temp_db: Database) -> None:
        temp_db.log_action(
            actor_id="user-123",
            action="trade_toggle",
            details="enabled=true",
            correlation_id="corr-456",
        )
        # No exception means success (we don't have a getter for simplicity)


class TestDatabaseStrategyState:
    def test_strategy_enabled_by_default(self, temp_db: Database) -> None:
        assert temp_db.get_strategy_enabled("unknown_strategy") is True

    def test_set_strategy_disabled(self, temp_db: Database) -> None:
        temp_db.set_strategy_enabled("vegas_value", False)
        assert temp_db.get_strategy_enabled("vegas_value") is False

    def test_set_strategy_enabled(self, temp_db: Database) -> None:
        temp_db.set_strategy_enabled("vegas_value", False)
        temp_db.set_strategy_enabled("vegas_value", True)
        assert temp_db.get_strategy_enabled("vegas_value") is True


class TestDatabaseWatchlist:
    def test_empty_watchlist_initially(self, temp_db: Database) -> None:
        watchlist = temp_db.get_watchlist()
        assert watchlist == set()

    def test_add_to_watchlist(self, temp_db: Database) -> None:
        temp_db.add_to_watchlist("market-1")
        temp_db.add_to_watchlist("market-2")
        watchlist = temp_db.get_watchlist()
        assert watchlist == {"market-1", "market-2"}

    def test_remove_from_watchlist(self, temp_db: Database) -> None:
        temp_db.add_to_watchlist("market-1")
        temp_db.add_to_watchlist("market-2")
        temp_db.remove_from_watchlist("market-1")
        watchlist = temp_db.get_watchlist()
        assert watchlist == {"market-2"}


class TestDatabaseDailyPnl:
    def test_default_pnl_is_zero(self, temp_db: Database) -> None:
        pnl = temp_db.get_daily_pnl()
        assert pnl == 0.0

    def test_update_daily_pnl(self, temp_db: Database) -> None:
        temp_db.update_daily_pnl(realized=50.0, unrealized=25.0)
        pnl = temp_db.get_daily_pnl()
        assert pnl == 75.0
