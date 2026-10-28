"""Terminal value, enterprise value and value per share."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .projections import Assumptions, project_fcf


def terminal_value_gordon(last_fcf: float, wacc: float, terminal_growth: float) -> float:
    """Terminal value via perpetual growth (Gordon): FCF_N * (1 + g) / (WACC - g)."""
    if wacc <= terminal_growth:
        raise ValueError("WACC must be greater than the terminal growth rate.")
    return last_fcf * (1 + terminal_growth) / (wacc - terminal_growth)


def terminal_value_exit_multiple(last_metric: float, multiple: float) -> float:
    """Terminal value via exit multiple (e.g. final-year EBITDA * EV/EBITDA)."""
    if multiple <= 0:
        raise ValueError("The multiple must be positive.")
    return last_metric * multiple


@dataclass(frozen=True)
class DCFResult:
    """Output of a DCF valuation."""

    projections: pd.DataFrame
    wacc: float
    terminal_growth: float | None
    terminal_value: float
    pv_fcf: float
    pv_terminal_value: float
    enterprise_value: float
    net_debt: float
    equity_value: float
    shares: float
    value_per_share: float

    @property
    def terminal_value_share(self) -> float:
        """Share of enterprise value coming from the terminal value."""
        return self.pv_terminal_value / self.enterprise_value if self.enterprise_value else float("nan")

    def upside(self, market_price: float) -> float:
        """Upside (+) or downside (-) versus the market price."""
        if market_price <= 0:
            raise ValueError("market_price must be positive.")
        return self.value_per_share / market_price - 1


def run_dcf(
    assumptions: Assumptions,
    wacc: float,
    terminal_growth: float,
    net_debt: float,
    shares: float,
    exit_multiple: float | None = None,
    mid_year: bool = False,
) -> DCFResult:
    """Run a full DCF valuation.

    Args:
        assumptions: Operating assumptions.
        wacc: Discount rate.
        terminal_growth: Perpetual growth rate (Gordon method).
        net_debt: Debt minus cash. Negative when the company has net cash.
        shares: Shares outstanding.
        exit_multiple: If given, the terminal value uses an exit EV/EBITDA
            multiple instead of the Gordon growth formula.
        mid_year: If True, cash flows are discounted at mid-year.
    """
    if shares <= 0:
        raise ValueError("shares must be positive.")

    proj = project_fcf(assumptions)
    years = proj.index.to_numpy()
    offset = 0.5 if mid_year else 0.0

    discount_factors = 1 / (1 + wacc) ** (years - offset)
    pv_fcf = float((proj["fcf"].to_numpy() * discount_factors).sum())

    last = proj.iloc[-1]
    if exit_multiple is not None:
        ebitda = last["ebit"] + last["da"]
        tv = terminal_value_exit_multiple(float(ebitda), exit_multiple)
        g_used: float | None = None
    else:
        tv = terminal_value_gordon(float(last["fcf"]), wacc, terminal_growth)
        g_used = terminal_growth

    # The terminal value is discounted from the end of the last projected year.
    n = int(years[-1])
    pv_tv = tv / (1 + wacc) ** n

    ev = pv_fcf + pv_tv
    equity = ev - net_debt

    return DCFResult(
        projections=proj.assign(discount_factor=discount_factors, pv_fcf=proj["fcf"] * discount_factors),
        wacc=wacc,
        terminal_growth=g_used,
        terminal_value=tv,
        pv_fcf=pv_fcf,
        pv_terminal_value=pv_tv,
        enterprise_value=ev,
        net_debt=net_debt,
        equity_value=equity,
        shares=shares,
        value_per_share=equity / shares,
    )
