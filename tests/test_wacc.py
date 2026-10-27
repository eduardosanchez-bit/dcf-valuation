import pytest

from dcf import after_tax_cost_of_debt, capm_cost_of_equity, wacc


def test_capm():
    assert capm_cost_of_equity(0.04, 1.2, 0.05) == pytest.approx(0.10)


def test_after_tax_cost_of_debt():
    assert after_tax_cost_of_debt(0.05, 0.20) == pytest.approx(0.04)


def test_after_tax_cost_of_debt_rejects_bad_tax():
    with pytest.raises(ValueError):
        after_tax_cost_of_debt(0.05, 1.0)


def test_wacc_weighted_average():
    # 60% equity a 10%, 40% deuda a 5% con t=20% -> 0.06 + 0.016
    assert wacc(600, 400, 0.10, 0.05, 0.20) == pytest.approx(0.076)


def test_wacc_all_equity_equals_cost_of_equity():
    assert wacc(1000, 0, 0.09, 0.05, 0.25) == pytest.approx(0.09)


def test_wacc_rejects_empty_capital():
    with pytest.raises(ValueError):
        wacc(0, 0, 0.1, 0.05, 0.2)
