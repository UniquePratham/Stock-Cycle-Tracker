"""Authentication and user profile service with secure PBKDF2 password hashing."""

from __future__ import annotations

import hashlib
import re
import secrets
from typing import List, Optional, Tuple

from stock_cycle_tracker.domain.user import AVAILABLE_AVATARS, AvatarInfo, User, get_avatar
from stock_cycle_tracker.storage.repository import StockCycleRepository


class AuthService:
    """Handles user registration, authentication, session security, and profile updates."""

    def __init__(self, repository: StockCycleRepository) -> None:
        self.repo = repository

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Derives a secure password hash using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        )
        return key.hex()

    def get_available_avatars(self) -> List[AvatarInfo]:
        """Returns the list of curated trader avatars."""
        return AVAILABLE_AVATARS

    def signup(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = "",
        avatar_id: str = "bull_trader",
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Registers a new user account.
        Returns (User, None) on success or (None, error_message) on failure.
        """
        u = username.strip()
        e = email.strip().lower()
        p = password.strip()
        name = full_name.strip() or u

        # Validations
        if not u or len(u) < 3:
            return None, "Username must be at least 3 characters long."
        if not re.match(r"^[a-zA-Z0-9_-]+$", u):
            return None, "Username can only contain letters, numbers, hyphens, and underscores."
        if not e or not re.match(r"^[^@]+@[^@]+\.[^@]+$", e):
            return None, "Please provide a valid email address."
        if not p or len(p) < 6:
            return None, "Password must be at least 6 characters long."

        # Check existing username
        if self.repo.get_user_by_username(u):
            return None, f"Username '{u}' is already taken. Please choose another."

        # Check existing email
        if self.repo.get_user_by_email(e):
            return None, f"An account with email '{e}' already exists."

        # Generate salt & hash password
        salt = secrets.token_hex(16)
        pwd_hash = self._hash_password(p, salt)

        user = User(
            username=u,
            email=e,
            password_hash=pwd_hash,
            salt=salt,
            full_name=name,
            avatar_id=avatar_id if avatar_id in [a.id for a in AVAILABLE_AVATARS] else "bull_trader",
        )

        created_user = self.repo.create_user(user)
        return created_user, None

    def signin(
        self,
        identifier: str,
        password: str,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticates a user via username or email.
        Returns (User, None) on success or (None, error_message) on failure.
        """
        ident = identifier.strip()
        p = password.strip()

        if not ident:
            return None, "Please enter your username or email."
        if not p:
            return None, "Please enter your password."

        # Find user by email or username
        user: Optional[User] = None
        if "@" in ident:
            user = self.repo.get_user_by_email(ident)
        else:
            user = self.repo.get_user_by_username(ident)

        if not user:
            return None, "Account not found. Please check your credentials or Sign Up."

        # Verify hash
        expected_hash = self._hash_password(p, user.salt)
        if not secrets.compare_digest(user.password_hash, expected_hash):
            return None, "Invalid password. Please try again."

        return user, None

    def update_profile(
        self,
        user_id: int,
        full_name: str,
        avatar_id: str,
    ) -> bool:
        """Updates user display name and avatar selection."""
        return self.repo.update_user_profile(user_id, full_name, avatar_id)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves user profile by ID."""
        return self.repo.get_user_by_id(user_id)
