"""Tests for session persistence, ownership checks and the demo-login flag."""

from __future__ import annotations

import os
from datetime import date
from unittest import mock

import pytest

from stock_cycle_tracker.domain.models import Stock
from stock_cycle_tracker.services.auth_service import AuthService
from stock_cycle_tracker.storage.db import DatabaseManager
from stock_cycle_tracker.storage.repository import StockCycleRepository
from stock_cycle_tracker.ui import session_auth


@pytest.fixture()
def repo() -> StockCycleRepository:
    return StockCycleRepository(DatabaseManager(":memory:"))


@pytest.fixture()
def auth(repo: StockCycleRepository) -> AuthService:
    return AuthService(repo)


@pytest.fixture(autouse=True)
def _wire_container(repo, auth):
    """Points the service locator at this test's in-memory database.

    `session_auth` resolves services through `ServiceContainer`, so the
    singleton has to be reset per test or the session rows land in a different
    database than the one the test asserts against.
    """
    from stock_cycle_tracker.ui.state import ServiceContainer

    container = ServiceContainer.__new__(ServiceContainer)
    container.db_manager = repo.db
    container.repository = repo
    container.auth_service = auth
    ServiceContainer.reset(container)
    yield
    ServiceContainer.reset(None)


def _make_user(auth: AuthService, username: str = "alice"):
    user, err = auth.signup(
        username=username,
        email=f"{username}@example.com",
        password="secret123",
        full_name=username.title(),
    )
    assert err is None, err
    return user


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


def test_session_token_resolves_to_its_user(repo, auth):
    user = _make_user(auth)
    token = session_auth.create_session(user)

    resolved = session_auth.user_for_token(token)
    assert resolved is not None
    assert resolved.id == user.id


def test_only_the_hash_is_stored(repo, auth):
    user = _make_user(auth)
    token = session_auth.create_session(user)

    with repo.db.get_connection() as conn:
        rows = conn.execute("SELECT token_hash FROM sessions").fetchall()

    stored = {r["token_hash"] for r in rows}
    # The raw token must never appear in the database.
    assert token not in stored
    assert session_auth._hash_token(token) in stored


def test_unknown_token_resolves_to_nothing(auth):
    _make_user(auth)
    assert session_auth.user_for_token("not-a-real-token") is None
    assert session_auth.user_for_token(None) is None


def test_destroyed_session_stops_working(repo, auth):
    user = _make_user(auth)
    token = session_auth.create_session(user)
    assert session_auth.user_for_token(token) is not None

    session_auth.destroy_session(token)
    assert session_auth.user_for_token(token) is None


def test_expired_session_is_rejected(repo, auth):
    user = _make_user(auth)
    # A session that expired an hour ago.
    token = "expired-token"
    repo.create_session(user.id, session_auth._hash_token(token), ttl_days=-1)

    assert session_auth.user_for_token(token) is None


def test_deleted_user_loses_access(repo, auth):
    user = _make_user(auth)
    token = session_auth.create_session(user)
    assert session_auth.user_for_token(token) is not None

    with repo.db.get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user.id,))
        conn.commit()

    # The session row cascades away with the user.
    assert session_auth.user_for_token(token) is None


def test_cookie_value_parsing():
    header = "other=1; sct_session=abc123; another=2"
    assert session_auth._cookie_value(header, "sct_session") == "abc123"
    assert session_auth._cookie_value(header, "missing") is None
    assert session_auth._cookie_value("", "sct_session") is None


# ---------------------------------------------------------------------------
# Ownership
# ---------------------------------------------------------------------------


def test_delete_stock_is_scoped_to_owner(repo, auth):
    alice = _make_user(auth, "alice")
    bob = _make_user(auth, "bob")

    stock = repo.create_or_get_stock(Stock(symbol="RELIANCE"), user_id=alice.id)

    # Bob cannot delete Alice's stock by guessing its id.
    assert repo.delete_stock(stock.id, user_id=bob.id) is False
    assert repo.get_stock("RELIANCE", user_id=alice.id) is not None

    # Alice can.
    assert repo.delete_stock(stock.id, user_id=alice.id) is True


def test_delete_cycle_is_scoped_to_owner(repo, auth):
    alice = _make_user(auth, "alice")
    bob = _make_user(auth, "bob")

    stock = repo.create_or_get_stock(Stock(symbol="TCS"), user_id=alice.id)
    cycle = repo.add_cycle(stock.id, date(2020, 1, 10), user_id=alice.id)

    assert repo.delete_cycle(cycle.id, user_id=bob.id) is False
    assert repo.delete_cycle(cycle.id, user_id=alice.id) is True


def test_list_all_cycles_only_returns_own_rows(repo, auth):
    alice = _make_user(auth, "alice")
    bob = _make_user(auth, "bob")

    a_stock = repo.create_or_get_stock(Stock(symbol="INFY"), user_id=alice.id)
    repo.add_cycle(a_stock.id, date(2019, 7, 15), user_id=alice.id)

    b_stock = repo.create_or_get_stock(Stock(symbol="HDFCBANK"), user_id=bob.id)
    repo.add_cycle(b_stock.id, date(2018, 4, 12), user_id=bob.id)

    alice_rows = repo.list_all_cycles(user_id=alice.id)
    assert [s.symbol for s, _ in alice_rows] == ["INFY"]


# ---------------------------------------------------------------------------
# Demo login
# ---------------------------------------------------------------------------


def test_demo_login_is_off_by_default():
    from stock_cycle_tracker.ui.app import demo_login_enabled

    with mock.patch.dict(os.environ, {}, clear=True):
        assert demo_login_enabled() is False


def test_demo_login_enabled_only_with_exact_flag():
    from stock_cycle_tracker.ui.app import demo_login_enabled

    for value, expected in [("1", True), ("0", False), ("true", False), ("", False)]:
        with mock.patch.dict(os.environ, {"ENABLE_DEMO_LOGIN": value}):
            assert demo_login_enabled() is expected, value


def test_demo_user_has_no_known_password(auth):
    """The demo account must not be reachable through the sign-in form."""
    user = auth.get_or_create_demo_user()
    assert user is not None

    # None of the obvious passwords work.
    for guess in ("investor123", "demo", "password", "demo123"):
        found, _ = auth.signin("demo", guess)
        assert found is None, f"demo account accepted {guess!r}"


def test_demo_user_is_reused(auth):
    first = auth.get_or_create_demo_user()
    second = auth.get_or_create_demo_user()
    assert first.id == second.id
