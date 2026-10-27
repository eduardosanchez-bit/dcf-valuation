"""Modelo de valoración por descuento de flujos de caja (DCF)."""

from .projections import Assumptions, fade_growth, project_fcf
from .sensitivity import scenario_table, sensitivity_table
from .valuation import DCFResult, run_dcf, terminal_value_exit_multiple, terminal_value_gordon
from .wacc import after_tax_cost_of_debt, capm_cost_of_equity, wacc

__all__ = [
    "Assumptions",
    "DCFResult",
    "after_tax_cost_of_debt",
    "capm_cost_of_equity",
    "fade_growth",
    "project_fcf",
    "run_dcf",
    "scenario_table",
    "sensitivity_table",
    "terminal_value_exit_multiple",
    "terminal_value_gordon",
    "wacc",
]

__version__ = "0.1.0"
