"""Plotly interactive chart generator supporting multiple cycles, responsive heights, and adaptive light/dark theme gridlines."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go

from stock_cycle_tracker.domain.models import CycleAnalysis, NormalizedOHLC


def create_cycle_plotly_figure(
    symbol: str,
    ohlc_bars: List[NormalizedOHLC],
    analysis: Optional[CycleAnalysis] = None,
    all_analyses: Optional[List[CycleAnalysis]] = None,
    overlay_all: bool = False,
    is_mobile: bool = False,
    is_portrait: bool = False,
    is_dark_mode: bool = True,
) -> go.Figure:
    """Generates an interactive Plotly chart with visible theme-aware grid lines and price action."""
    fig = go.Figure()

    if not ohlc_bars:
        fig.update_layout(
            annotations=[
                dict(
                    text="No historical price data available",
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=14, color="#94A3B8"),
                )
            ]
        )
        return fig

    df = pd.DataFrame([
        {
            "Date": b.date,
            "Open": b.open,
            "High": b.high,
            "Low": b.low,
            "Close": b.close,
            "Volume": b.volume,
        }
        for b in ohlc_bars
    ])
    df.sort_values("Date", inplace=True)

    # Base price trace: Line plot with soft area gradient
    line_col = "#38BDF8" if is_dark_mode else "#0284C7"
    fill_col = "rgba(56, 189, 248, 0.08)" if is_dark_mode else "rgba(2, 132, 199, 0.06)"

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            mode="lines",
            name="Daily Close",
            line=dict(color=line_col, width=2.0),
            fill="tozeroy",
            fillcolor=fill_col,
            hovertemplate="<b>%{x|%d-%b-%Y}</b><br>Close: ₹%{y:,.2f}<extra></extra>",
        )
    )

    # Determine which analyses to plot
    analyses_to_plot: List[CycleAnalysis] = []
    if overlay_all and all_analyses:
        analyses_to_plot = all_analyses
    elif analysis:
        analyses_to_plot = [analysis]

    # Palette for multiple cycle lines
    cycle_colors = ["#F59E0B", "#10B981", "#8B5CF6", "#EC4899", "#3B82F6"]

    for idx, c_analysis in enumerate(analyses_to_plot):
        col = cycle_colors[idx % len(cycle_colors)]
        c_num = c_analysis.cycle_number
        ref_high = c_analysis.reference_high
        ref_trade_date = c_analysis.actual_reference_trading_date

        # Reference High horizontal line
        fig.add_hline(
            y=ref_high,
            line_dash="dash",
            line_color=col,
            line_width=1.8,
            annotation_text=f"C{c_num} Ref High: ₹{ref_high:,.2f}",
            annotation_position="top right",
            annotation_font=dict(color=col, size=9 if is_mobile else 11, family="Inter, Roboto, sans-serif"),
            annotation_bgcolor="#1E293B" if is_dark_mode else "#F1F5F9",
            annotation_bordercolor=col,
            annotation_borderwidth=1,
            annotation_borderpad=3,
        )

        # Anchor date vertical reference line
        fig.add_vline(
            x=ref_trade_date,
            line_dash="dot",
            line_color=col,
            line_width=1.5,
            annotation_text=f"C{c_num} Ref: {ref_trade_date.strftime('%d-%b')}",
            annotation_position="bottom left",
            annotation_font=dict(color=col, size=9 if is_mobile else 10, family="Inter, Roboto, sans-serif"),
            annotation_bgcolor="#1E293B" if is_dark_mode else "#F1F5F9",
            annotation_bordercolor=col,
            annotation_borderwidth=1,
            annotation_borderpad=2,
        )

    # Add Latest Price marker dot
    if not df.empty:
        last_row = df.iloc[-1]
        fig.add_trace(
            go.Scatter(
                x=[last_row["Date"]],
                y=[last_row["Close"]],
                mode="markers",
                name=f"Current ({analysis.price_type.value if analysis else 'PRICE'})",
                marker=dict(size=9 if is_mobile else 10, color="#F43F5E", line=dict(width=2, color="#FFFFFF")),
                hovertemplate="<b>Latest: %{x|%d-%b-%Y}</b><br>Price: ₹%{y:,.2f}<extra></extra>",
            )
        )

    # Adaptive chart height
    if is_mobile:
        chart_height = 580 if is_portrait else 340
    else:
        chart_height = 460

    title_text = (
        f"<b>{symbol}</b> (Cycle {analysis.cycle_number if analysis else 1})"
        if is_mobile
        else f"<b>{symbol}</b> — Annual Cycle Price Action & Reference High Anchor"
    )

    # Theme-aware colors
    if is_dark_mode:
        paper_bg = "#111827"
        plot_bg = "#0B1120"
        grid_col = "rgba(255, 255, 255, 0.15)"  # High-contrast visible gridlines
        zero_col = "rgba(255, 255, 255, 0.25)"
        title_col = "#F8FAFC"
        axis_font_col = "#CBD5E1"
        legend_bg = "rgba(17, 24, 39, 0.85)"
        legend_font_col = "#E2E8F0"
        template_name = "plotly_dark"
    else:
        paper_bg = "#FFFFFF"
        plot_bg = "#F8FAFC"
        grid_col = "#E2E8F0"                   # Distinct soft gray gridlines
        zero_col = "#CBD5E1"
        title_col = "#0F172A"
        axis_font_col = "#475569"
        legend_bg = "rgba(255, 255, 255, 0.9)"
        legend_font_col = "#334155"
        template_name = "plotly_white"

    fig.update_layout(
        template=template_name,
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        margin=dict(l=40 if is_mobile else 65, r=15 if is_mobile else 45, t=50 if is_mobile else 65, b=40 if is_mobile else 50),
        height=chart_height,
        autosize=True,
        dragmode=False,
        title=dict(
            text=title_text,
            font=dict(size=12 if is_mobile else 16, color=title_col, family="Inter, Roboto, sans-serif"),
            x=0.02,
            y=0.97,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.98,
            font=dict(color=legend_font_col, size=9 if is_mobile else 11),
            bgcolor=legend_bg,
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=grid_col,
            gridwidth=1.2,
            zeroline=True,
            zerolinecolor=zero_col,
            fixedrange=True,
            color=axis_font_col,
            tickfont=dict(size=9 if is_mobile else 11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=grid_col,
            gridwidth=1.2,
            zeroline=True,
            zerolinecolor=zero_col,
            fixedrange=True,
            color=axis_font_col,
            tickprefix="₹",
            tickformat=",.2f",
            separatethousands=True,
            tickfont=dict(size=9 if is_mobile else 11),
        ),
        hovermode="x unified" if not is_mobile else False,
    )

    return fig
