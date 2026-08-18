"""Design tokens, dual light/dark theme configuration, and color helpers for Stock Cycle Tracker."""

from __future__ import annotations

import rio


def create_dark_theme() -> rio.Theme:
    """Creates a custom dark financial-terminal theme for Rio."""
    return rio.Theme.from_colors(
        mode="dark",
        primary_color=rio.Color.from_hex("#3B82F6"),     # Electric Blue
        secondary_color=rio.Color.from_hex("#6366F1"),   # Indigo
        background_color=rio.Color.from_hex("#090D16"),  # Deep Obsidian Canvas
        neutral_color=rio.Color.from_hex("#111827"),     # Card Surface
        hud_color=rio.Color.from_hex("#1E293B"),         # Elevated Container / Border
        success_color=rio.Color.from_hex("#10B981"),     # Emerald Green
        warning_color=rio.Color.from_hex("#F59E0B"),     # Amber
        danger_color=rio.Color.from_hex("#F43F5E"),      # Rose Red
        text_color=rio.Color.from_hex("#F8FAFC"),        # Light Slate text
        corner_radius_small=0.4,
        corner_radius_medium=0.6,
        corner_radius_large=0.8,
    )


def create_light_theme() -> rio.Theme:
    """Creates a sleek, high-contrast light theme for Rio."""
    return rio.Theme.from_colors(
        mode="light",
        primary_color=rio.Color.from_hex("#2563EB"),     # Vivid Blue
        secondary_color=rio.Color.from_hex("#4F46E5"),   # Indigo
        background_color=rio.Color.from_hex("#F1F5F9"),  # Soft Cool Slate Canvas
        neutral_color=rio.Color.from_hex("#FFFFFF"),     # Pure White Cards
        hud_color=rio.Color.from_hex("#E2E8F0"),         # Light Gray Elevated Container
        success_color=rio.Color.from_hex("#059669"),     # Rich Emerald
        warning_color=rio.Color.from_hex("#D97706"),     # Warm Amber
        danger_color=rio.Color.from_hex("#E11D48"),      # Crisp Red
        text_color=rio.Color.from_hex("#0F172A"),        # Deep Charcoal Text
        corner_radius_small=0.4,
        corner_radius_medium=0.6,
        corner_radius_large=0.8,
    )


def create_app_theme() -> tuple[rio.Theme, rio.Theme]:
    """Returns dual (light, dark) theme pair for the Rio application."""
    return (create_light_theme(), create_dark_theme())


# Palette tokens for custom fills
COLOR_BG_DARK = rio.Color.from_hex("#090D16")
COLOR_SURFACE_CARD = rio.Color.from_hex("#111827")
COLOR_SURFACE_HOVER = rio.Color.from_hex("#1E293B")
COLOR_BORDER = rio.Color.from_hex("#334155")
COLOR_TEXT_PRIMARY = rio.Color.from_hex("#F8FAFC")
COLOR_TEXT_MUTED = rio.Color.from_hex("#94A3B8")
COLOR_TEXT_DIM = rio.Color.from_hex("#64748B")

# Bullish / Bearish Color Tokens
COLOR_UP_STRONG = rio.Color.from_hex("#10B981")    # Emerald
COLOR_UP_LIGHT = rio.Color.from_hex("#34D399")
COLOR_DOWN_STRONG = rio.Color.from_hex("#F43F5E")  # Rose Red
COLOR_DOWN_LIGHT = rio.Color.from_hex("#FB7185")
COLOR_NEUTRAL = rio.Color.from_hex("#94A3B8")      # Slate


def get_change_color(percentage_change: float) -> rio.Color:
    """Returns emerald for positive change, rose for negative, slate for neutral."""
    if percentage_change > 0.0:
        return COLOR_UP_STRONG
    elif percentage_change < 0.0:
        return COLOR_DOWN_STRONG
    return COLOR_NEUTRAL


def get_bucket_color(bucket: str) -> rio.Color:
    """Returns color based on bucket classification."""
    b = bucket.lower()
    if "upside" in b:
        return COLOR_UP_STRONG
    elif "downside" in b:
        return COLOR_DOWN_STRONG
    return COLOR_NEUTRAL
