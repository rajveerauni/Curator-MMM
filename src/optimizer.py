"""Constrained budget allocation using nonlinear optimization (SLSQP).

The objective maximizes *predicted* sales from the fitted linear layer
applied to steady-state adstock and Hill-saturated spend. This is a
pragmatic planning approximation; full dynamic optimization would
simulate multi-week paths with state dependence.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.transforms import hill_saturation

ROOT: Path = Path(__file__).resolve().parent.parent
OUTPUTS_DIR: Path = ROOT / "outputs"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _steady_state_adstock(weekly_spend: float, decay: float) -> float:
    """Long-run adstock level for constant weekly spend."""
    d = float(decay)
    if d >= 1.0:
        raise ValueError("decay must be < 1 for steady-state adstock")
    return float(weekly_spend) / (1.0 - d)


def _predicted_revenue(
    spends: np.ndarray,
    intercept: float,
    beta_means: Mapping[str, float],
    ec50s: Mapping[str, float],
    slopes: Mapping[str, float],
    decays: Mapping[str, float],
    norm_stats: Mapping[str, Mapping[str, float]],
) -> float:
    """Point prediction for vector ``[tv, google, insta]`` weekly spends."""
    keys = ["tv", "google", "instagram"]
    betas = [beta_means["beta_tv"], beta_means["beta_google"], beta_means["beta_insta"]]
    total = float(intercept)
    for k, s, b in zip(keys, spends, betas):
        ad = _steady_state_adstock(s, decays[k])
        h = float(hill_saturation(np.array([ad]), ec50s[k], slopes[k])[0])
        n = (h - norm_stats[k]["mean"]) / norm_stats[k]["std"]
        total += float(b) * n
    return total


def evaluate_allocation(
    spends: Sequence[float],
    beta_means: Mapping[str, float],
    ec50s: Mapping[str, float],
    slopes: Mapping[str, float],
    decays: Mapping[str, float],
    norm_stats: Mapping[str, Mapping[str, float]],
) -> float:
    """Predict weekly revenue for a concrete spend vector (TV, Google, Instagram).

    Args:
        spends: Length-3 sequence of weekly spends aligned to TV → Google → Instagram.
        beta_means: Posterior means including ``intercept``.
        ec50s: Hill potencies by channel.
        slopes: Hill slopes by channel.
        decays: Adstock decays by channel.
        norm_stats: Normalization statistics for Hill outputs.

    Returns:
        Point prediction of expected sales.

    Example:
        >>> evaluate_allocation([100, 100, 100], betas, ec50s, slopes, decays, stats)
        142000.0
    """
    arr = np.asarray(spends, dtype=float).reshape(-1)
    if arr.shape[0] != 3:
        raise ValueError("spends must have three entries (TV, Google, Instagram)")
    intercept = float(beta_means["intercept"])
    return float(
        _predicted_revenue(arr, intercept, beta_means, ec50s, slopes, decays, norm_stats)
    )


def optimize_budget(
    total_budget: float,
    beta_means: Mapping[str, float],
    ec50s: Mapping[str, float],
    slopes: Mapping[str, float],
    decays: Mapping[str, float],
    norm_stats: Mapping[str, Mapping[str, float]],
    channel_bounds: Mapping[str, tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Maximize predicted revenue subject to a total budget and box constraints.

    Args:
        total_budget: Total weekly spend to allocate across the three channels.
        beta_means: Posterior means with keys ``intercept``, ``beta_tv``,
            ``beta_google``, ``beta_insta``.
        ec50s: Hill ``ec50`` by channel key (``tv``, ``google``, ``instagram``).
        slopes: Hill slopes by channel key.
        decays: Adstock decay by channel key.
        norm_stats: Normalization means/std devs for transformed signals.
        channel_bounds: Optional per-channel ``(min_spend, max_spend)`` in
            absolute dollars. Defaults to 5%–70% of ``total_budget``.

    Returns:
        Dictionary with optimal spends, predicted revenue, and efficiency.

    Example:
        >>> out = optimize_budget(
        ...     500_000,
        ...     {"intercept": 120_000, "beta_tv": 1.0, "beta_google": 1.5, "beta_insta": 1.2},
        ...     {"tv": 25_000, "google": 12_000, "instagram": 8_000},
        ...     {"tv": 2.5, "google": 2.0, "instagram": 1.8},
        ...     {"tv": 0.55, "google": 0.2, "instagram": 0.3},
        ...     norm_stats,
        ... )
        >>> out["predicted_revenue"] > 0
        True
    """
    if total_budget <= 0:
        raise ValueError("total_budget must be positive")
    intercept = float(beta_means["intercept"])

    keys = ["tv", "google", "instagram"]
    if channel_bounds is None:
        lo = 0.05 * total_budget
        hi = 0.70 * total_budget
        bounds = [(lo, hi), (lo, hi), (lo, hi)]
    else:
        bounds = [channel_bounds[k] for k in keys]

    def objective(x: np.ndarray) -> float:
        rev = _predicted_revenue(x, intercept, beta_means, ec50s, slopes, decays, norm_stats)
        return -rev

    x0 = np.full(3, total_budget / 3.0)
    cons = {"type": "eq", "fun": lambda x: float(np.sum(x) - total_budget)}
    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 500, "ftol": 1e-9},
    )
    if not res.success:
        print(f"[{_ts()}] Optimizer warning: {res.message}")

    opt = res.x.astype(float)
    pred = _predicted_revenue(opt, intercept, beta_means, ec50s, slopes, decays, norm_stats)
    return {
        "tv_spend": float(opt[0]),
        "google_spend": float(opt[1]),
        "instagram_spend": float(opt[2]),
        "predicted_revenue": float(pred),
        "revenue_per_dollar": float(pred / total_budget),
        "optimizer_success": bool(res.success),
        "optimizer_message": str(res.message),
    }


def run_scenario_analysis(
    beta_means: Mapping[str, float],
    ec50s: Mapping[str, float],
    slopes: Mapping[str, float],
    decays: Mapping[str, float],
    norm_stats: Mapping[str, Mapping[str, float]],
    path: Path | None = None,
) -> pd.DataFrame:
    """Optimize allocations across ten budget levels from 100k to 1M.

    Args:
        beta_means: See :func:`optimize_budget`.
        ec50s: Hill potencies by channel.
        slopes: Hill slopes by channel.
        decays: Adstock decays by channel.
        norm_stats: Normalization stats for Hill outputs.
        path: Optional PNG output path.

    Returns:
        DataFrame of optimal allocations by budget scenario.

    Example:
        >>> df = run_scenario_analysis(betas, ec50s, slopes, decays, stats)
        >>> df.columns
        Index(['budget', 'tv_spend', 'google_spend', 'instagram_spend', 'predicted_revenue'], dtype='object')
    """
    print(f"[{_ts()}] Running budget scenario analysis...")
    budgets = np.linspace(100_000, 1_000_000, num=10)
    rows: list[dict[str, float]] = []
    for b in budgets:
        out = optimize_budget(float(b), beta_means, ec50s, slopes, decays, norm_stats)
        rows.append(
            {
                "budget": float(b),
                "tv_spend": out["tv_spend"],
                "google_spend": out["google_spend"],
                "instagram_spend": out["instagram_spend"],
                "predicted_revenue": out["predicted_revenue"],
            }
        )

    scenario_df = pd.DataFrame(rows)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUTS_DIR / "scenario_results.csv"
    scenario_df.to_csv(csv_path, index=False)
    print(f"[{_ts()}] Saved scenario table to {csv_path}")

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(scenario_df))
    tv = scenario_df["tv_spend"].to_numpy()
    g = scenario_df["google_spend"].to_numpy()
    insta = scenario_df["instagram_spend"].to_numpy()
    ax.bar(x, tv, label="TV", color="#EF9F27")
    ax.bar(x, g, bottom=tv, label="Google", color="#5DCAA5")
    ax.bar(x, insta, bottom=tv + g, label="Instagram", color="#AFA9EC")
    ax.set_xticks(x, [f"${v/1000:.0f}k" for v in scenario_df["budget"]], rotation=45, ha="right")
    ax.set_title("Optimal weekly allocation by total budget scenario")
    ax.set_ylabel("Spend ($)")
    ax.legend(frameon=False)
    ax.set_facecolor("#131b2e")
    fig.patch.set_facecolor("#0b1326")
    ax.tick_params(colors="#dae2fd")
    ax.title.set_color("#dae2fd")
    ax.yaxis.label.set_color("#adc7ff")
    for spine in ax.spines.values():
        spine.set_color("#3e4949")

    p = path or (OUTPUTS_DIR / "scenario_analysis.png")
    plt.tight_layout()
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[{_ts()}] Saved scenario chart to {p}")
    return scenario_df
