import pytest

pytest.importorskip("plotly")

from dcf import Assumptions, run_dcf, scenario_table, sensitivity_table  # noqa: E402
from dcf import charts  # noqa: E402


@pytest.fixture
def result():
    return run_dcf(Assumptions(base_revenue=1000), 0.09, 0.025, net_debt=200, shares=100)


def test_projection_charts_build(result):
    assert len(charts.revenue_chart(result.projections).data) == 1
    assert len(charts.fcf_chart(result.projections).data) == 2


def test_ev_bridge_totals_are_consistent(result):
    fig = charts.ev_bridge(result)
    y = list(fig.data[0].y)
    assert y[0] + y[1] == pytest.approx(y[2])
    assert y[2] + y[3] == pytest.approx(y[4])


def test_heatmap_and_scenarios_build(result):
    a = Assumptions(base_revenue=1000)
    waccs = [0.08, 0.09, 0.10]
    growths = [0.02, 0.025, 0.03]
    table = sensitivity_table(a, 200, 100, waccs, growths)
    fig = charts.sensitivity_heatmap(table, price=15.0, base_wacc=0.09, base_growth=0.025)
    assert fig.data[0].zmid == 15.0
    scen = scenario_table(a, 200, 100, 0.09, 0.025)
    assert len(charts.scenario_chart(scen, price=15.0).data) == 1
