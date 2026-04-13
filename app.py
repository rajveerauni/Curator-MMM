"""Curator MMM — Streamlit dashboard (premium dark UI, design-system aligned)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import arviz as az
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT: Path = Path(__file__).resolve().parent
OUTPUTS: Path = ROOT / "outputs"
DATA_CSV: Path = ROOT / "data" / "synthetic_mmm_data.csv"

CHANNEL_PARAMS: dict[str, dict[str, float]] = {
    "tv": {"decay": 0.55, "ec50": 25_000.0, "slope": 2.5},
    "google": {"decay": 0.20, "ec50": 12_000.0, "slope": 2.0},
    "instagram": {"decay": 0.30, "ec50": 8_000.0, "slope": 1.8},
}

PLOTLY_LAYOUT: dict[str, Any] = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#dae2fd", size=12),
    xaxis=dict(
        gridcolor="rgba(62,73,73,0.3)",
        linecolor="rgba(62,73,73,0.5)",
        tickfont=dict(color="#879392", size=10),
    ),
    yaxis=dict(
        gridcolor="rgba(62,73,73,0.3)",
        linecolor="rgba(62,73,73,0.5)",
        tickfont=dict(color="#879392", size=10),
    ),
    legend=dict(
        bgcolor="rgba(45,52,73,0.6)",
        bordercolor="rgba(135,147,146,0.15)",
        borderwidth=1,
        font=dict(color="#adc7ff", size=11),
    ),
    margin=dict(l=0, r=0, t=40, b=0),
)


def inject_fonts() -> None:
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet"/>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
        """,
        unsafe_allow_html=True,
    )


def inject_css() -> None:
    css_path = ROOT / "assets" / "style.css"
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_usd(value: float) -> str:
    return f"${value:,.0f}"


def format_inr_lakhs(value: float) -> str:
    """Format rupee amounts with comma grouping (portfolio demo)."""
    return f"₹{value:,.0f}"


def beta_means_from_trace(trace: az.InferenceData) -> dict[str, float]:
    post = trace.posterior
    return {
        "intercept": float(post["intercept"].mean()),
        "beta_tv": float(post["beta_tv"].mean()),
        "beta_google": float(post["beta_google"].mean()),
        "beta_insta": float(post["beta_insta"].mean()),
    }


SIDEBAR_LOGO_HTML = """
<div style="display:flex;align-items:center;gap:12px;padding:0 8px;margin-bottom:16px">
  <div style="width:32px;height:32px;border-radius:6px;background:#008080;
              display:flex;align-items:center;justify-content:center">
    <span class="material-symbols-outlined" style="color:#e3fffe;font-size:18px">analytics</span>
  </div>
  <div>
    <div style="font-size:18px;font-weight:800;color:#008080;letter-spacing:-0.5px">Curator MMM</div>
    <div style="font-size:10px;color:#adc7ff;opacity:0.7;letter-spacing:0.15em;text-transform:uppercase">
      Marketing Insights
    </div>
  </div>
</div>
"""

SIDEBAR_FOOTER_HTML = """
<div style="padding:16px 8px;border-top:1px solid rgba(255,255,255,0.05);
            display:flex;align-items:center;gap:12px;margin-top:24px">
  <div style="width:32px;height:32px;border-radius:50%;background:#008080;
              display:flex;align-items:center;justify-content:center;
              font-weight:700;color:#e3fffe;font-size:13px">AR</div>
  <div>
    <div style="font-size:13px;font-weight:500;color:#dae2fd">Alex Rivard</div>
    <div style="font-size:11px;color:#adc7ff;opacity:0.6">Senior Analyst</div>
  </div>
</div>
"""


def render_sidebar_nav_html(current_key: str) -> str:
    """Decorative nav row mirroring the design spec (Streamlit ``radio`` handles selection)."""
    items = [
        ("dashboard", "dashboard", "Dashboard"),
        ("attribution", "analytics", "Channel Attribution"),
        ("optimization", "query_stats", "Optimization"),
        ("scenarios", "insights", "Scenarios"),
        ("methodology", "settings", "Methodology"),
    ]
    nav_blocks: list[str] = []
    for key, icon, label in items:
        active = key == current_key
        color = "#76d6d5" if active else "#adc7ff"
        weight = "700" if active else "400"
        border = "2px solid #76d6d5" if active else "none"
        bg = "rgba(255,255,255,0.05)" if active else "transparent"
        nav_blocks.append(
            f"""
            <div style="display:flex;align-items:center;gap:16px;padding:12px 16px;
                        color:{color};font-weight:{weight};border-right:{border};
                        background:{bg};text-decoration:none;margin-bottom:2px;
                        border-radius:4px;font-size:14px;letter-spacing:-0.2px">
              <span class="material-symbols-outlined" style="font-size:20px">{icon}</span>
              {label}
            </div>
            """
        )
    return "".join(nav_blocks)


def render_mobile_nav_strip() -> None:
    st.markdown(
        """
        <div class="curator-mobile-nav" style="display:flex;justify-content:space-around;align-items:center">
          <span class="material-symbols-outlined" style="color:#76d6d5;font-size:22px">dashboard</span>
          <span class="material-symbols-outlined" style="color:#adc7ff;font-size:22px;opacity:0.7">analytics</span>
          <span class="material-symbols-outlined" style="color:#adc7ff;font-size:22px;opacity:0.7">query_stats</span>
          <span class="material-symbols-outlined" style="color:#adc7ff;font-size:22px;opacity:0.7">insights</span>
          <span class="material-symbols-outlined" style="color:#adc7ff;font-size:22px;opacity:0.7">settings</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_dashboard() -> None:
    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px">
          <div>
            <h2 style="font-size:28px;font-weight:700;color:#dae2fd;letter-spacing:-0.5px;margin:0">Data Overview</h2>
            <p style="color:#adc7ff;font-size:13px;margin:4px 0 0">
              Real-time performance metrics across all active streams.</p>
          </div>
          <div style="display:flex;gap:12px">
            <div style="background:#222a3d;padding:8px 16px;border-radius:12px;border:1px solid rgba(118,214,213,0.1);
                        font-size:13px;color:#dae2fd;display:flex;align-items:center;gap:8px">
              <span class="material-symbols-outlined" style="font-size:16px">filter_list</span>
              Filter Views
            </div>
            <div style="background:linear-gradient(135deg,#76d6d5,#adc7ff);padding:8px 20px;border-radius:12px;
                        font-size:13px;font-weight:700;color:#002020;display:flex;align-items:center;gap:8px">
              <span class="material-symbols-outlined" style="font-size:16px">download</span>
              Export Report
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = [
        {
            "label": "TOTAL SALES",
            "value": "$2,482,900",
            "badge": "+12.4%",
            "badge_bg": "rgba(118,214,213,0.1)",
            "badge_color": "#76d6d5",
            "subtext": "vs. previous period",
            "path": "M0 15 Q 10 5, 20 12 T 40 8 T 60 14 T 80 5 T 100 2",
            "stroke": "#76d6d5",
        },
        {
            "label": "NET ROI",
            "value": "384%",
            "badge": "4.2x",
            "badge_bg": "rgba(118,214,213,0.1)",
            "badge_color": "#76d6d5",
            "subtext": "Target: 350%",
            "path": "M0 18 Q 20 15, 40 10 T 60 8 T 80 4 T 100 1",
            "stroke": "#76d6d5",
        },
        {
            "label": "AVG. CPA",
            "value": "$14.20",
            "badge": "+2.1%",
            "badge_bg": "rgba(255,180,171,0.1)",
            "badge_color": "#ffb4ab",
            "subtext": "Efficiency threshold: $15.00",
            "path": "M0 5 Q 20 10, 40 12 T 60 15 T 80 18 T 100 19",
            "stroke": "#ffb4ab",
        },
        {
            "label": "TOTAL SPEND",
            "value": "$645,000",
            "badge": "Stable",
            "badge_bg": "rgba(135,147,146,0.1)",
            "badge_color": "#879392",
            "subtext": "82% of monthly budget",
            "path": "M0 10 H 20 L 30 15 L 40 10 L 60 10 L 80 12 L 100 10",
            "stroke": "#adc7ff",
        },
    ]

    c1, c2, c3, c4 = st.columns(4)
    for col, card in zip((c1, c2, c3, c4), cards):
        with col:
            st.markdown(
                f"""
                <div style="background:#131b2e;border-radius:12px;padding:24px;outline:1px solid rgba(135,147,146,0.15)">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
                    <span style="font-size:10px;color:#879392;text-transform:uppercase;letter-spacing:0.1em">{card["label"]}</span>
                    <span style="font-size:11px;font-weight:700;padding:2px 8px;border-radius:99px;background:{card["badge_bg"]};color:{card["badge_color"]}">{card["badge"]}</span>
                  </div>
                  <div style="font-size:32px;font-weight:800;color:#dae2fd;letter-spacing:-1px;margin-bottom:4px">{card["value"]}</div>
                  <div style="font-size:11px;color:#879392;margin-bottom:12px">{card["subtext"]}</div>
                  <svg style="width:100%;height:40px" viewBox="0 0 100 20">
                    <path d="{card["path"]}" fill="none" stroke="{card["stroke"]}" stroke-width="2"/>
                  </svg>
                </div>
                """,
                unsafe_allow_html=True,
            )

    df = pd.read_csv(DATA_CSV, parse_dates=["week"]) if DATA_CSV.exists() else None
    weeks = np.arange(len(df)) if df is not None else np.arange(156)
    sales = df["sales"].to_numpy() if df is not None else np.sin(weeks / 10) * 20_000 + 400_000
    prev = np.roll(sales, 4)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=sales,
            mode="lines",
            name="Weekly Sales",
            line=dict(color="#76d6d5", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=prev,
            mode="lines",
            name="Previous Period",
            line=dict(color="#ffb692", width=2, dash="dot"),
            opacity=0.6,
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Weekly Sales Trends", font=dict(color="#dae2fd", size=16)),
        legend=dict(**PLOTLY_LAYOUT["legend"], orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
    )
    fig.update_xaxes(title_text="Week index")
    fig.update_yaxes(title_text="Sales ($)")

    left, right = st.columns([8, 4])
    with left:
        st.markdown(
            """
            <div style="margin-bottom:12px">
              <div style="font-size:12px;color:#adc7ff;text-transform:uppercase;letter-spacing:0.12em">Performance</div>
              <div style="font-size:18px;font-weight:700;color:#dae2fd">Weekly Sales Trends</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="curator-glass">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(
            """
            <div style="background:#131b2e;border-radius:12px;padding:24px;outline:1px solid rgba(135,147,146,0.15)">
              <h3 style="font-size:16px;font-weight:700;color:#dae2fd;margin-bottom:20px">Channel Performance</h3>
              <div style="margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px">
                  <span style="color:#dae2fd;font-weight:500">Social</span>
                  <span style="color:#adc7ff">$245k</span>
                </div>
                <div style="width:100%;height:6px;background:#2d3449;border-radius:99px;overflow:hidden">
                  <div style="height:100%;width:85%;background:rgba(118,214,213,1.0);border-radius:99px"></div>
                </div>
              </div>
              <div style="margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px">
                  <span style="color:#dae2fd;font-weight:500">Search</span>
                  <span style="color:#adc7ff">$180k</span>
                </div>
                <div style="width:100%;height:6px;background:#2d3449;border-radius:99px;overflow:hidden">
                  <div style="height:100%;width:65%;background:rgba(118,214,213,0.8);border-radius:99px"></div>
                </div>
              </div>
              <div style="margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px">
                  <span style="color:#dae2fd;font-weight:500">Display</span>
                  <span style="color:#adc7ff">$110k</span>
                </div>
                <div style="width:100%;height:6px;background:#2d3449;border-radius:99px;overflow:hidden">
                  <div style="height:100%;width:40%;background:rgba(118,214,213,0.6);border-radius:99px"></div>
                </div>
              </div>
              <div style="margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px">
                  <span style="color:#dae2fd;font-weight:500">TV</span>
                  <span style="color:#adc7ff">$90k</span>
                </div>
                <div style="width:100%;height:6px;background:#2d3449;border-radius:99px;overflow:hidden">
                  <div style="height:100%;width:32%;background:rgba(118,214,213,0.4);border-radius:99px"></div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    d1, d2 = st.columns(2)
    with d1:
        st.markdown(
            """
            <div style="background:#131b2e;border-radius:12px;padding:24px;outline:1px solid rgba(135,147,146,0.15);text-align:center">
              <div style="font-size:12px;color:#adc7ff;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:12px">Budget mix</div>
              <svg viewBox="0 0 36 36" style="width:160px;height:160px;margin:auto;transform:rotate(-90deg)">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="3.8"/>
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 15.9155 7.9577"
                      fill="none" stroke="#76d6d5" stroke-width="3.8" stroke-dasharray="70, 100"/>
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 10 17.5"
                      fill="none" stroke="#4a8eff" stroke-width="3.8" stroke-dasharray="20, 100" stroke-dashoffset="-70"/>
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 2 19"
                      fill="none" stroke="#ffb692" stroke-width="3.8" stroke-dasharray="10, 100" stroke-dashoffset="-90"/>
              </svg>
              <div style="margin-top:8px;font-size:18px;font-weight:800;color:#dae2fd">70% Digital</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with d2:
        st.markdown(
            """
            <div style="background:#131b2e;border-radius:12px;padding:24px;outline:1px solid rgba(135,147,146,0.15)">
              <div style="font-size:16px;font-weight:700;color:#dae2fd;margin-bottom:16px">Model Insights</div>
              <div style="display:flex;gap:12px;margin-bottom:14px;align-items:flex-start">
                <span class="material-symbols-outlined" style="color:#76d6d5">auto_awesome</span>
                <div style="font-size:13px;color:#adc7ff;line-height:1.4">Diminishing returns detected on TikTok spend.</div>
              </div>
              <div style="display:flex;gap:12px;margin-bottom:14px;align-items:flex-start">
                <span class="material-symbols-outlined" style="color:#ffb692">error</span>
                <div style="font-size:13px;color:#adc7ff;line-height:1.4">Data anomaly in Search week 09.</div>
              </div>
              <div style="display:flex;gap:12px;margin-bottom:18px;align-items:flex-start">
                <span class="material-symbols-outlined" style="color:#4a8eff">trending_up</span>
                <div style="font-size:13px;color:#adc7ff;line-height:1.4">Opportunity to scale OTT by 15%.</div>
              </div>
              <div style="text-align:center">
                <div style="display:inline-block;background:linear-gradient(135deg,#76d6d5,#adc7ff);color:#002020;
                            font-weight:800;padding:10px 18px;border-radius:12px;font-size:11px;letter-spacing:0.12em;text-transform:uppercase">
                  Review All Alerts
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="margin-top:48px;height:40px;background:linear-gradient(to right, rgba(0,128,128,0.2), transparent, rgba(74,142,255,0.2));
                    filter:blur(48px);opacity:0.2;border-radius:999px"></div>
        """,
        unsafe_allow_html=True,
    )


def page_attribution() -> None:
    st.markdown(
        """
        <div style="margin-bottom:24px">
          <h2 style="font-size:28px;font-weight:700;color:#dae2fd;letter-spacing:-0.5px;margin:0">Channel Attribution</h2>
          <p style="color:#adc7ff;font-size:13px;margin:6px 0 0">
            Posterior mean decomposition of revenue across paid media levers.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    roi_path = OUTPUTS / "roi_summary.csv"
    contrib_path = OUTPUTS / "contributions.csv"
    if not roi_path.exists() or not contrib_path.exists():
        st.warning("Run `python run_all.py` to generate attribution outputs.")
        return

    roi_df = pd.read_csv(roi_path)
    contrib = pd.read_csv(contrib_path, parse_dates=["week"])

    m1, m2, m3 = st.columns(3)
    rois = {row["channel"]: row for _, row in roi_df.iterrows()}
    for col, name in zip((m1, m2, m3), ("TV", "Google", "Instagram")):
        r = rois.get(name, {})
        val = float(r.get("roi", 0.0)) * 100
        with col:
            st.markdown(
                f"""
                <div style="background:#131b2e;border-radius:12px;padding:20px;outline:1px solid rgba(135,147,146,0.15)">
                  <div style="font-size:10px;color:#879392;text-transform:uppercase;letter-spacing:0.1em">{name} ROI</div>
                  <div style="font-size:32px;font-weight:800;color:#dae2fd">{val:.1f}%</div>
                  <div style="font-size:11px;color:#879392">ROAS-style (incremental / spend)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    weeks = np.arange(len(contrib))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=contrib["baseline"],
            stackgroup="one",
            name="Baseline",
            fillcolor="rgba(136,135,128,0.7)",
            line=dict(width=0, color="#888780"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=contrib["contrib_tv"],
            stackgroup="one",
            name="TV",
            fillcolor="rgba(239,159,39,0.85)",
            line=dict(width=0, color="#EF9F27"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=contrib["contrib_google"],
            stackgroup="one",
            name="Google",
            fillcolor="rgba(93,202,165,0.85)",
            line=dict(width=0, color="#5DCAA5"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=contrib["contrib_insta"],
            stackgroup="one",
            name="Instagram",
            fillcolor="rgba(175,169,236,0.85)",
            line=dict(width=0, color="#AFA9EC"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=contrib["actual_sales"],
            name="Actual sales",
            line=dict(color="black", dash="dash", width=2),
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Historical decomposition", font=dict(color="#dae2fd", size=16)),
        hovermode="x unified",
    )
    st.markdown('<div class="curator-glass" style="margin-top:8px">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        hfig = go.Figure(
            go.Bar(
                x=roi_df["roi"],
                y=roi_df["channel"],
                orientation="h",
                marker=dict(color=["#EF9F27", "#5DCAA5", "#AFA9EC"]),
            )
        )
        hfig.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text="ROI comparison", font=dict(color="#dae2fd", size=15)),
            xaxis_title="ROAS (incremental / spend)",
        )
        st.plotly_chart(hfig, use_container_width=True)
    with right:
        st.dataframe(contrib, use_container_width=True, hide_index=True)


def page_optimization() -> None:
    st.markdown(
        """
        <div style="margin-bottom:24px">
          <h2 style="font-size:28px;font-weight:700;color:#dae2fd;letter-spacing:-0.5px;margin:0">Budget Optimizer</h2>
          <p style="color:#adc7ff;font-size:13px;margin:6px 0 0">
            SLSQP allocation maximizing predicted sales under Hill + steady-state adstock.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    trace_path = OUTPUTS / "trace.nc"
    norm_path = OUTPUTS / "normalization_stats.json"
    if not trace_path.exists() or not norm_path.exists():
        st.warning("Fit outputs missing — run `python run_all.py` first.")
        return

    from src.optimizer import evaluate_allocation, optimize_budget

    trace = az.from_netcdf(str(trace_path))
    betas = beta_means_from_trace(trace)
    norm_stats = load_json(norm_path)
    decays = {k: CHANNEL_PARAMS[k]["decay"] for k in ("tv", "google", "instagram")}
    ec50s = {k: CHANNEL_PARAMS[k]["ec50"] for k in ("tv", "google", "instagram")}
    slopes = {k: CHANNEL_PARAMS[k]["slope"] for k in ("tv", "google", "instagram")}

    st.markdown(
        '<div style="font-size:12px;color:#adc7ff;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px">Controls</div>',
        unsafe_allow_html=True,
    )
    budget = st.slider(
        "Total weekly budget (₹)",
        min_value=100_000,
        max_value=5_000_000,
        step=100_000,
        value=1_000_000,
    )
    c1, c2, c3 = st.columns(3)
    default_min = int(min(0.05 * budget, budget * 0.5))
    max_min = max(int(budget * 0.5), 1)
    with c1:
        min_tv = st.slider("Min TV (₹)", 0, max_min, default_min, step=50_000)
    with c2:
        min_g = st.slider("Min Google (₹)", 0, max_min, default_min, step=50_000)
    with c3:
        min_i = st.slider("Min Instagram (₹)", 0, max_min, default_min, step=50_000)

    run = st.button("Optimize Allocation", use_container_width=True)

    if run:
        bounds = {
            "tv": (float(min_tv), 0.70 * budget),
            "google": (float(min_g), 0.70 * budget),
            "instagram": (float(min_i), 0.70 * budget),
        }
        out = optimize_budget(
            float(budget),
            betas,
            ec50s,
            slopes,
            decays,
            norm_stats,
            channel_bounds=bounds,
        )
        eq = np.array([budget / 3.0, budget / 3.0, budget / 3.0], dtype=float)
        rev_eq = evaluate_allocation(eq, betas, ec50s, slopes, decays, norm_stats)
        uplift = (out["predicted_revenue"] - rev_eq) / rev_eq * 100 if rev_eq else 0.0

        k1, k2, k3 = st.columns(3)
        for col, label, val in zip(
            (k1, k2, k3),
            ("Optimal TV", "Optimal Google", "Optimal Instagram"),
            (out["tv_spend"], out["google_spend"], out["instagram_spend"]),
        ):
            with col:
                st.markdown(
                    f"""
                    <div style="background:#131b2e;border-radius:12px;padding:20px;outline:1px solid rgba(135,147,146,0.15)">
                      <div style="font-size:10px;color:#879392;text-transform:uppercase;letter-spacing:0.1em">{label}</div>
                      <div style="font-size:28px;font-weight:800;color:#dae2fd">{format_inr_lakhs(val)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        pie = go.Figure(
            data=[
                go.Pie(
                    labels=["TV", "Google", "Instagram"],
                    values=[out["tv_spend"], out["google_spend"], out["instagram_spend"]],
                    hole=0.55,
                    marker=dict(colors=["#EF9F27", "#5DCAA5", "#AFA9EC"]),
                )
            ]
        )
        pie.update_layout(**PLOTLY_LAYOUT, title=dict(text="Allocation mix", font=dict(color="#dae2fd")))
        st.plotly_chart(pie, use_container_width=True)

        st.markdown(
            f"""
            <div style="background:#131b2e;border-radius:12px;padding:24px;outline:1px solid rgba(135,147,146,0.15);margin-top:12px">
              <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
                <div>
                  <div style="font-size:10px;color:#879392;text-transform:uppercase;letter-spacing:0.1em">Predicted revenue</div>
                  <div style="font-size:36px;font-weight:800;color:#dae2fd">{format_inr_lakhs(out["predicted_revenue"])}</div>
                </div>
                <div style="font-size:12px;font-weight:800;padding:6px 12px;border-radius:99px;background:rgba(118,214,213,0.12);color:#76d6d5">
                  Uplift vs equal split: {uplift:+.1f}%
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def page_scenarios() -> None:
    st.markdown(
        """
        <div style="margin-bottom:24px">
          <h2 style="font-size:28px;font-weight:700;color:#dae2fd;letter-spacing:-0.5px;margin:0">Scenario Analysis</h2>
          <p style="color:#adc7ff;font-size:13px;margin:6px 0 0">
            Optimal weekly allocations from $100k to $1M total spend (ten scenarios).</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    scen_csv = OUTPUTS / "scenario_results.csv"
    if not scen_csv.exists():
        st.warning("Scenario table not found — run `python run_all.py`.")
        return
    sdf = pd.read_csv(scen_csv)
    x = np.arange(len(sdf))
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=sdf["tv_spend"], name="TV", marker_color="#EF9F27"))
    fig.add_trace(go.Bar(x=x, y=sdf["google_spend"], name="Google", marker_color="#5DCAA5"))
    fig.add_trace(go.Bar(x=x, y=sdf["instagram_spend"], name="Instagram", marker_color="#AFA9EC"))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="stack",
        title=dict(text="Stacked optimal allocation by budget", font=dict(color="#dae2fd")),
        xaxis=dict(
            **PLOTLY_LAYOUT["xaxis"],
            tickmode="array",
            tickvals=list(x),
            ticktext=[f"₹{v/1000:.0f}k" for v in sdf["budget"]],
        ),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(sdf, use_container_width=True, hide_index=True)


def page_methodology() -> None:
    st.markdown(
        """
        <div style="margin-bottom:24px">
          <h2 style="font-size:28px;font-weight:700;color:#dae2fd;letter-spacing:-0.5px;margin:0">Methodology</h2>
          <p style="color:#adc7ff;font-size:13px;margin:6px 0 0">
            How Curator MMM translates spend into incremental revenue.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sections = [
        (
            "What is Marketing Mix Modeling?",
            "Marketing Mix Modeling (MMM) estimates how historical media and baseline demand "
            "jointly explain sales. Unlike last-click attribution, MMM is robust to platform bias "
            "and captures long-run carry-over. Executives use MMM to reallocate budget toward "
            "the next marginal dollar with the highest predicted return.",
        ),
        (
            "Adstock Transform",
            "Adstock models memory: this week's spend continues to influence demand in future "
            "weeks with geometric decay. Higher decay implies longer-lasting media effects, which "
            "is common for broad-reach channels such as television compared to lower-funnel search.",
        ),
        (
            "Saturation Curve",
            "The Hill function maps accumulated spend into a bounded response between zero and one, "
            "encoding diminishing returns. Its EC50 controls where the curve bends and the slope "
            "controls how sharply performance plateaus as budgets scale.",
        ),
        (
            "Bayesian Inference",
            "We place weakly informative priors on incremental coefficients and estimate posterior "
            "uncertainty with Hamiltonian Monte Carlo. Probabilistic outputs communicate confidence "
            "for planning scenarios instead of hiding ambiguity behind a single OLS point estimate.",
        ),
        (
            "Budget Optimization",
            "Given posterior means and transform hyperparameters, constrained nonlinear optimization "
            "allocates a fixed weekly budget across channels while respecting minimums and channel "
            "caps. The objective maximizes predicted sales under steady-state adstock, a pragmatic "
            "approximation for portfolio planning.",
        ),
    ]

    for title, body in sections:
        st.markdown(f'<div style="font-size:18px;font-weight:700;color:#76d6d5;margin:20px 0 8px">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#adc7ff;font-size:14px;line-height:1.6">{body}</p>', unsafe_allow_html=True)

    st.latex(
        r"Sales_{t} = \alpha + \beta_{1} \cdot TV_{t} + \beta_{2} \cdot Google_{t} + \beta_{3} \cdot Instagram_{t} + \epsilon_{t}"
    )


def main() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    inject_fonts()
    inject_css()

    labels = {
        "dashboard": "Dashboard",
        "attribution": "Channel Attribution",
        "optimization": "Optimization",
        "scenarios": "Scenarios",
        "methodology": "Methodology",
    }

    st.sidebar.markdown(SIDEBAR_LOGO_HTML, unsafe_allow_html=True)
    choice = st.sidebar.radio(
        "Navigation",
        list(labels.keys()),
        format_func=lambda k: labels[k],
        label_visibility="collapsed",
    )
    st.sidebar.markdown(render_sidebar_nav_html(choice), unsafe_allow_html=True)
    st.sidebar.markdown(SIDEBAR_FOOTER_HTML, unsafe_allow_html=True)

    st.markdown(
        """
        <div style="position:sticky;top:0;z-index:50;display:flex;justify-content:space-between;align-items:center;
                    padding:12px 0 20px;margin-bottom:8px;backdrop-filter:blur(24px);
                    border-bottom:1px solid rgba(255,255,255,0.06)">
          <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
            <div style="font-size:11px;font-weight:900;color:#dae2fd;letter-spacing:0.2em;text-transform:uppercase">
              Marketing Curator</div>
            <div style="position:relative">
              <span class="material-symbols-outlined" style="position:absolute;left:12px;top:8px;font-size:18px;color:#879392">search</span>
              <div style="width:260px;max-width:40vw;height:36px;background:#2d3449;border-radius:999px;
                          border:1px solid rgba(135,147,146,0.2)"></div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:14px">
            <span class="material-symbols-outlined" style="color:#adc7ff;font-size:22px">calendar_today</span>
            <div style="position:relative">
              <span class="material-symbols-outlined" style="color:#adc7ff;font-size:22px">notifications</span>
              <div style="position:absolute;top:2px;right:2px;width:7px;height:7px;background:#ffb4ab;border-radius:50%"></div>
            </div>
            <div style="width:1px;height:24px;background:rgba(255,255,255,0.08)"></div>
            <div style="width:32px;height:32px;border-radius:50%;background:#008080;display:flex;align-items:center;
                        justify-content:center;font-weight:700;color:#e3fffe;font-size:12px">AR</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if choice == "dashboard":
        page_dashboard()
    elif choice == "attribution":
        page_attribution()
    elif choice == "optimization":
        page_optimization()
    elif choice == "scenarios":
        page_scenarios()
    else:
        page_methodology()

    render_mobile_nav_strip()


if __name__ == "__main__":
    main()
