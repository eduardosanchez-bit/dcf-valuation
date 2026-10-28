"""Streamlit app for the DCF model.

Run with:  python -m streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dcf import (  # noqa: E402
    Assumptions,
    after_tax_cost_of_debt,
    capm_cost_of_equity,
    fade_growth,
    run_dcf,
    scenario_table,
    sensitivity_table,
    wacc as compute_wacc,
)
from dcf import charts  # noqa: E402
from dcf.companies import BY_TICKER, COMPANIES  # noqa: E402
from dcf.data import CompanySnapshot, fetch_company  # noqa: E402

M = 1_000_000  # figures are displayed in millions
MANUAL = "Manual input"
CUSTOM = "Other ticker…"

st.set_page_config(page_title="DCF Valuation", page_icon="📈", layout="wide")


@st.cache_data(ttl=3600, show_spinner="Fetching market data…")
def load_company(ticker: str) -> CompanySnapshot:
    return fetch_company(ticker)


def plot(fig) -> None:
    st.plotly_chart(fig, width="stretch", theme=None, config=charts.CONFIG)


# ---------------------------------------------------------------- Company
with st.sidebar:
    st.header("1. Company")
    options = [MANUAL] + [c.ticker for c in COMPANIES] + [CUSTOM]

    def option_label(opt: str) -> str:
        if opt in BY_TICKER:
            return BY_TICKER[opt].label
        return opt

    choice = st.selectbox("Select a company", options, index=1, format_func=option_label)
    if choice == CUSTOM:
        ticker = st.text_input("Yahoo Finance ticker", placeholder="e.g. ADBE or BKT.MC").strip().upper()
    elif choice == MANUAL:
        ticker = ""
    else:
        ticker = choice

snap: CompanySnapshot | None = None
if ticker:
    try:
        snap = load_company(ticker)
    except Exception as exc:  # noqa: BLE001
        st.sidebar.warning(
            f"Live data for {ticker} is unavailable right now (Yahoo Finance did not respond or the ticker is "
            "invalid). Using manual inputs instead."
        )
        with st.sidebar.expander("Error details"):
            st.code(str(exc)[:300])

tag = snap.ticker if snap else "manual"
currency = snap.currency if snap else "USD"

d_rev = snap.revenue / M if snap else 10_000.0
d_margin = snap.ebit_margin if snap else 0.20
d_tax = snap.tax_rate if snap else 0.21
d_da = snap.da_pct if snap else 0.04
d_capex = snap.capex_pct if snap else 0.05
d_debt = snap.total_debt / M if snap else 2_000.0
d_cash = snap.cash / M if snap else 1_000.0
d_mcap = snap.market_cap / M if snap else 20_000.0
d_shares = snap.shares / M if snap else 1_000.0
d_beta = snap.beta if snap else 1.0
d_price = snap.price if snap else 20.0


def clamp(value: float, low: float, high: float) -> float:
    return float(min(max(value, low), high))


with st.sidebar:
    st.header("2. Operating assumptions")
    base_revenue = st.number_input("Last year revenue (M)", min_value=1.0, value=float(d_rev), key=f"rev_{tag}")
    years = st.slider("Projection years", 3, 10, 5)
    g_start = st.slider("Year 1 growth (%)", -10.0, 40.0, 8.0, 0.5) / 100
    g_end = st.slider("Final year growth (%)", -5.0, 20.0, 3.0, 0.5) / 100
    ebit_margin = st.slider("EBIT margin (%)", -10.0, 60.0, clamp(round(d_margin * 100, 1), -10, 60), 0.5, key=f"m_{tag}") / 100
    tax_rate = st.slider("Tax rate (%)", 0.0, 40.0, clamp(round(d_tax * 100, 1), 0, 40), 0.5, key=f"t_{tag}") / 100
    da_pct = st.slider("D&A (% of revenue)", 0.0, 20.0, clamp(round(d_da * 100, 1), 0, 20), 0.5, key=f"da_{tag}") / 100
    capex_pct = st.slider("Capex (% of revenue)", 0.0, 30.0, clamp(round(d_capex * 100, 1), 0, 30), 0.5, key=f"cx_{tag}") / 100
    nwc_pct = st.slider("Δ NWC (% of Δ revenue)", 0.0, 40.0, 10.0, 0.5) / 100

    st.header("3. Cost of capital")
    rf = st.slider("Risk-free rate (%)", 0.0, 8.0, 4.0, 0.1) / 100
    erp = st.slider("Equity risk premium (%)", 2.0, 9.0, 5.0, 0.1) / 100
    beta = st.slider("Beta", 0.2, 2.5, clamp(round(d_beta, 2), 0.2, 2.5), 0.05, key=f"b_{tag}")
    kd = st.slider("Pre-tax cost of debt (%)", 0.0, 12.0, 5.0, 0.1) / 100

    st.header("4. Balance sheet & market")
    market_cap = st.number_input("Market cap (M)", min_value=1.0, value=float(d_mcap), key=f"mc_{tag}")
    debt = st.number_input("Total debt (M)", min_value=0.0, value=float(d_debt), key=f"d_{tag}")
    cash = st.number_input("Cash (M)", min_value=0.0, value=float(d_cash), key=f"c_{tag}")
    shares = st.number_input("Shares outstanding (M)", min_value=0.001, value=float(d_shares), key=f"s_{tag}")
    price = st.number_input("Current share price", min_value=0.01, value=float(d_price), key=f"p_{tag}")

    st.header("5. Terminal value")
    terminal_growth = st.slider("Terminal growth (%)", 0.0, 5.0, 2.5, 0.1) / 100
    use_multiple = st.checkbox("Use exit EV/EBITDA multiple")
    exit_multiple = st.slider("EV/EBITDA multiple", 3.0, 30.0, 12.0, 0.5) if use_multiple else None
    mid_year = st.checkbox("Mid-year discounting convention")

# ---------------------------------------------------------------- Calculation
ke = capm_cost_of_equity(rf, beta, erp)
wacc_calc = compute_wacc(market_cap, debt, ke, kd, tax_rate)

with st.sidebar:
    override = st.checkbox("Set WACC manually")
    wacc_value = (
        st.slider("WACC (%)", 3.0, 20.0, clamp(round(wacc_calc * 100, 2), 3, 20), 0.1) / 100 if override else wacc_calc
    )

st.title("DCF Valuation")
st.caption("Discounted free cash flow model. Educational tool, not financial advice.")

if wacc_value <= terminal_growth and not use_multiple:
    st.error("WACC must be greater than terminal growth. Adjust the assumptions.")
    st.stop()

assumptions = Assumptions(
    base_revenue=base_revenue,
    revenue_growth=fade_growth(g_start, g_end, years),
    ebit_margin=ebit_margin,
    tax_rate=tax_rate,
    da_pct=da_pct,
    capex_pct=capex_pct,
    nwc_pct=nwc_pct,
)
net_debt = debt - cash
result = run_dcf(assumptions, wacc_value, terminal_growth, net_debt, shares, exit_multiple, mid_year)

# ---------------------------------------------------------------- Results
if snap:
    st.subheader(f"{snap.name} ({snap.ticker})")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Intrinsic value per share", f"{result.value_per_share:,.2f}")
c2.metric("Market price", f"{price:,.2f}")
c3.metric("Upside / downside", f"{result.upside(price):+.1%}")
c4.metric(
    "WACC",
    f"{result.wacc:.2%}",
    help=f"Cost of equity (CAPM): {ke:.2%} · After-tax cost of debt: {after_tax_cost_of_debt(kd, tax_rate):.2%}",
)

c5, c6, c7, c8 = st.columns(4)
c5.metric(f"Enterprise value ({currency} M)", f"{result.enterprise_value:,.0f}")
c6.metric(f"Net debt ({currency} M)", f"{net_debt:,.0f}")
c7.metric(f"Equity value ({currency} M)", f"{result.equity_value:,.0f}")
c8.metric("Terminal value share", f"{result.terminal_value_share:.0%}")

sector = (snap.sector if snap and snap.sector else BY_TICKER[ticker].sector if ticker in BY_TICKER else "").lower()
if "financ" in sector:
    st.info(
        "Banks, insurers and other financial companies are poorly suited to an unlevered FCF model "
        "(debt is part of their operations). Treat this result with caution."
    )
if result.terminal_value_share > 0.75:
    st.warning("The terminal value is over 75% of enterprise value: the result depends heavily on long-term assumptions.")

tab_proj, tab_val, tab_sens, tab_scen = st.tabs(["Projection", "Valuation", "Sensitivity", "Scenarios"])

with tab_proj:
    left, right = st.columns(2)
    with left:
        plot(charts.revenue_chart(result.projections, currency))
    with right:
        plot(charts.fcf_chart(result.projections, currency))
    with st.expander("Projection table"):
        st.dataframe(
            result.projections.rename(
                columns={
                    "revenue": "Revenue",
                    "growth": "Growth",
                    "ebit": "EBIT",
                    "nopat": "NOPAT",
                    "da": "D&A",
                    "capex": "Capex",
                    "delta_nwc": "Δ NWC",
                    "fcf": "FCF",
                    "discount_factor": "Discount factor",
                    "pv_fcf": "PV of FCF",
                }
            ).style.format({"Growth": "{:.1%}", "Discount factor": "{:.4f}"}, precision=1),
            width="stretch",
        )

with tab_val:
    plot(charts.ev_bridge(result, currency))
    st.caption(
        "Present value of projected cash flows plus present value of the terminal value gives enterprise value; "
        "subtracting net debt gives equity value."
    )

with tab_sens:
    waccs = [round(wacc_value + d, 4) for d in (-0.02, -0.01, 0.0, 0.01, 0.02)]
    growths = [round(terminal_growth + d, 4) for d in (-0.01, -0.005, 0.0, 0.005, 0.01)]
    table = sensitivity_table(assumptions, net_debt, shares, waccs, growths, mid_year)
    plot(charts.sensitivity_heatmap(table, price, waccs[2], growths[2]))
    st.caption(
        f"Blue cells are valued above the current price ({price:,.2f}), red cells below. "
        "The outlined cell is the base case."
    )

with tab_scen:
    scen = scenario_table(assumptions, net_debt, shares, wacc_value, terminal_growth)
    plot(charts.scenario_chart(scen, price, currency))
    st.caption("Pessimistic / optimistic: −/+ 2 pp annual revenue growth and −/+ 3 pp EBIT margin versus the base case.")
    st.dataframe(scen.style.format("{:,.2f}"), width="stretch")

with st.expander("Methodology and limitations"):
    st.markdown(
        """
        - **FCFF** = EBIT·(1−t) + D&A − Capex − ΔNWC.
        - **WACC** uses CAPM for the cost of equity, weighted at market values.
        - **Terminal value** via Gordon growth or exit multiple, discounted from the end of the last projected year.
        - **Limitations**: constant margins and reinvestment ratios, no dynamic capital structure, leases,
          stock options or non-operating assets.
        - Yahoo Finance data can be incomplete or delayed; review it before relying on the result.
        """
    )
