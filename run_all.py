"""Run the end-to-end MMM pipeline: data → transforms → fit → attribution → scenarios."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT: Path = Path(__file__).resolve().parent


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def main() -> None:
    sys.path.insert(0, str(ROOT))

    from src.attribution import (
        compute_contributions,
        compute_roi,
        plot_decomposition,
        plot_roi_bars,
    )
    from src.model import (
        TRACE_PATH,
        apply_normalization,
        build_model,
        compute_normalization_stats,
        diagnose_model,
        fit_model,
        load_trace,
        save_normalization_stats,
        save_trace,
    )
    from src.optimizer import run_scenario_analysis
    from src.transforms import apply_channel_transforms

    print(f"[{_ts()}] Starting MMM pipeline from {ROOT}")

    # 1) Synthetic data
    subprocess.run([sys.executable, str(ROOT / "data" / "generate_data.py")], cwd=str(ROOT), check=True)

    raw_path = ROOT / "data" / "synthetic_mmm_data.csv"
    df_raw = pd.read_csv(raw_path, parse_dates=["week"])

    channel_params = {
        "tv": {"decay": 0.55, "ec50": 25_000.0, "slope": 2.5},
        "google": {"decay": 0.20, "ec50": 12_000.0, "slope": 2.0},
        "instagram": {"decay": 0.30, "ec50": 8_000.0, "slope": 1.8},
    }

    print(f"[{_ts()}] Applying channel transforms...")
    df_t = apply_channel_transforms(df_raw, channel_params)
    transformed_path = ROOT / "outputs" / "transformed_mmm_data.csv"
    transformed_path.parent.mkdir(parents=True, exist_ok=True)
    df_t.to_csv(transformed_path, index=False)
    print(f"[{_ts()}] Saved transformed data to {transformed_path}")

    norm_stats = compute_normalization_stats(df_t)
    save_normalization_stats(norm_stats)
    df_n = apply_normalization(df_t, norm_stats)

    model = build_model(df_n)
    if TRACE_PATH.exists():
        print(f"[{_ts()}] Found cached trace at {TRACE_PATH}; skipping refit")
        trace = load_trace(TRACE_PATH)
    else:
        trace = fit_model(model)
        save_trace(trace, TRACE_PATH)

    diagnose_model(trace)

    contrib = compute_contributions(df_t, trace, norm_stats)
    roi = compute_roi(contrib, df_raw)
    plot_decomposition(contrib)
    plot_roi_bars(roi)

    post = trace.posterior
    beta_means = {
        "intercept": float(post["intercept"].mean()),
        "beta_tv": float(post["beta_tv"].mean()),
        "beta_google": float(post["beta_google"].mean()),
        "beta_insta": float(post["beta_insta"].mean()),
    }
    decays = {k: channel_params[k]["decay"] for k in ("tv", "google", "instagram")}
    ec50s = {k: channel_params[k]["ec50"] for k in ("tv", "google", "instagram")}
    slopes = {k: channel_params[k]["slope"] for k in ("tv", "google", "instagram")}

    run_scenario_analysis(beta_means, ec50s, slopes, decays, norm_stats)

    print(f"[{_ts()}] Pipeline complete. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
