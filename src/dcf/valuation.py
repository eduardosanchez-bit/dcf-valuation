"""Valor terminal, valor de empresa y valor por acción."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .projections import Assumptions, project_fcf


def terminal_value_gordon(last_fcf: float, wacc: float, terminal_growth: float) -> float:
    """Valor terminal por crecimiento perpetuo (Gordon): FCF_N * (1+g) / (WACC - g)."""
    if wacc <= terminal_growth:
        raise ValueError("El WACC debe ser mayor que el crecimiento terminal.")
    return last_fcf * (1 + terminal_growth) / (wacc - terminal_growth)


def terminal_value_exit_multiple(last_metric: float, multiple: float) -> float:
    """Valor terminal por múltiplo de salida (p. ej. EV/EBITDA * EBITDA del último año)."""
    if multiple <= 0:
        raise ValueError("El múltiplo debe ser positivo.")
    return last_metric * multiple


@dataclass(frozen=True)
class DCFResult:
    """Resultado de una valoración DCF."""

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
        """Peso del valor terminal sobre el valor de empresa."""
        return self.pv_terminal_value / self.enterprise_value if self.enterprise_value else float("nan")

    def upside(self, market_price: float) -> float:
        """Potencial (+) o sobrevaloración (-) frente al precio de mercado."""
        if market_price <= 0:
            raise ValueError("market_price debe ser positivo.")
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
    """Ejecuta la valoración DCF completa.

    Args:
        assumptions: Hipótesis operativas.
        wacc: Tasa de descuento.
        terminal_growth: Crecimiento perpetuo (método Gordon).
        net_debt: Deuda neta (deuda - caja). Negativa si hay caja neta.
        shares: Número de acciones en circulación.
        exit_multiple: Si se indica, el valor terminal usa EV/EBITDA de salida
            en lugar de Gordon.
        mid_year: Si es True, los flujos se descuentan a mitad de año.
    """
    if shares <= 0:
        raise ValueError("shares debe ser positivo.")

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

    # El valor terminal se descuenta al final del último año proyectado.
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
