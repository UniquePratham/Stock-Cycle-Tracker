"""Domain models for User accounts, Avatars, and Authentication."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AvatarInfo:
    """Represents a curated trader avatar."""
    id: str
    name: str
    icon: str
    color_hex: str
    role: str
    description: str


AVAILABLE_AVATARS: List[AvatarInfo] = [
    AvatarInfo(
        id="bull_trader",
        name="Bull Trader",
        icon="material/trending-up",
        color_hex="#10B981",
        role="Momentum Rider",
        description="Rides strong upward cycle trends with disciplined risk management.",
    ),
    AvatarInfo(
        id="cycle_master",
        name="Cycle Master",
        icon="material/history-toggle-off",
        color_hex="#3B82F6",
        role="Institutional Cycles",
        description="Tracks historical annual recurrence patterns and reference high/lows.",
    ),
    AvatarInfo(
        id="diamond_hands",
        name="Diamond Hands",
        icon="material/diamond",
        color_hex="#06B6D4",
        role="Value Compounder",
        description="Holds high-conviction institutional positions through cycle pullbacks.",
    ),
    AvatarInfo(
        id="alpha_eagle",
        name="Alpha Eagle",
        icon="material/visibility",
        color_hex="#8B5CF6",
        role="Macro & Sector Rotator",
        description="Identifies sector breakouts and multi-year cycle bottoms.",
    ),
    AvatarInfo(
        id="quantum_analyst",
        name="Quant Analyst",
        icon="material/calculate",
        color_hex="#EC4899",
        role="Quantitative Models",
        description="Analyzes statistical moving averages, DMA support, and volume spikes.",
    ),
    AvatarInfo(
        id="wolf_trader",
        name="Dalal Street Wolf",
        icon="material/bolt",
        color_hex="#F59E0B",
        role="Breakout Scalper",
        description="Capitalizes on high-volatility event dates and quarterly earnings cycles.",
    ),
    AvatarInfo(
        id="rocket_rider",
        name="Moonshot Trader",
        icon="material/rocket",
        color_hex="#6366F1",
        role="Growth & Catalysts",
        description="Focuses on high-growth upside momentum (>20% buckets).",
    ),
    AvatarInfo(
        id="bear_hunter",
        name="Bear Hunter",
        icon="material/shield",
        color_hex="#F43F5E",
        role="Contrarian Accumulator",
        description="Accumulates quality blue-chips during severe downside discount windows.",
    ),
]

AVATAR_MAP: Dict[str, AvatarInfo] = {a.id: a for a in AVAILABLE_AVATARS}


def get_avatar(avatar_id: Optional[str]) -> AvatarInfo:
    """Returns the AvatarInfo for a given avatar_id, defaulting to Bull Trader."""
    if avatar_id and avatar_id in AVATAR_MAP:
        return AVATAR_MAP[avatar_id]
    return AVAILABLE_AVATARS[0]


@dataclass
class User:
    """User account entity with credentials and profile information."""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    salt: str = ""
    full_name: str = ""
    avatar_id: str = "bull_trader"
    created_at: datetime = field(default_factory=utc_now)

    @property
    def avatar(self) -> AvatarInfo:
        return get_avatar(self.avatar_id)

    @property
    def display_name(self) -> str:
        return self.full_name or self.username or "Investor"
