"""Proyección de ingresos y flujo de caja libre (FCF) a la empresa."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import pandas as pd


@dataclass(frozen=True)
class Assumptions:
    """Hipótesis operativas del modelo. Los porcentajes se expresan en tanto por uno.

    Attributes:
        base_revenue: Ingresos del último ejercicio real.
        revenue_growth: Crecimiento anual de ingresos, uno por año proyectado.
        ebit_margin: Margen EBIT sobre ingresos.
        tax_rate: Tasa impositiva efectiva sobre el EBIT.
        da_pct: Amortización y depreciación como % de ingresos.
        capex_pct: Inversión en activos fijos (capex) como % de ingresos.
        nwc_pct: Variación del capital circulante como % de la variación de ingresos.
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
            raise ValueError("base_revenue debe ser positivo.")
        if not self.revenue_growth:
            raise ValueError("revenue_growth no puede estar vacío.")
        if not 0 <= self.tax_rate < 1:
            raise ValueError("tax_rate debe estar en [0, 1).")

    @property
    def years(self) -> int:
        return len(self.revenue_growth)

    def with_changes(self, **kwargs) -> "Assumptions":
        """Copia con campos modificados (útil para escenarios)."""
        return replace(self, **kwargs)


def fade_growth(start: float, end: float, years: int) -> list[float]:
    """Interpolación lineal del crecimiento desde ``start`` hasta ``end``."""
    if years < 1:
        raise ValueError("years debe ser >= 1.")
    if years == 1:
        return [start]
    step = (end - start) / (years - 1)
    return [start + step * i for i in range(years)]


def project_fcf(a: Assumptions) -> pd.DataFrame:
    """Proyecta el FCF a la empresa (FCFF) año a año.

    FCFF = EBIT * (1 - t) + D&A - Capex - ΔNWC
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
