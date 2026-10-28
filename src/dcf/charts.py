"""Plotly figures with a consistent, restrained visual style.

Design rules: one y-axis per chart, thin bars with rounded tops, hairline grid,
selective direct labels, and a fixed categorical order (blue, then orange).
Plotly is an optional dependency, so this module is not imported by ``dcf``.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .valuation import DCFResult

# Palette (light surface)
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
NEUTRAL_MID = "#f0efec"
DIV_LOW = "#ec8a89"  # red arm of the diverging scale
DIV_HIGH = "#6da7ec"  # blue arm of the diverging scale

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

CONFIG = {"displayModeBar": False}


def _style(fig: go.Figure, title: str, height: int = 360, legend: bool = False) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left", y=0.98, yanchor="top", font=dict(size=15, color=INK)),
        font=dict(family=FONT, size=12, color=INK_2),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        height=height,
        margin=dict(l=56, r=16, t=84 if legend else 60, b=40),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(color=INK_2),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=AXIS, font=dict(family=FONT, size=12, color=INK)),
        bargap=0.45,
        bargroupgap=0.08,
    )
    fig.update_xaxes(showgrid=False, linecolor=AXIS, ticks="", tickfont=dict(color=MUTED), fixedrange=True)
    fig.update_yaxes(
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=False,
        ticks="",
        tickfont=dict(color=MUTED),
        tickformat=",.0f",
        fixedrange=True,
    )
    try:  # rounded bar tops need a recent Plotly; fall back silently otherwise
        fig.update_traces(marker_cornerradius=4, selector=dict(type="bar"))
    except (ValueError, TypeError):
        pass
    return fig


def _labels(values, decimals: int = 0) -> list[str]:
    return [f"{v:,.{decimals}f}" for v in values]


def revenue_chart(projections: pd.DataFrame, currency: str = "USD") -> go.Figure:
    """Revenue for the base year (grey, actual) and each projected year (blue)."""
    growth = projections["growth"].tolist()
    base = projections["revenue"].iloc[0] / (1 + growth[0])
    x = ["Base"] + [f"Y{i}" for i in projections.index]
    y = [base] + projections["revenue"].tolist()
    notes = ["Last reported year"] + [f"{g:+.1%} vs. prior year" for g in growth]

    fig = go.Figure(
        go.Bar(
            x=x,
            y=y,
            marker_color=[AXIS] + [BLUE] * len(growth),
            text=_labels(y),
            textposition="outside",
            textfont=dict(color=INK_2),
            cliponaxis=False,
            customdata=notes,
            hovertemplate="<b>%{x}</b><br>Revenue: %{y:,.0f}<br>%{customdata}<extra></extra>",
        )
    )
    return _style(fig, f"Revenue ({currency} M)")


def fcf_chart(projections: pd.DataFrame, currency: str = "USD") -> go.Figure:
    """Free cash flow vs. its present value, year by year."""
    x = [f"Y{i}" for i in projections.index]
    fig = go.Figure()
    fig.add_bar(
        x=x,
        y=projections["fcf"],
        name="Free cash flow",
        marker_color=BLUE,
        text=_labels(projections["fcf"]),
        textposition="outside",
        textfont=dict(color=INK_2, size=11),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>FCF: %{y:,.0f}<extra></extra>",
    )
    fig.add_bar(
        x=x,
        y=projections["pv_fcf"],
        name="Present value",
        marker_color=ORANGE,
        hovertemplate="<b>%{x}</b><br>Present value: %{y:,.0f}<extra></extra>",
    )
    return _style(fig, f"Free cash flow ({currency} M)", legend=True)


def ev_bridge(result: DCFResult, currency: str = "USD") -> go.Figure:
    """Waterfall from present values to enterprise value and equity value."""
    steps = [
        ("PV of cash flows", result.pv_fcf, "relative"),
        ("PV of terminal value", result.pv_terminal_value, "relative"),
        ("Enterprise value", result.enterprise_value, "total"),
        ("Net debt" if result.net_debt >= 0 else "Net cash", -result.net_debt, "relative"),
        ("Equity value", result.equity_value, "total"),
    ]
    text = [f"{v:+,.0f}" if m == "relative" else f"{v:,.0f}" for _, v, m in steps]
    fig = go.Figure(
        go.Waterfall(
            x=[s[0] for s in steps],
            y=[s[1] for s in steps],
            measure=[s[2] for s in steps],
            text=text,
            textposition="outside",
            textfont=dict(color=INK_2),
            cliponaxis=False,
            increasing=dict(marker=dict(color=BLUE)),
            decreasing=dict(marker=dict(color=ORANGE)),
            totals=dict(marker=dict(color=INK_2)),
            connector=dict(line=dict(color=AXIS, width=1)),
            hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(waterfallgap=0.45)
    return _style(fig, f"From cash flows to equity value ({currency} M)")


def sensitivity_heatmap(table: pd.DataFrame, price: float, base_wacc: float, base_growth: float) -> go.Figure:
    """Value per share by WACC (rows) and terminal growth (columns).

    Colour is diverging around the market price: blue above, red below.
    The base case is outlined.
    """
    z = table.values.astype(float)
    text = [["n/a" if v != v else f"{v:,.2f}" for v in row] for row in z]
    xs = [f"{g:.1%}" for g in table.columns]
    ys = [f"{w:.1%}" for w in table.index]

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=xs,
            y=ys,
            text=text,
            texttemplate="%{text}",
            textfont=dict(color=INK, size=13),
            colorscale=[[0, DIV_LOW], [0.5, NEUTRAL_MID], [1, DIV_HIGH]],
            zmid=price,
            showscale=False,
            xgap=3,
            ygap=3,
            hovertemplate="WACC %{y} · growth %{x}<br>Value per share: %{text}<extra></extra>",
        )
    )
    _style(fig, "Value per share: WACC vs. terminal growth")
    # Labels like "2.5%" look numeric to Plotly, so force categorical axes.
    fig.update_xaxes(
        type="category", title=dict(text="Terminal growth", font=dict(color=MUTED)), side="bottom", showline=False
    )
    fig.update_yaxes(type="category", title=dict(text="WACC", font=dict(color=MUTED)), autorange="reversed", showgrid=False)

    try:
        col = list(table.columns).index(base_growth)
        row = list(table.index).index(base_wacc)
        fig.add_shape(
            type="rect",
            x0=col - 0.5,
            x1=col + 0.5,
            y0=row - 0.5,
            y1=row + 0.5,
            line=dict(color=INK, width=2),
            fillcolor="rgba(0,0,0,0)",
        )
    except ValueError:
        pass
    return fig


def scenario_chart(scenarios: pd.DataFrame, price: float, currency: str = "USD") -> go.Figure:
    """Value per share by scenario against the current market price."""
    values = scenarios["Value per share"]
    fig = go.Figure(
        go.Bar(
            x=values.index,
            y=values.values,
            marker_color=BLUE,
            text=_labels(values.values, 2),
            textposition="outside",
            textfont=dict(color=INK_2),
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>Value per share: %{y:,.2f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=price,
        line=dict(color=INK, width=1.5, dash="dash"),
        annotation_text=f"Market<br>price<br><b>{price:,.2f}</b>",
        annotation_position="right",
        annotation_font=dict(color=INK, size=12),
    )
    _style(fig, f"Value per share by scenario ({currency})")
    fig.update_layout(margin=dict(l=56, r=72, t=60, b=40))  # room for the price label
    return fig
