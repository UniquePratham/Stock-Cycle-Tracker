"""Session-backed authentication.

The signed-in user is identified by an **httponly** cookie, which the page's own
JavaScript cannot read. The cookie holds an opaque session token; the server
keeps only a SHA-256 hash of that token, so a leaked database row cannot be
replayed as a login.

The previous build kept the user in component state, so a reload or a new tab
dropped the login. This module is what makes the login survive both.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Optional

import rio

from stock_cycle_tracker.domain.user import User
from stock_cycle_tracker.ui.state import ServiceContainer

# Name of the httponly cookie carrying the opaque session token.
SESSION_COOKIE = "sct_session"

# How long a session stays valid.
SESSION_TTL_DAYS = 30


def _hash_token(token: str) -> str:
    """Returns the SHA-256 hex digest of a session token.

    Only this hash is stored, so the raw token exists solely in the user's
    cookie.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user: User) -> str:
    """Creates a session row for `user` and returns the raw token.

    The caller is responsible for putting the token into an httponly cookie.
    """
    container = ServiceContainer.get()
    token = secrets.token_urlsafe(32)
    container.repository.create_session(
        user_id=user.id,
        token_hash=_hash_token(token),
        ttl_days=SESSION_TTL_DAYS,
    )
    return token


def user_for_token(token: Optional[str]) -> Optional[User]:
    """Resolves a raw session token to its user, or None if invalid/expired."""
    if not token:
        return None

    container = ServiceContainer.get()
    user_id = container.repository.get_session_user_id(_hash_token(token))
    if user_id is None:
        return None

    return container.auth_service.get_user_by_id(user_id)


def destroy_session(token: Optional[str]) -> None:
    """Deletes the session row for a token, so the cookie stops working."""
    if not token:
        return
    container = ServiceContainer.get()
    container.repository.delete_session(_hash_token(token))


def _cookie_value(cookie_header: str, name: str) -> Optional[str]:
    """Extracts one cookie value from a raw `Cookie:` header."""
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        key, _, value = part.strip().partition("=")
        if key == name:
            return value or None
    return None


def session_token(session: rio.Session) -> Optional[str]:
    """Reads the session token out of the request's cookie header."""
    headers = getattr(session, "http_headers", None)
    if headers is None:
        return None
    return _cookie_value(headers.get("cookie", ""), SESSION_COOKIE)


def current_user(session: rio.Session) -> Optional[User]:
    """Returns the signed-in user for this Rio session, or None.

    The token is resolved against the database on every call, so a deleted
    account loses access immediately.
    """
    return user_for_token(session_token(session))


def cookie_url_for(session: rio.Session, token: str) -> Optional[str]:
    """Returns a URL that sets the session cookie, or None if unavailable.

    Rio's server exposes `url_for_cookies`, which sets the cookie with
    `httponly=True`. Visiting the returned URL is what actually stores it.
    """
    server = getattr(session, "_app_server", None)
    url_for_cookies = getattr(server, "url_for_cookies", None)
    if url_for_cookies is None:
        return None
    return url_for_cookies({SESSION_COOKIE: token})
