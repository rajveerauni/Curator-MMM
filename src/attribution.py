"""Historical attribution: decompose sales into channel contributions.

Point estimates use posterior means for interpretable weekly dashboards.
For decision-grade planning, full posterior predictive intervals should
accompany these tables (omitted here for dashboard simplicity).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT: Path = Path(__file__).resolve().parent.parent
OUTPUTS_DIR: Path = ROOT / "outputs"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _posterior_means(trace: az.InferenceData) -> dict[str, float]:
    post = trace.posterior
    return {
        "intercept": float(post["intercept"].mean()),
        "beta_tv": float(post["beta_tv"].mean()),
        "beta_google": float(post["beta_google"].mean()),
        "beta_insta": float(post["beta_insta"].mean()),
    }


def compute_contributions(
    df_transformed: pd.DataFrame,
    trace: az.InferenceData,
    norm_stats: dict[str, dict[str, float]],
    path: Path | None = None,
) -> pd.DataFrame:
    """Decompose observed sales into baseline and channel contributions.

    Uses z-score normalization consistent with :mod:`src.model` and
    posterior means for coefficients.

    Args:
        df_transformed: Weekly frame with ``*_transformed`` and ``sales``.
        trace: Fitted :class:`arviz.InferenceData`.
        norm_stats: Channel mean/std used during training.
        path: Optional CSV path (defaults to ``outputs/contributions.csv``).

    Returns:
        Weekly attribution table.

    Example:
        >>> contrib_df = compute_contributions(transformed, idata, stats)
        >>> contrib_df[["week", "fitted_sales"]].head()
    """
    print(f"[{_ts()}] Computing historical contributions...")
    means = _posterior_means(trace)

    tv_n = (df_transformed["tv_transformed"].astype(float) - norm_stats["tv"]["mean"]) / norm_stats[
        "tv"
    ]["std"]
    g_n = (df_transformed["google_transformed"].astype(float) - norm_stats["google"]["mean"]) / norm_stats[
        "google"
    ]["std"]
    i_n = (
        df_transformed["instagram_transformed"].astype(float) - norm_stats["instagram"]["mean"]
    ) / norm_stats["instagram"]["std"]

    baseline = np.full(len(df_transformed), means["intercept"], dtype=float)
    contrib_tv = means["beta_tv"] * tv_n.to_numpy()
    contrib_google = means["beta_google"] * g_n.to_numpy()
    contrib_insta = means["beta_insta"] * i_n.to_numpy()

    fitted = baseline + contrib_tv + contrib_google + contrib_insta
    actual = df_transformed["sales"].astype(float).to_numpy()
    residual = actual - fitted

    out = pd.DataFrame(
        {
            "week": df_transformed["week"],
            "actual_sales": actual,
            "baseline": baseline,
            "contrib_tv": contrib_tv,
            "contrib_google": contrib_google,
            "contrib_insta": contrib_insta,
            "fitted_sales": fitted,
            "residual": residual,
        }
    )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    p = path or (OUTPUTS_DIR / "contributions.csv")
    out.to_csv(p, index=False)
    print(f"[{_ts()}] Saved contributions to {p}")
    return out


def compute_roi(
    contributions_df: pd.DataFrame,
    raw_df: pd.DataFrame,
    path: Path | None = None,
) -> pd.DataFrame:
    """Aggregate ROAS-style metrics by channel (incremental sales / spend).

    Args:
        contributions_df: Output of :func:`compute_contributions`.
        raw_df: Raw spend columns aligned by row order with contributions.
        path: Optional CSV path (defaults to ``outputs/roi_summary.csv``).

    Returns:
        One row per channel with spend and efficiency metrics.

    Example:
        >>> roi_df = compute_roi(contrib_df, raw)
        >>> roi_df.loc[roi_df["channel"] == "TV", "roi"].iloc[0] > 0
        True
    """
    print(f"[{_ts()}] Computing ROI summary...")
    if len(contributions_df) != len(raw_df):
        raise ValueError("contributions_df and raw_df must have the same length")

    channels = [
        ("TV", "tv_spend", "contrib_tv"),
        ("Google", "google_spend", "contrib_google"),
        ("Instagram", "instagram_spend", "contrib_insta"),
    ]
    rows: list[dict[str, float | str]] = []
    for name, spend_col, contrib_col in channels:
        total_spend = float(raw_df[spend_col].astype(float).sum())
        incremental = float(contributions_df[contrib_col].astype(float).sum())
        roas = incremental / total_spend if total_spend > 0 else float("nan")
        rows.append(
            {
                "channel": name,
                "total_spend": total_spend,
                "incremental_sales": incremental,
                "roi": roas,
                "revenue_per_1_spent": roas,
            }
        )

    roi_df = pd.DataFrame(rows)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    p = path or (OUTPUTS_DIR / "roi_summary.csv")
    roi_df.to_csv(p, index=False)
    print(f"[{_ts()}] Saved ROI summary to {p}")
    return roi_df


def plot_decomposition(contributions_df: pd.DataFrame, path: Path | None = None) -> Path:
    """Save a stacked-area decomposition with actual sales overlay.

    Args:
        contributions_df: Weekly decomposition from :func:`compute_contributions`.
        path: Optional PNG path (defaults to ``outputs/decomposition.png``).

    Returns:
        Path to the written figure.

    Example:
        >>> plot_decomposition(contrib_df)
        PosixPath('.../decomposition.png')
    """
    print(f"[{_ts()}] Plotting decomposition chart...")
    df = contributions_df.copy()
    x = np.arange(len(df))

    baseline = df["baseline"].to_numpy()
    tv = df["contrib_tv"].to_numpy()
    google = df["contrib_google"].to_numpy()
    insta = df["contrib_insta"].to_numpy()
    actual = df["actual_sales"].to_numpy()

    fig, ax = plt.subplots(figsize=(12, 5))
    colors = {
        "baseline": "#888780",
        "tv": "#EF9F27",
        "google": "#5DCAA5",
        "insta": "#AFA9EC",
    }

    ax.stackplot(
        x,
        baseline,
        tv,
        google,
        insta,
        labels=["Baseline", "TV", "Google", "Instagram"],
        colors=[colors["baseline"], colors["tv"], colors["google"], colors["insta"]],
        alpha=0.9,
    )
    ax.plot(x, actual, color="black", linestyle="--", linewidth=1.5, label="Actual sales")
    ax.set_title("Sales decomposition (posterior mean coefficients)")
    ax.set_xlabel("Week index")
    ax.set_ylabel("Sales ($)")
    ax.legend(loc="upper right", frameon=False)
    ax.set_facecolor("#131b2e")
    fig.patch.set_facecolor("#0b1326")
    ax.tick_params(colors="#dae2fd")
    ax.title.set_color("#dae2fd")
    ax.xaxis.label.set_color("#adc7ff")
    ax.yaxis.label.set_color("#adc7ff")
    for spine in ax.spines.values():
        spine.set_color("#3e4949")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    p = path or (OUTPUTS_DIR / "decomposition.png")
    plt.tight_layout()
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[{_ts()}] Saved decomposition figure to {p}")
    return p


def plot_roi_bars(roi_df: pd.DataFrame, path: Path | None = None) -> Path:
    """Horizontal bar chart of ROAS with value annotations.

    Args:
        roi_df: Aggregated ROI metrics.
        path: Optional PNG path (defaults to ``outputs/roi_bars.png``).

    Returns:
        Path to the written figure.

    Example:
        >>> plot_roi_bars(roi_df)
    """
    print(f"[{_ts()}] Plotting ROI bar chart...")
    df = roi_df.sort_values("roi", ascending=True)
    labels = df["channel"].tolist()
    values = df["roi"].astype(float).tolist()

    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(len(labels))
    ax.barh(y, values, color="#76d6d5", alpha=0.85)
    ax.set_yticks(y, labels)
    ax.set_xlabel("ROAS (incremental sales / spend)")
    ax.set_title("Channel efficiency (ROAS)")
    for i, v in enumerate(values):
        ax.text(v, i, f"  {v:.2f}x", va="center", color="#dae2fd", fontsize=10)
    ax.set_facecolor("#131b2e")
    fig.patch.set_facecolor("#0b1326")
    ax.tick_params(colors="#dae2fd")
    ax.title.set_color("#dae2fd")
    ax.xaxis.label.set_color("#adc7ff")
    for spine in ax.spines.values():
        spine.set_color("#3e4949")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    p = path or (OUTPUTS_DIR / "roi_bars.png")
    plt.tight_layout()
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[{_ts()}] Saved ROI bars to {p}")
    return p
