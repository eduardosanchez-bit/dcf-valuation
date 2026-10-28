"""Revenue and free cash flow (FCF) projections."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import pandas as pd


@dataclass(frozen=True)
class Assumptions:
    """Operating assumptions. Percentages are expressed as fractions (0.05 = 5%).

    Attributes:
        base_revenue: Revenue of the last reported fiscal year.
        revenue_growth: Annual revenue growth, one entry per projected year.
        ebit_margin: EBIT margin on revenue.
        tax_rate: Effective tax rate applied to EBIT.
        da_pct: Depreciation and amortization as a share of revenue.
        capex_pct: Capital expenditure as a share of revenue.
        nwc_pct: Change in net working capital as a share of the change in revenue.
    """

    base_revenue: float
    revenue_growth: list[float] = field(default_factory=lambda: [0.08, 0.07, 0.06, 0.05, 0.04])
    ebit_margin: float = 0.20
    tax_rate: float = 0.21
    da_pct: float = 0.04
    capex_pct: float = 0.05
    nwc_pct: float = 0.10

    def __post_init__(self) -> None:
        if self.base_revenue <= 0:
            raise ValueError("base_revenue must be positive.")
        if not self.revenue_growth:
            raise ValueError("revenue_growth cannot be empty.")
        if not 0 <= self.tax_rate < 1:
            raise ValueError("tax_rate must be in [0, 1).")

    @property
    def years(self) -> int:
        return len(self.revenue_growth)

    def with_changes(self, **kwargs) -> "Assumptions":
        """Return a copy with some fields changed (handy for scenarios)."""
        return replace(self, **kwargs)


def fade_growth(start: float, end: float, years: int) -> list[float]:
    """Linearly interpolate growth from ``start`` to ``end`` over ``years`` years."""
    if years < 1:
        raise ValueError("years must be >= 1.")
    if years == 1:
        return [start]
    step = (end - start) / (years - 1)
    return [start + step * i for i in range(years)]


def project_fcf(a: Assumptions) -> pd.DataFrame:
    """Project unlevered free cash flow (FCFF) year by year.

    FCFF = EBIT * (1 - t) + D&A - Capex - change in NWC
    """
    rows = []
    prev_revenue = a.base_revenue
    for year, g in enumerate(a.revenue_growth, start=1):
        revenue = prev_revenue * (1 + g)
        ebit = revenue * a.ebit_margin
        nopat = ebit * (1 - a.tax_rate)
        da = revenue * a.da_pct
        capex = revenue * a.capex_pct
        delta_nwc = (revenue - prev_revenue) * a.nwc_pct
        fcf = nopat + da - capex - delta_nwc
        rows.append(
            {
                "year": year,
                "revenue": revenue,
                "growth": g,
                "ebit": ebit,
                "nopat": nopat,
                "da": da,
                "capex": capex,
                "delta_nwc": delta_nwc,
                "fcf": fcf,
            }
        )
        prev_revenue = revenue
    return pd.DataFrame(rows).set_index("year")
