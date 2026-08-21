"""Unit tests for AuthService, PBKDF2 hashing, user avatars, and local storage isolation."""

from datetime import date
import pytest

from stock_cycle_tracker.domain.models import Stock
from stock_cycle_tracker.domain.user import AVAILABLE_AVATARS, User
from stock_cycle_tracker.services.auth_service import AuthService
from stock_cycle_tracker.storage.db import DatabaseManager
from stock_cycle_tracker.storage.repository import StockCycleRepository


@pytest.fixture
def repo():
    db = DatabaseManager(":memory:")
    return StockCycleRepository(db)


@pytest.fixture
def auth_service(repo):
    return AuthService(repo)


def test_signup_success(auth_service):
    user, error = auth_service.signup(
        username="trader_pro",
        email="trader@cycles.com",
        password="securepassword123",
        full_name="Alex Mercer",
        avatar_id="cycle_master",
    )
    assert error is None
    assert user is not None
    assert user.id is not None
    assert user.username == "trader_pro"
    assert user.email == "trader@cycles.com"
    assert user.full_name == "Alex Mercer"
    assert user.avatar.id == "cycle_master"
    assert user.avatar.name == "Cycle Master"
    assert len(user.password_hash) > 20
    assert len(user.salt) > 10


def test_signup_validation_errors(auth_service):
    # Short username
    _, err = auth_service.signup("ab", "valid@email.com", "password123")
    assert "at least 3 characters" in err

    # Invalid email
    _, err = auth_service.signup("valid_user", "invalid-email", "password123")
    assert "valid email" in err

    # Short password
    _, err = auth_service.signup("valid_user", "valid@email.com", "123")
    assert "at least 6 characters" in err


def test_signup_duplicate_username_and_email(auth_service):
    auth_service.signup("alpha_trader", "alpha@test.com", "password123")

    # Duplicate username
    _, err = auth_service.signup("alpha_trader", "different@test.com", "password123")
    assert "already taken" in err

    # Duplicate email
    _, err = auth_service.signup("beta_trader", "alpha@test.com", "password123")
    assert "already exists" in err


def test_signin_with_username_and_email(auth_service):
    auth_service.signup(
        username="momentum_rider",
        email="momentum@trade.in",
        password="correctpassword",
        full_name="Rider",
        avatar_id="bull_trader",
    )

    # Sign in with username
    user1, err1 = auth_service.signin("momentum_rider", "correctpassword")
    assert err1 is None
    assert user1 is not None
    assert user1.username == "momentum_rider"

    # Sign in with email
    user2, err2 = auth_service.signin("momentum@trade.in", "correctpassword")
    assert err2 is None
    assert user2 is not None
    assert user2.email == "momentum@trade.in"

    # Wrong password
    _, err3 = auth_service.signin("momentum_rider", "wrongpassword")
    assert "Invalid password" in err3

    # Non-existent user
    _, err4 = auth_service.signin("ghost_user", "password123")
    assert "Account not found" in err4


def test_user_profile_update(auth_service):
    user, _ = auth_service.signup("quant_dev", "quant@test.com", "password123")
    assert user is not None

    success = auth_service.update_profile(user.id, "Dr. Quant", "quantum_analyst")
    assert success is True

    updated_user = auth_service.get_user_by_id(user.id)
    assert updated_user.full_name == "Dr. Quant"
    assert updated_user.avatar.id == "quantum_analyst"
    assert updated_user.avatar.role == "Quantitative Models"


def test_user_scoped_data_isolation(repo, auth_service):
    user1, _ = auth_service.signup("user_one", "u1@test.com", "pass12345")
    user2, _ = auth_service.signup("user_two", "u2@test.com", "pass12345")

    # User 1 adds Reliance
    stk1 = repo.create_or_get_stock(Stock(symbol="RELIANCE", company_name="Reliance Industries"), user_id=user1.id)
    cyc1 = repo.add_cycle(stk1.id, date(2020, 9, 18), user_id=user1.id)

    # User 2 adds TCS
    stk2 = repo.create_or_get_stock(Stock(symbol="TCS", company_name="Tata Consultancy Services"), user_id=user2.id)
    cyc2 = repo.add_cycle(stk2.id, date(2021, 5, 10), user_id=user2.id)

    # User 1's stocks and cycles
    u1_stocks = repo.list_stocks(user_id=user1.id)
    u1_cycles = repo.list_all_cycles(user_id=user1.id)
    assert any(s.symbol == "RELIANCE" for s in u1_stocks)
    assert any(s.symbol == "RELIANCE" for s, _ in u1_cycles)

    # User 2's stocks and cycles
    u2_stocks = repo.list_stocks(user_id=user2.id)
    u2_cycles = repo.list_all_cycles(user_id=user2.id)
    assert any(s.symbol == "TCS" for s in u2_stocks)
    assert any(s.symbol == "TCS" for s, _ in u2_cycles)
