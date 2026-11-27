"""Shared guard for the protected pages."""

from __future__ import annotations

from typing import Optional

import rio

from stock_cycle_tracker.ui.session_auth import current_user


def require_login(event: rio.GuardEvent) -> Optional[str]:
    """Redirects to the landing page when nobody is signed in.

    Runs before the page is built, so an unauthenticated visitor never sees a
    flash of protected content.
    """
    if current_user(event.session) is None:
        return "/"
    return None
