"""Cost of capital: CAPM, after-tax cost of debt and WACC."""

from __future__ import annotations


def capm_cost_of_equity(risk_free: float, beta: float, equity_risk_premium: float) -> float:
    """Cost of equity under CAPM: Rf + beta * ERP."""
    return risk_free + beta * equity_risk_premium


def after_tax_cost_of_debt(pre_tax_cost: float, tax_rate: float) -> float:
    """Cost of debt after the tax shield: Kd * (1 - t)."""
    if not 0 <= tax_rate < 1:
        raise ValueError("tax_rate must be in [0, 1).")
    return pre_tax_cost * (1 - tax_rate)


def wacc(
    equity_value: float,
    debt_value: float,
    cost_of_equity: float,
    pre_tax_cost_of_debt: float,
    tax_rate: float,
) -> float:
    """Weighted average cost of capital.

    WACC = E/(D+E) * Ke + D/(D+E) * Kd * (1 - t)

    ``equity_value`` and ``debt_value`` must share the same unit
    (ideally market value of equity and value of debt).
    """
    if equity_value < 0 or debt_value < 0:
        raise ValueError("equity_value and debt_value cannot be negative.")
    total = equity_value + debt_value
    if total == 0:
        raise ValueError("equity_value + debt_value must be greater than 0.")

    w_e = equity_value / total
    w_d = debt_value / total
    return w_e * cost_of_equity + w_d * after_tax_cost_of_debt(pre_tax_cost_of_debt, tax_rate)
