"""Plotly chart builder for stock cycle visual analysis with responsive mobile orientation and multi-cycle support."""

from __future__ import annotations

from typing import List, Optional
import pandas as pd
import plotly.graph_objects as go

from stock_cycle_tracker.domain.models import CycleAnalysis, NormalizedOHLC

CYCLE_COLORS = [
    "#F59E0B",  # Amber (Cycle 1)
    "#EC4899",  # Pink (Cycle 2)
    "#10B981",  # Emerald (Cycle 3)
    "#8B5CF6",  # Purple (Cycle 4)
    "#06B6D4",  # Cyan (Cycle 5)
]


def create_cycle_plotly_figure(
    symbol: str,
    ohlc_bars: List[NormalizedOHLC],
    analysis: Optional[CycleAnalysis] = None,
    all_analyses: Optional[List[CycleAnalysis]] = None,
    overlay_all: bool = False,
    is_mobile: bool = False,
) -> go.Figure:
    """Builds a rich, dark-themed financial Plotly figure with multi-cycle switching and tall vertical mobile view."""
    chart_height = 680 if is_mobile else 520

    if not ohlc_bars:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            title=dict(
                text=f"{symbol} — No Historical Price Data Available",
                font=dict(color="#94A3B8", size=14),
            ),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            height=chart_height,
        )
        return fig

    # Build DataFrame from NormalizedOHLC objects
    records = [
        {
            "date": b.date,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        }
        for b in ohlc_bars
    ]
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    fig = go.Figure()

    # Close price line with subtle area fill
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines",
            name="Daily Close",
            line=dict(color="#3B82F6", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.08)",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Close: ₹%{y:,.2f}<extra></extra>",
        )
    )

    analyses_to_draw = []
    if overlay_all and all_analyses:
        analyses_to_draw = all_analyses
    elif analysis:
        analyses_to_draw = [analysis]

    for idx, item in enumerate(analyses_to_draw):
        color = CYCLE_COLORS[idx % len(CYCLE_COLORS)]
        ref_high = item.reference_high
        ref_date = item.actual_reference_trading_date
        c_num = item.cycle_number

        # Reference High horizontal line
        fig.add_hline(
            y=ref_high,
            line_dash="dash",
            line_color=color,
            line_width=2.0,
            annotation_text=f"C{c_num} Ref High: ₹{ref_high:,.2f}",
            annotation_position="top right" if not is_mobile else "top left",
            annotation_font=dict(color=color, size=10 if is_mobile else 11, family="Inter, Roboto, sans-serif"),
            annotation_bgcolor="#1E293B",
            annotation_bordercolor=color,
            annotation_borderwidth=1,
        )

        # Actual reference date vertical line
        fig.add_vline(
            x=pd.to_datetime(ref_date),
            line_dash="dot",
            line_color=color,
            line_width=1.5,
            annotation_text=f"C{c_num} Ref: {ref_date.strftime('%d-%b')}",
            annotation_position="bottom left",
            annotation_font=dict(color=color, size=9 if is_mobile else 11, family="Inter, Roboto, sans-serif"),
            annotation_bgcolor="#1E293B",
            annotation_bordercolor=color,
            annotation_borderwidth=1,
        )

    # Current price marker
    if analysis:
        cur_price = analysis.current_price
        latest_date = df["date"].iloc[-1]
        is_up = analysis.percentage_change >= 0
        point_col = "#10B981" if is_up else "#F43F5E"

        fig.add_trace(
            go.Scatter(
                x=[latest_date],
                y=[cur_price],
                mode="markers+text",
                name=f"Current ({analysis.price_type.value})",
                marker=dict(
                    color=point_col,
                    size=11 if is_mobile else 13,
                    symbol="circle",
                    line=dict(color="#FFFFFF", width=2.0),
                ),
                text=[f" ₹{cur_price:,.2f}"],
                textposition="top right" if not is_mobile else "top left",
                textfont=dict(color=point_col, size=11 if is_mobile else 13, family="Inter, Roboto, sans-serif"),
                hovertemplate="<b>Current Price</b>: ₹%{y:,.2f}<br>%{text}<extra></extra>",
            )
        )

    title_text = (
        f"<b>{symbol}</b> (Cycle {analysis.cycle_number if analysis else 1})"
        if is_mobile
        else f"<b>{symbol}</b> — Annual Cycle Price Action & Reference High Anchor"
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#0B1120",
        margin=dict(l=45 if is_mobile else 65, r=20 if is_mobile else 45, t=55 if is_mobile else 65, b=45 if is_mobile else 50),
        height=chart_height,
        autosize=True,
        title=dict(
            text=title_text,
            font=dict(size=13 if is_mobile else 16, color="#F8FAFC", family="Inter, Roboto, sans-serif"),
            x=0.02,
            y=0.97,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.98,
            font=dict(color="#94A3B8", size=9 if is_mobile else 11),
            bgcolor="rgba(17, 24, 39, 0.8)",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1E293B",
            gridwidth=1,
            zeroline=False,
            color="#94A3B8",
            tickfont=dict(size=9 if is_mobile else 11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1E293B",
            gridwidth=1,
            zeroline=False,
            color="#94A3B8",
            tickprefix="₹",
            tickformat=",.2f",
            separatethousands=True,
            tickfont=dict(size=9 if is_mobile else 11),
        ),
        hovermode="x unified",
    )

    return fig
