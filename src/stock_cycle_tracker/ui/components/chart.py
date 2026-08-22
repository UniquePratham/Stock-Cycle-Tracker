"""Plotly interactive chart generator supporting multi-year timelines (1M to Max), 50/200 DMA, Volume, and Cycle Anchors."""

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
    show_price: bool = True,
    show_50_dma: bool = True,
    show_200_dma: bool = True,
    show_volume: bool = True,
    show_cycle_anchors: bool = True,
    timeframe_label: str = "1Yr",
    is_mobile: bool = False,
    is_portrait: bool = False,
    is_dark_mode: bool = True,
) -> go.Figure:
    """Generates an interactive Plotly chart with 50/200 DMA, volume histogram, and cycle anchor lines."""
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
    df.reset_index(drop=True, inplace=True)

    # Calculate Moving Averages
    df["50_DMA"] = df["Close"].rolling(window=50, min_periods=1).mean()
    df["200_DMA"] = df["Close"].rolling(window=200, min_periods=1).mean()

    # 1. Volume Bar Series (Secondary Y-Axis at bottom 20% of chart)
    if show_volume and "Volume" in df.columns and df["Volume"].sum() > 0:
        vol_color = "rgba(56, 189, 248, 0.28)" if is_dark_mode else "rgba(2, 132, 199, 0.22)"
        fig.add_trace(
            go.Bar(
                x=df["Date"],
                y=df["Volume"],
                name="Trading Volume",
                yaxis="y2",
                marker_color=vol_color,
                hovertemplate="Volume: <b>%{y:,.0f} shares</b><extra>Volume</extra>",
            )
        )

    # 2. Base Price Line with full OHLC hover metadata and area fill
    if show_price:
        line_col = "#38BDF8" if is_dark_mode else "#0284C7"
        fill_col = "rgba(56, 189, 248, 0.07)" if is_dark_mode else "rgba(2, 132, 199, 0.05)"

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name=f"Price ({analysis.exchange if analysis else 'NSE'})",
                line=dict(color=line_col, width=2.0),
                fill="tozeroy",
                fillcolor=fill_col,
                customdata=df[["Open", "High", "Low", "Close", "Volume"]].values,
                hovertemplate=(
                    "<b>Date: %{x|%d-%b-%Y}</b><br>"
                    "Open: ₹%{customdata[0]:,.2f}<br>"
                    "High: ₹%{customdata[1]:,.2f}<br>"
                    "Low: ₹%{customdata[2]:,.2f}<br>"
                    "Close: <b>₹%{customdata[3]:,.2f}</b><br>"
                    "Volume: %{customdata[4]:,.0f}"
                    "<extra>Price</extra>"
                ),
            )
        )

    # 3. 50 Day Moving Average (Amber / Orange)
    if show_50_dma:
        dma50_col = "#F59E0B" if is_dark_mode else "#D97706"
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["50_DMA"],
                mode="lines",
                name="50 Day Moving Avg",
                line=dict(color=dma50_col, width=1.6),
                hovertemplate="50 DMA: <b>₹%{y:,.2f}</b><extra>50 DMA</extra>",
            )
        )

    # 4. 200 Day Moving Average (Slate / Deep Navy)
    if show_200_dma:
        dma200_col = "#94A3B8" if is_dark_mode else "#334155"
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["200_DMA"],
                mode="lines",
                name="200 Day Moving Avg",
                line=dict(color=dma200_col, width=1.6),
                hovertemplate="200 DMA: <b>₹%{y:,.2f}</b><extra>200 DMA</extra>",
            )
        )

    # 5. Cycle Anchor Horizontal & Vertical Annotations
    if show_cycle_anchors:
        analyses_to_plot: List[CycleAnalysis] = []
        if overlay_all and all_analyses:
            analyses_to_plot = all_analyses
        elif analysis:
            analyses_to_plot = [analysis]

        cycle_colors = ["#10B981", "#8B5CF6", "#EC4899", "#3B82F6", "#F59E0B"]

        for idx, c_analysis in enumerate(analyses_to_plot):
            col = cycle_colors[idx % len(cycle_colors)]
            c_num = c_analysis.cycle_number
            ref_high = c_analysis.reference_high
            ref_low = c_analysis.reference_low
            ref_trade_date = c_analysis.actual_reference_trading_date

            # Reference High horizontal dashed line
            fig.add_hline(
                y=ref_high,
                line_dash="dash",
                line_color=col,
                line_width=1.6,
                annotation_text=f" <b>Cycle {c_num} Ref High: ₹{ref_high:,.2f}</b> ",
                annotation_position="top right",
                annotation_font=dict(color=col, size=9 if is_mobile else 11, family="Roboto, Inter, sans-serif"),
                annotation_bgcolor="#1E293B" if is_dark_mode else "#F1F5F9",
                annotation_bordercolor=col,
                annotation_borderwidth=1,
                annotation_borderpad=3,
            )

            # Reference Low horizontal dotted line if distinct
            if ref_low > 0 and ref_low != ref_high:
                fig.add_hline(
                    y=ref_low,
                    line_dash="dot",
                    line_color=col,
                    line_width=1.2,
                    annotation_text=f" <b>Cycle {c_num} Ref Low: ₹{ref_low:,.2f}</b> ",
                    annotation_position="bottom right",
                    annotation_font=dict(color=col, size=8 if is_mobile else 10, family="Roboto, Inter, sans-serif"),
                    annotation_bgcolor="#1E293B" if is_dark_mode else "#F1F5F9",
                    annotation_bordercolor=col,
                    annotation_borderwidth=1,
                    annotation_borderpad=2,
                )

            # Anchor date vertical reference line (use ISO string format for Plotly datetime compatibility)
            ref_date_str = ref_trade_date.strftime("%Y-%m-%d") if hasattr(ref_trade_date, "strftime") else str(ref_trade_date)
            fig.add_vline(
                x=ref_date_str,
                line_dash="dot",
                line_color=col,
                line_width=1.4,
                annotation_text=f" <b>Cycle {c_num} Ref Date: {ref_trade_date.strftime('%d-%b-%Y') if hasattr(ref_trade_date, 'strftime') else str(ref_trade_date)}</b> ",
                annotation_position="bottom left",
                annotation_font=dict(color=col, size=8 if is_mobile else 10, family="Roboto, Inter, sans-serif"),
                annotation_bgcolor="#1E293B" if is_dark_mode else "#F1F5F9",
                annotation_bordercolor=col,
                annotation_borderwidth=1,
                annotation_borderpad=2,
            )

    # 6. Latest Price marker dot
    if not df.empty:
        last_row = df.iloc[-1]
        fig.add_trace(
            go.Scatter(
                x=[last_row["Date"]],
                y=[last_row["Close"]],
                mode="markers+text",
                name=f"Current: ₹{last_row['Close']:,.2f}",
                text=[f" ₹{last_row['Close']:,.2f}"],
                textposition="top right",
                textfont=dict(size=10 if is_mobile else 11, color="#F43F5E", family="Roboto, Inter, sans-serif"),
                marker=dict(size=8 if is_mobile else 10, color="#F43F5E", line=dict(width=2, color="#FFFFFF")),
                hovertemplate="Latest Price: <b>₹%{y:,.2f}</b> (%{x|%d-%b-%Y})<extra>Current</extra>",
            )
        )

    # Adaptive chart height
    if is_mobile:
        chart_height = 560 if is_portrait else 340
    else:
        chart_height = 480

    title_text = (
        f"<b>{symbol}</b> ({timeframe_label})"
        if is_mobile
        else f"<b>{symbol}</b> <span style='font-size:12px;color:#94A3B8'>({timeframe_label} Timeline)</span>"
    )

    # Max volume for yaxis2 range
    max_vol = float(df["Volume"].max()) if not df.empty and "Volume" in df.columns else 1000.0

    # Theme-aware colors
    if is_dark_mode:
        paper_bg = "#111827"
        plot_bg = "#0B1120"
        grid_col = "rgba(255, 255, 255, 0.12)"  # High-contrast visible gridlines
        zero_col = "rgba(255, 255, 255, 0.22)"
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
        margin=dict(l=45 if is_mobile else 65, r=15 if is_mobile else 35, t=55 if is_mobile else 50, b=35 if is_mobile else 40),
        height=chart_height,
        autosize=True,
        dragmode=False,
        title=dict(
            text=title_text,
            font=dict(size=13 if is_mobile else 16, color=title_col, family="Roboto, Inter, sans-serif"),
            x=0.01,
            y=0.97,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(color=legend_font_col, size=9 if is_mobile else 11),
            bgcolor=legend_bg,
        ),
        xaxis=dict(
            title=dict(text="Trading Date", font=dict(size=10 if is_mobile else 11, color=axis_font_col)),
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
            title=dict(text="Price (₹ INR)", font=dict(size=10 if is_mobile else 11, color=axis_font_col)),
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
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False,
            showticklabels=False,
            range=[0, max_vol * 4.5 if max_vol > 0 else 1000],
            fixedrange=True,
        ),
        hovermode="x" if not is_mobile else False,
    )

    return fig
