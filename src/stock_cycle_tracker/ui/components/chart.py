"""Plotly chart builder for stock cycle visual analysis."""

from __future__ import annotations

from typing import List, Optional
import pandas as pd
import plotly.graph_objects as go

from stock_cycle_tracker.domain.models import CycleAnalysis, NormalizedOHLC


def create_cycle_plotly_figure(
    symbol: str,
    ohlc_bars: List[NormalizedOHLC],
    analysis: Optional[CycleAnalysis] = None,
) -> go.Figure:
    """Builds a rich, dark-themed financial Plotly figure for cycle analysis."""
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
            height=500,
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
            name="Daily Close Price",
            line=dict(color="#3B82F6", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.08)",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Close: ₹%{y:,.2f}<extra></extra>",
        )
    )

    if analysis:
        ref_high = analysis.reference_high
        ref_date = analysis.actual_reference_trading_date
        cur_price = analysis.current_price

        # Reference High horizontal line
        fig.add_hline(
            y=ref_high,
            line_dash="dash",
            line_color="#F59E0B",
            line_width=2.0,
            annotation_text=f"Ref High: ₹{ref_high:,.2f}",
            annotation_position="top right",
            annotation_font=dict(color="#F59E0B", size=12, family="Inter, Roboto, sans-serif"),
            annotation_bgcolor="#1E293B",
            annotation_bordercolor="#F59E0B",
            annotation_borderwidth=1,
        )

        # Actual reference date vertical line
        fig.add_vline(
            x=pd.to_datetime(ref_date),
            line_dash="dot",
            line_color="#06B6D4",
            line_width=1.8,
            annotation_text=f"Ref Date: {ref_date.strftime('%d-%b-%Y')}",
            annotation_position="bottom left",
            annotation_font=dict(color="#06B6D4", size=11, family="Inter, Roboto, sans-serif"),
            annotation_bgcolor="#1E293B",
            annotation_bordercolor="#06B6D4",
            annotation_borderwidth=1,
        )

        # Current price marker
        latest_date = df["date"].iloc[-1]
        is_up = analysis.percentage_change >= 0
        point_col = "#10B981" if is_up else "#F43F5E"

        fig.add_trace(
            go.Scatter(
                x=[latest_date],
                y=[cur_price],
                mode="markers+text",
                name=f"Current Price ({analysis.price_type.value})",
                marker=dict(
                    color=point_col,
                    size=12,
                    symbol="circle",
                    line=dict(color="#FFFFFF", width=2.0),
                ),
                text=[f" ₹{cur_price:,.2f} ({analysis.percentage_change:+.2f}%)"],
                textposition="top right",
                textfont=dict(color=point_col, size=13, family="Inter, Roboto, sans-serif"),
                hovertemplate="<b>Current Price</b>: ₹%{y:,.2f}<br>%{text}<extra></extra>",
            )
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#0B1120",
        margin=dict(l=65, r=45, t=65, b=50),
        height=520,
        autosize=True,
        title=dict(
            text=f"<b>{symbol}</b> — Annual Cycle Price Action & Reference High Anchor",
            font=dict(size=16, color="#F8FAFC", family="Inter, Roboto, sans-serif"),
            x=0.02,
            y=0.96,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.98,
            font=dict(color="#94A3B8", size=11),
            bgcolor="rgba(17, 24, 39, 0.8)",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1E293B",
            gridwidth=1,
            zeroline=False,
            color="#94A3B8",
            tickfont=dict(size=11),
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
            tickfont=dict(size=11),
        ),
        hovermode="x unified",
    )

    return fig
