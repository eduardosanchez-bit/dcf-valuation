import pytest

from dcf import Assumptions, fade_growth, project_fcf


def make(**kw):
    base = dict(
        base_revenue=1000,
        revenue_growth=[0.10],
        ebit_margin=0.20,
        tax_rate=0.25,
        da_pct=0.05,
        capex_pct=0.06,
        nwc_pct=0.10,
    )
    base.update(kw)
    return Assumptions(**base)


def test_single_year_fcf_matches_hand_calculation():
    row = project_fcf(make()).loc[1]
    assert row["revenue"] == pytest.approx(1100)
    assert row["ebit"] == pytest.approx(220)
    assert row["nopat"] == pytest.approx(165)
    assert row["delta_nwc"] == pytest.approx(10)
    # 165 + 55 - 66 - 10
    assert row["fcf"] == pytest.approx(144)


def test_revenue_compounds_over_years():
    proj = project_fcf(make(revenue_growth=[0.10, 0.10]))
    assert proj.loc[2, "revenue"] == pytest.approx(1210)


def test_number_of_rows_matches_growth_list():
    assert len(project_fcf(make(revenue_growth=[0.05] * 7))) == 7


def test_fade_growth_endpoints_and_length():
    g = fade_growth(0.10, 0.02, 5)
    assert len(g) == 5
    assert g[0] == pytest.approx(0.10)
    assert g[-1] == pytest.approx(0.02)


def test_invalid_assumptions_rejected():
    with pytest.raises(ValueError):
        make(base_revenue=0)
    with pytest.raises(ValueError):
        make(revenue_growth=[])
    with pytest.raises(ValueError):
        make(tax_rate=1.2)
