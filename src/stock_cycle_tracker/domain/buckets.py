"""Bucket classification engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BucketConfig:
    """Configurable boundaries for bucket classification."""
    threshold_low: float = 5.0
    threshold_mid1: float = 10.0
    threshold_mid2: float = 15.0
    threshold_high: float = 20.0


class BucketClassifier:
    """Classifies percentage change into specified upside/downside buckets."""

    def __init__(self, config: Optional[BucketConfig] = None) -> None:
        self.config = config or BucketConfig()

    def classify(self, percentage_change: float) -> str:
        """
        Classify percentage change according to deterministic bounds:
        Upside:
          0% <= x <= +5%   -> "Upside 0–5%"
          +5% < x <= +10%  -> "Upside 5–10%"
          +10% < x <= +15% -> "Upside 10–15%"
          +15% < x <= +20% -> "Upside 15–20%"
          x > +20%         -> "Upside >20%"
        Downside:
          -5% <= x < 0%    -> "Downside 0–5%"
          -10% <= x < -5%  -> "Downside 5–10%"
          -15% <= x < -10% -> "Downside 10–15%"
          -20% <= x < -15% -> "Downside 15–20%"
          x < -20%         -> "Downside >20%"
        """
        cfg = self.config
        val = round(percentage_change, 4)

        if val > cfg.threshold_high:
            return f"Upside >{int(cfg.threshold_high)}%"
        elif cfg.threshold_mid2 < val <= cfg.threshold_high:
            return f"Upside {int(cfg.threshold_mid2)}–{int(cfg.threshold_high)}%"
        elif cfg.threshold_mid1 < val <= cfg.threshold_mid2:
            return f"Upside {int(cfg.threshold_mid1)}–{int(cfg.threshold_mid2)}%"
        elif cfg.threshold_low < val <= cfg.threshold_mid1:
            return f"Upside {int(cfg.threshold_low)}–{int(cfg.threshold_mid1)}%"
        elif 0.0 <= val <= cfg.threshold_low:
            return f"Upside 0–{int(cfg.threshold_low)}%"
        elif -cfg.threshold_low <= val < 0.0:
            return f"Downside 0–{int(cfg.threshold_low)}%"
        elif -cfg.threshold_mid1 <= val < -cfg.threshold_low:
            return f"Downside {int(cfg.threshold_low)}–{int(cfg.threshold_mid1)}%"
        elif -cfg.threshold_mid2 <= val < -cfg.threshold_mid1:
            return f"Downside {int(cfg.threshold_mid1)}–{int(cfg.threshold_mid2)}%"
        elif -cfg.threshold_high <= val < -cfg.threshold_mid2:
            return f"Downside {int(cfg.threshold_mid2)}–{int(cfg.threshold_high)}%"
        else:  # val < -cfg.threshold_high
            return f"Downside >{int(cfg.threshold_high)}%"
