"""Channel transforms for MMM: geometric adstock and Hill saturation.

These transforms map raw weekly spend into *effective* media signals that
feed the Bayesian regression. Adstock captures carry-over; Hill curves
capture diminishing returns at high spend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

ROOT: Path = Path(__file__).resolve().parent.parent


def geometric_adstock(series: np.ndarray, decay_rate: float) -> np.ndarray:
    """Apply recursive geometric adstock to a spend series.

    For weekly data, each period's *adstocked* value compounds prior
    effects with exponential decay. This is the standard MMM adstock
    recurrence used in Robyn, Meridian, and related libraries.

    Args:
        series: One-dimensional nonnegative spend array.
        decay_rate: Carry-over fraction in ``[0, 1)`` (higher = longer memory).

    Returns:
        Adstocked array of the same shape as ``series``.

    Example:
        >>> geometric_adstock(np.array([100.0, 0.0, 0.0]), 0.5)
        array([100. ,  50. ,  25. ])
    """
    s = np.asarray(series, dtype=float)
    if s.ndim != 1:
        raise ValueError("series must be one-dimensional")
    out = np.empty_like(s)
    out[0] = s[0]
    for i in range(1, len(s)):
        out[i] = s[i] + decay_rate * out[i - 1]
    return out


def hill_saturation(x: np.ndarray, ec50: float, slope: float) -> np.ndarray:
    """Hill saturation curve; maps nonnegative input to ``[0, 1)``.

    ``ec50`` is the half-saturation point (potency) and ``slope`` controls
    the steepness of the S-curve.

    Args:
        x: Nonnegative input (typically adstocked spend).
        ec50: Half-saturation level (must be positive).
        slope: Hill exponent (must be positive).

    Returns:
        Saturation values in ``[0, 1)``.

    Example:
        >>> hill_saturation(np.array([0.0, 10000.0]), ec50=10000.0, slope=2.0)
        array([0.  , 0.5])
    """
    if ec50 <= 0 or slope <= 0:
        raise ValueError("ec50 and slope must be positive")
    xc = np.maximum(np.asarray(x, dtype=float), 0.0)
    return (xc**slope) / (ec50**slope + xc**slope)


def apply_channel_transforms(
    df: pd.DataFrame, channel_params: Mapping[str, Mapping[str, Any]]
) -> pd.DataFrame:
    """Apply adstock then Hill saturation for each paid-media channel.

    Expects columns ``tv_spend``, ``google_spend``, ``instagram_spend``.
    ``channel_params`` maps channel keys ``tv``, ``google``, ``instagram``
    to dicts with keys ``decay``, ``ec50``, ``slope``.

    Args:
        df: Raw weekly panel.
        channel_params: Per-channel transform hyperparameters.

    Returns:
        Copy of ``df`` with ``tv_transformed``, ``google_transformed``,
        ``instagram_transformed`` columns appended.

    Example:
        >>> params = {
        ...     "tv": {"decay": 0.5, "ec50": 1.0, "slope": 2.0},
        ...     "google": {"decay": 0.2, "ec50": 1.0, "slope": 2.0},
        ...     "instagram": {"decay": 0.3, "ec50": 1.0, "slope": 2.0},
        ... }
        >>> out = apply_channel_transforms(raw_df, params)
    """
    required = {"tv_spend", "google_spend", "instagram_spend"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing columns: {sorted(missing)}")

    out = df.copy()

    tv_p = channel_params["tv"]
    g_p = channel_params["google"]
    i_p = channel_params["instagram"]

    tv_ad = geometric_adstock(out["tv_spend"].to_numpy(), float(tv_p["decay"]))
    g_ad = geometric_adstock(out["google_spend"].to_numpy(), float(g_p["decay"]))
    i_ad = geometric_adstock(out["instagram_spend"].to_numpy(), float(i_p["decay"]))

    out["tv_transformed"] = hill_saturation(tv_ad, float(tv_p["ec50"]), float(tv_p["slope"]))
    out["google_transformed"] = hill_saturation(g_ad, float(g_p["ec50"]), float(g_p["slope"]))
    out["instagram_transformed"] = hill_saturation(
        i_ad, float(i_p["ec50"]), float(i_p["slope"])
    )
    return out
