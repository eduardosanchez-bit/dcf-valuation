"""Análisis de sensibilidad y escenarios."""

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
    """Valor por acción para combinaciones de WACC (filas) y crecimiento terminal (columnas).

    Las combinaciones inválidas (WACC <= g) se devuelven como NaN.
    """
    wacc_values = list(wacc_values)
    growth_values = list(growth_values)
    table = pd.DataFrame(
        np.nan,
        index=pd.Index(wacc_values, name="WACC"),
        columns=pd.Index(growth_values, name="Crecimiento terminal"),
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
    """Compara escenarios pesimista / base / optimista.

    El escenario optimista suma ``growth_shift`` al crecimiento de cada año y
    ``margin_shift`` al margen EBIT; el pesimista los resta.
    """
    scenarios = {
        "Pesimista": (-growth_shift, -margin_shift),
        "Base": (0.0, 0.0),
        "Optimista": (growth_shift, margin_shift),
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
                "Escenario": name,
                "Valor empresa": r.enterprise_value,
                "Valor equity": r.equity_value,
                "Valor por acción": r.value_per_share,
            }
        )
    return pd.DataFrame(rows).set_index("Escenario")
