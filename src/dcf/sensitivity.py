"""Sensitivity analysis and scenarios."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from .projections import Assumptions
from .valuation import run_dcf


def sensitivity_table(
    assumptions: Assumptions,
    net_debt: float,
    shares: float,
    wacc_values: Iterable[float],
    growth_values: Iterable[float],
    mid_year: bool = False,
) -> pd.DataFrame:
    """Value per share for WACC (rows) and terminal growth (columns) combinations.

    Invalid combinations (WACC <= g) are returned as NaN.
    """
    wacc_values = list(wacc_values)
    growth_values = list(growth_values)
    table = pd.DataFrame(
        np.nan,
        index=pd.Index(wacc_values, name="WACC"),
        columns=pd.Index(growth_values, name="Terminal growth"),
    )
    for w in wacc_values:
        for g in growth_values:
            if w <= g:
                continue
            table.loc[w, g] = run_dcf(assumptions, w, g, net_debt, shares, mid_year=mid_year).value_per_share
    return table


def scenario_table(
    base: Assumptions,
    net_debt: float,
    shares: float,
    wacc: float,
    terminal_growth: float,
    growth_shift: float = 0.02,
    margin_shift: float = 0.03,
) -> pd.DataFrame:
    """Compare pessimistic / base / optimistic scenarios.

    The optimistic case adds ``growth_shift`` to each year's growth and
    ``margin_shift`` to the EBIT margin; the pessimistic case subtracts them.
    """
    scenarios = {
        "Pessimistic": (-growth_shift, -margin_shift),
        "Base": (0.0, 0.0),
        "Optimistic": (growth_shift, margin_shift),
    }
    rows = []
    for name, (dg, dm) in scenarios.items():
        a = base.with_changes(
            revenue_growth=[g + dg for g in base.revenue_growth],
            ebit_margin=base.ebit_margin + dm,
        )
        r = run_dcf(a, wacc, terminal_growth, net_debt, shares)
        rows.append(
            {
                "Scenario": name,
                "Enterprise value": r.enterprise_value,
                "Equity value": r.equity_value,
                "Value per share": r.value_per_share,
            }
        )
    return pd.DataFrame(rows).set_index("Scenario")
