import math

import pytest

from dcf import (
    Assumptions,
    run_dcf,
    scenario_table,
    sensitivity_table,
    terminal_value_exit_multiple,
    terminal_value_gordon,
)


@pytest.fixture
def one_year():
    return Assumptions(
        base_revenue=1000,
        revenue_growth=[0.10],
        ebit_margin=0.20,
        tax_rate=0.25,
        da_pct=0.05,
        capex_pct=0.06,
        nwc_pct=0.10,
    )


@pytest.fixture
def five_year():
    return Assumptions(base_revenue=1000)


def test_gordon_terminal_value():
    assert terminal_value_gordon(100, 0.10, 0.02) == pytest.approx(1275)


def test_gordon_requires_wacc_above_growth():
    with pytest.raises(ValueError):
        terminal_value_gordon(100, 0.02, 0.02)


def test_exit_multiple_terminal_value():
    assert terminal_value_exit_multiple(275, 8) == pytest.approx(2200)


def test_dcf_gordon_matches_hand_calculation(one_year):
    # FCF=144 -> PV=144/1.1; TV=144*1.02/0.08=1836 -> PV=1836/1.1; EV=1980/1.1=1800
    r = run_dcf(one_year, wacc=0.10, terminal_growth=0.02, net_debt=300, shares=100)
    assert r.enterprise_value == pytest.approx(1800)
    assert r.equity_value == pytest.approx(1500)
    assert r.value_per_share == pytest.approx(15)
    assert r.terminal_value_share == pytest.approx(1836 / 1980)


def test_dcf_exit_multiple_matches_hand_calculation(one_year):
    # EBITDA = 220 + 55 = 275; TV = 2200; EV = (144 + 2200)/1.1
    r = run_dcf(one_year, 0.10, 0.02, 0, 100, exit_multiple=8)
    assert r.enterprise_value == pytest.approx((144 + 2200) / 1.1)
    assert r.terminal_growth is None


def test_mid_year_increases_pv_of_flows(one_year):
    end = run_dcf(one_year, 0.10, 0.02, 0, 100)
    mid = run_dcf(one_year, 0.10, 0.02, 0, 100, mid_year=True)
    assert mid.pv_fcf == pytest.approx(144 / 1.1**0.5)
    assert mid.pv_fcf > end.pv_fcf


def test_net_cash_increases_equity_value(one_year):
    with_debt = run_dcf(one_year, 0.10, 0.02, 500, 100)
    with_cash = run_dcf(one_year, 0.10, 0.02, -500, 100)
    assert with_cash.equity_value - with_debt.equity_value == pytest.approx(1000)


def test_upside(one_year):
    r = run_dcf(one_year, 0.10, 0.02, 300, 100)
    assert r.upside(10) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        r.upside(0)


def test_invalid_shares_rejected(one_year):
    with pytest.raises(ValueError):
        run_dcf(one_year, 0.10, 0.02, 0, 0)


def test_sensitivity_is_monotonic(five_year):
    waccs = [0.08, 0.09, 0.10, 0.11]
    growths = [0.01, 0.02, 0.03]
    t = sensitivity_table(five_year, 0, 100, waccs, growths)
    # higher WACC -> lower value; higher growth -> higher value
    for g in growths:
        col = t[g].to_numpy()
        assert all(col[i] > col[i + 1] for i in range(len(col) - 1))
    for w in waccs:
        row = t.loc[w].to_numpy()
        assert all(row[i] < row[i + 1] for i in range(len(row) - 1))


def test_sensitivity_marks_invalid_cells_as_nan(five_year):
    t = sensitivity_table(five_year, 0, 100, [0.02, 0.10], [0.03])
    assert math.isnan(t.loc[0.02, 0.03])
    assert not math.isnan(t.loc[0.10, 0.03])


def test_scenarios_are_ordered(five_year):
    s = scenario_table(five_year, 0, 100, 0.10, 0.02)
    v = s["Value per share"]
    assert v["Pessimistic"] < v["Base"] < v["Optimistic"]
