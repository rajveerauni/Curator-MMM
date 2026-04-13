"""Generate synthetic weekly MMM data for portfolio demonstration.

This script creates 156 weeks of TV, Google, and Instagram spend with
seasonal patterns, applies the *true* adstock and Hill saturation used
in the data-generating process, and writes ``synthetic_mmm_data.csv``.

The ground-truth parameters are stored as module constants for reference
in documentation and sanity checks; the modeling code does *not* read
these values (the Bayesian model learns coefficients from data).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# True transform parameters (data-generating process only)
# -----------------------------------------------------------------------------
TV_DECAY: float = 0.55
TV_EC50: float = 25000.0
TV_SLOPE: float = 2.5

GOOGLE_DECAY: float = 0.20
GOOGLE_EC50: float = 12000.0
GOOGLE_SLOPE: float = 2.0

INSTAGRAM_DECAY: float = 0.30
INSTAGRAM_EC50: float = 8000.0
INSTAGRAM_SLOPE: float = 1.8

# Linear weights on saturated adstock (DGP). Hill outputs are unitless in [0, 1];
# this scale maps their weighted sum into realistic revenue units while keeping
# the intended relative elasticities (2.8 : 3.5 : 2.1).
WEIGHT_TV: float = 2.8
WEIGHT_GOOGLE: float = 3.5
WEIGHT_INSTAGRAM: float = 2.1
SATURATION_TO_REVENUE_SCALE: float = 55_000.0
BASELINE_SALES: float = 120_000.0
SALES_NOISE_SD: float = 8000.0

RNG_SEED: int = 42
N_WEEKS: int = 156
START_DATE: str = "2022-01-03"

ROOT: Path = Path(__file__).resolve().parent


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _geometric_adstock(series: np.ndarray, decay_rate: float) -> np.ndarray:
    """Apply geometric adstock (same recurrence as ``src.transforms``)."""
    result = np.empty_like(series, dtype=float)
    result[0] = series[0]
    for i in range(1, len(series)):
        result[i] = series[i] + decay_rate * result[i - 1]
    return result


def _hill_saturation(x: np.ndarray, ec50: float, slope: float) -> np.ndarray:
    """Hill saturation; output in [0, 1]."""
    x = np.asarray(x, dtype=float)
    xc = np.maximum(x, 0.0)
    return (xc**slope) / (ec50**slope + xc**slope)


def _is_christmas_season(week: pd.Timestamp) -> bool:
    return week.month == 12 and week.day >= 10


def _is_easter_window(week: pd.Timestamp) -> bool:
    """Approximate Easter-adjacent retail window (US-centric heuristic)."""
    return (week.month == 3 and week.day >= 15) or (week.month == 4 and week.day <= 20)


def main() -> None:
    print(f"[{_ts()}] Generating synthetic MMM dataset ({N_WEEKS} weeks)...")
    np.random.seed(RNG_SEED)

    week_dates = pd.date_range(start=START_DATE, periods=N_WEEKS, freq="W-MON")
    rows = []

    for i, week in enumerate(week_dates):
        tv_mult = 1.0
        if _is_christmas_season(week) or _is_easter_window(week):
            tv_mult = 1.35

        tv_raw = np.random.gamma(shape=2.0, scale=15_000.0) * tv_mult
        google_raw = np.random.gamma(shape=3.0, scale=8_000.0)

        insta_mult = 1.0
        week_num_1based = i + 1
        if 20 <= week_num_1based <= 30:
            insta_mult = 1.25
        insta_raw = np.random.gamma(shape=2.0, scale=5_000.0) * insta_mult

        rows.append(
            {
                "week": week.date(),
                "tv_spend": float(tv_raw),
                "google_spend": float(google_raw),
                "instagram_spend": float(insta_raw),
            }
        )

    df = pd.DataFrame(rows)

    tv_ad = _geometric_adstock(df["tv_spend"].to_numpy(), TV_DECAY)
    g_ad = _geometric_adstock(df["google_spend"].to_numpy(), GOOGLE_DECAY)
    i_ad = _geometric_adstock(df["instagram_spend"].to_numpy(), INSTAGRAM_DECAY)

    tv_sat = _hill_saturation(tv_ad, TV_EC50, TV_SLOPE)
    g_sat = _hill_saturation(g_ad, GOOGLE_EC50, GOOGLE_SLOPE)
    i_sat = _hill_saturation(i_ad, INSTAGRAM_EC50, INSTAGRAM_SLOPE)

    noise = np.random.normal(loc=0.0, scale=SALES_NOISE_SD, size=N_WEEKS)
    saturated_mix = (
        WEIGHT_TV * tv_sat + WEIGHT_GOOGLE * g_sat + WEIGHT_INSTAGRAM * i_sat
    )
    df["sales"] = BASELINE_SALES + SATURATION_TO_REVENUE_SCALE * saturated_mix + noise

    out_path = ROOT / "synthetic_mmm_data.csv"
    df.to_csv(out_path, index=False)
    print(f"[{_ts()}] Saved {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
