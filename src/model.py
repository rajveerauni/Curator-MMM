"""Bayesian Marketing Mix Model (linear Gaussian) with PyMC.

The model regresses weekly sales on *normalized* saturated adstock signals.
Coefficients are weakly informative Half-Normal priors on the positive
domain, reflecting the business belief that media rarely *reduces* sales
in aggregate (holdout tests and priors can be extended for production).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm

ROOT: Path = Path(__file__).resolve().parent.parent
OUTPUTS_DIR: Path = ROOT / "outputs"
TRACE_PATH: Path = OUTPUTS_DIR / "trace.nc"
NORM_STATS_PATH: Path = OUTPUTS_DIR / "normalization_stats.json"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _ensure_outputs_dir() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_normalization_stats(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Compute z-score stats for transformed channel columns.

    Args:
        df: Frame containing ``*_transformed`` columns.

    Returns:
        Nested dict keyed by channel with ``mean`` and ``std`` (ddof=0).

    Example:
        >>> stats = compute_normalization_stats(transformed_df)
        >>> stats["tv"]["mean"]
        0.42
    """
    stats: dict[str, dict[str, float]] = {}
    for col, key in (
        ("tv_transformed", "tv"),
        ("google_transformed", "google"),
        ("instagram_transformed", "instagram"),
    ):
        s = df[col].astype(float)
        stats[key] = {"mean": float(s.mean()), "std": float(s.std(ddof=0)) or 1.0}
    return stats


def apply_normalization(df: pd.DataFrame, stats: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Return a copy with normalized ``*_norm`` columns added."""
    out = df.copy()
    for src, dst, key in (
        ("tv_transformed", "tv_norm", "tv"),
        ("google_transformed", "google_norm", "google"),
        ("instagram_transformed", "instagram_norm", "instagram"),
    ):
        m = stats[key]["mean"]
        sd = stats[key]["std"]
        out[dst] = (out[src].astype(float) - m) / sd
    return out


def save_normalization_stats(stats: dict[str, dict[str, float]], path: Path | None = None) -> None:
    """Persist normalization stats as JSON for attribution and optimizer."""
    _ensure_outputs_dir()
    p = path or NORM_STATS_PATH
    p.write_text(json.dumps(stats, indent=2), encoding="utf-8")


def load_normalization_stats(path: Path | None = None) -> dict[str, dict[str, float]]:
    """Load normalization stats written by :func:`save_normalization_stats`."""
    p = path or NORM_STATS_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def build_model(df_normalized: pd.DataFrame) -> pm.Model:
    """Build a PyMC linear model on normalized saturated signals.

    Args:
        df_normalized: Must include ``tv_norm``, ``google_norm``,
            ``instagram_norm``, and ``sales``.

    Returns:
        A :class:`pymc.Model` context object (not yet sampled).

    Example:
        >>> model = build_model(train_df)
        >>> with model:
        ...     pass  # define completed
    """
    required = {"tv_norm", "google_norm", "instagram_norm", "sales"}
    missing = required - set(df_normalized.columns)
    if missing:
        raise ValueError(f"Missing columns for model build: {sorted(missing)}")

    tv = df_normalized["tv_norm"].to_numpy(dtype=float)
    google = df_normalized["google_norm"].to_numpy(dtype=float)
    insta = df_normalized["instagram_norm"].to_numpy(dtype=float)
    sales = df_normalized["sales"].to_numpy(dtype=float)
    n = len(sales)

    coords = {"week": np.arange(n)}
    with pm.Model(coords=coords) as model:
        tv_d = pm.Data("tv_norm", tv, dims="week")
        g_d = pm.Data("google_norm", google, dims="week")
        i_d = pm.Data("instagram_norm", insta, dims="week")

        intercept = pm.Normal("intercept", mu=100_000.0, sigma=30_000.0)
        beta_tv = pm.HalfNormal("beta_tv", sigma=5.0)
        beta_google = pm.HalfNormal("beta_google", sigma=5.0)
        beta_insta = pm.HalfNormal("beta_insta", sigma=5.0)
        sigma = pm.HalfNormal("sigma", sigma=10_000.0)

        mu = (
            intercept
            + beta_tv * tv_d
            + beta_google * g_d
            + beta_insta * i_d
        )
        pm.Normal("obs", mu=mu, sigma=sigma, observed=sales, dims="week")
    return model


def fit_model(model: pm.Model) -> az.InferenceData:
    """Sample the posterior with NUTS (two chains).

    Args:
        model: A built :class:`pymc.Model`.

    Returns:
        :class:`arviz.InferenceData` posterior trace.

    Example:
        >>> with build_model(df) as m:
        ...     idata = fit_model(m)
    """
    print(f"[{_ts()}] Fitting model... this may take 5-10 minutes")
    with model:
        idata = pm.sample(
            draws=2000,
            tune=1000,
            chains=2,
            target_accept=0.9,
            random_seed=42,
            progressbar=True,
        )
    print(f"[{_ts()}] Sampling complete")
    return idata


def save_trace(trace: az.InferenceData, path: Path | None = None) -> None:
    """Save posterior trace to NetCDF (ArviZ)."""
    _ensure_outputs_dir()
    p = path or TRACE_PATH
    trace.to_netcdf(str(p))
    print(f"[{_ts()}] Saved trace to {p}")


def load_trace(path: Path | None = None) -> az.InferenceData:
    """Load posterior trace from NetCDF."""
    p = path or TRACE_PATH
    return az.from_netcdf(str(p))


def diagnose_model(trace: az.InferenceData, path: Path | None = None) -> pd.DataFrame:
    """Summarize convergence (R-hat) and save a compact posterior figure.

    Args:
        trace: Posterior draws.
        path: Optional path for ``posteriors.png`` (defaults to ``outputs/``).

    Returns:
        ArviZ summary table as a :class:`pandas.DataFrame`.

    Example:
        >>> table = diagnose_model(idata)
        >>> float(table.loc["intercept", "r_hat"])
        1.0
    """
    _ensure_outputs_dir()
    print(f"[{_ts()}] Running diagnostics...")
    summary = az.summary(trace, var_names=["intercept", "beta_tv", "beta_google", "beta_insta", "sigma"])
    summary_path = OUTPUTS_DIR / "posterior_summary.csv"
    summary.to_csv(summary_path)
    print(f"[{_ts()}] Saved summary to {summary_path}")

    fig_path = path or (OUTPUTS_DIR / "posteriors.png")
    az.plot_trace(trace, var_names=["intercept", "beta_tv", "beta_google", "beta_insta", "sigma"])
    plt.tight_layout()
    fig = plt.gcf()
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close("all")
    print(f"[{_ts()}] Saved posterior plot grid to {fig_path}")
    return summary.reset_index().rename(columns={"index": "variable"})
