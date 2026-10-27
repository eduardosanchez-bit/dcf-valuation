"""App Streamlit para el modelo DCF.

Ejecutar con:  streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
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
from dcf.data import CompanySnapshot, fetch_company  # noqa: E402

M = 1_000_000  # todas las cifras se muestran en millones

st.set_page_config(page_title="DCF Valuation", page_icon="📈", layout="wide")
st.title("📈 Valoración por DCF")
st.caption("Modelo de descuento de flujos de caja libres. Herramienta educativa, no es asesoramiento financiero.")

# ---------------------------------------------------------------- Datos
with st.sidebar:
    st.header("1. Empresa")
    ticker = st.text_input("Ticker", value="AAPL").strip().upper()
    if st.button("Cargar datos de Yahoo Finance", width="stretch"):
        try:
            with st.spinner("Descargando datos..."):
                st.session_state["snap"] = fetch_company(ticker)
            st.success(f"Datos cargados: {st.session_state['snap'].name}")
        except Exception as exc:  # noqa: BLE001
            st.session_state.pop("snap", None)
            st.error(f"No se pudieron cargar los datos ({exc}). Introduce los valores a mano.")

snap: CompanySnapshot | None = st.session_state.get("snap")
tag = snap.ticker if snap else "manual"

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

with st.sidebar:
    st.header("2. Hipótesis operativas")
    base_revenue = st.number_input("Ingresos último año (M)", min_value=1.0, value=float(d_rev), key=f"rev_{tag}")
    years = st.slider("Años de proyección", 3, 10, 5)
    g_start = st.slider("Crecimiento año 1 (%)", -10.0, 40.0, 8.0, 0.5) / 100
    g_end = st.slider("Crecimiento último año (%)", -5.0, 20.0, 3.0, 0.5) / 100
    ebit_margin = st.slider("Margen EBIT (%)", -10.0, 60.0, float(round(d_margin * 100, 1)), 0.5, key=f"m_{tag}") / 100
    tax_rate = st.slider("Tasa impositiva (%)", 0.0, 40.0, float(round(d_tax * 100, 1)), 0.5, key=f"t_{tag}") / 100
    da_pct = st.slider("D&A (% ingresos)", 0.0, 20.0, float(round(d_da * 100, 1)), 0.5, key=f"da_{tag}") / 100
    capex_pct = st.slider("Capex (% ingresos)", 0.0, 30.0, float(round(d_capex * 100, 1)), 0.5, key=f"cx_{tag}") / 100
    nwc_pct = st.slider("ΔNWC (% de Δ ingresos)", 0.0, 40.0, 10.0, 0.5) / 100

    st.header("3. Coste de capital")
    rf = st.slider("Tasa libre de riesgo (%)", 0.0, 8.0, 4.0, 0.1) / 100
    erp = st.slider("Prima de riesgo de mercado (%)", 2.0, 9.0, 5.0, 0.1) / 100
    beta = st.slider("Beta", 0.2, 2.5, float(round(min(max(d_beta, 0.2), 2.5), 2)), 0.05, key=f"b_{tag}")
    kd = st.slider("Coste de la deuda antes de impuestos (%)", 0.0, 12.0, 5.0, 0.1) / 100

    st.header("4. Balance y mercado")
    market_cap = st.number_input("Capitalización (M)", min_value=1.0, value=float(d_mcap), key=f"mc_{tag}")
    debt = st.number_input("Deuda total (M)", min_value=0.0, value=float(d_debt), key=f"d_{tag}")
    cash = st.number_input("Caja (M)", min_value=0.0, value=float(d_cash), key=f"c_{tag}")
    shares = st.number_input("Acciones (M)", min_value=0.001, value=float(d_shares), key=f"s_{tag}")
    price = st.number_input("Precio actual", min_value=0.01, value=float(d_price), key=f"p_{tag}")

    st.header("5. Valor terminal")
    terminal_growth = st.slider("Crecimiento terminal (%)", 0.0, 5.0, 2.5, 0.1) / 100
    use_multiple = st.checkbox("Usar múltiplo de salida EV/EBITDA")
    exit_multiple = st.slider("Múltiplo EV/EBITDA", 3.0, 30.0, 12.0, 0.5) if use_multiple else None
    mid_year = st.checkbox("Convención de mitad de año")

# ---------------------------------------------------------------- Cálculo
ke = capm_cost_of_equity(rf, beta, erp)
wacc_calc = compute_wacc(market_cap, debt, ke, kd, tax_rate)

with st.sidebar:
    override = st.checkbox("Fijar WACC manualmente")
    wacc_value = st.slider("WACC (%)", 3.0, 20.0, float(round(wacc_calc * 100, 2)), 0.1) / 100 if override else wacc_calc

if wacc_value <= terminal_growth and not use_multiple:
    st.error("El WACC debe ser mayor que el crecimiento terminal. Ajusta las hipótesis.")
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

# ---------------------------------------------------------------- Resultados
if snap:
    st.subheader(f"{snap.name} ({snap.ticker})")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Valor intrínseco por acción", f"{result.value_per_share:,.2f}")
c2.metric("Precio de mercado", f"{price:,.2f}")
c3.metric("Potencial", f"{result.upside(price):+.1%}")
c4.metric("WACC", f"{result.wacc:.2%}", help=f"Coste del equity (CAPM): {ke:.2%} · Coste de deuda neto: {after_tax_cost_of_debt(kd, tax_rate):.2%}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Valor de empresa (M)", f"{result.enterprise_value:,.0f}")
c6.metric("Deuda neta (M)", f"{net_debt:,.0f}")
c7.metric("Valor del equity (M)", f"{result.equity_value:,.0f}")
c8.metric("Peso del valor terminal", f"{result.terminal_value_share:.0%}")

if result.terminal_value_share > 0.75:
    st.warning("El valor terminal supone más del 75 % del valor de empresa: la valoración depende mucho de las hipótesis a largo plazo.")

tab_proj, tab_sens, tab_scen = st.tabs(["Proyección", "Sensibilidad", "Escenarios"])

with tab_proj:
    proj = result.projections
    fig = go.Figure()
    fig.add_bar(x=proj.index, y=proj["fcf"], name="FCF")
    fig.add_scatter(x=proj.index, y=proj["pv_fcf"], name="FCF descontado", mode="lines+markers")
    fig.update_layout(xaxis_title="Año", yaxis_title="Millones", height=380, margin=dict(t=20))
    st.plotly_chart(fig, width="stretch")
    st.dataframe(
        proj.rename(
            columns={
                "revenue": "Ingresos", "growth": "Crecimiento", "ebit": "EBIT", "nopat": "NOPAT",
                "da": "D&A", "capex": "Capex", "delta_nwc": "ΔNWC", "fcf": "FCF",
                "discount_factor": "Factor desc.", "pv_fcf": "VA del FCF",
            }
        ).style.format({"Crecimiento": "{:.1%}", "Factor desc.": "{:.4f}"}, precision=1),
        width="stretch",
    )

with tab_sens:
    st.write("Valor por acción según WACC (filas) y crecimiento terminal (columnas).")
    waccs = [round(wacc_value + d, 4) for d in (-0.02, -0.01, 0.0, 0.01, 0.02)]
    growths = [round(terminal_growth + d, 4) for d in (-0.01, -0.005, 0.0, 0.005, 0.01)]
    table = sensitivity_table(assumptions, net_debt, shares, waccs, growths, mid_year)
    heat = px.imshow(
        table.values,
        x=[f"{g:.1%}" for g in growths],
        y=[f"{w:.1%}" for w in waccs],
        text_auto=".2f",
        color_continuous_scale="RdYlGn",
        aspect="auto",
        labels=dict(x="Crecimiento terminal", y="WACC", color="€/acción"),
    )
    heat.update_layout(height=380, margin=dict(t=20))
    st.plotly_chart(heat, width="stretch")

with tab_scen:
    st.write("Pesimista / base / optimista: ±2 pp de crecimiento anual y ±3 pp de margen EBIT.")
    scen = scenario_table(assumptions, net_debt, shares, wacc_value, terminal_growth)
    st.dataframe(scen.style.format("{:,.2f}"), width="stretch")

with st.expander("Metodología y limitaciones"):
    st.markdown(
        """
        - **FCFF** = EBIT·(1−t) + D&A − Capex − ΔNWC.
        - **WACC** con CAPM para el coste del equity y ponderación a valores de mercado.
        - **Valor terminal** por Gordon o por múltiplo de salida; se descuenta al final del último año.
        - **Limitaciones**: hipótesis constantes de margen y reinversión, sin modelar estructura de capital
          dinámica, arrendamientos, opciones sobre acciones ni activos no operativos.
        - Los datos de Yahoo Finance pueden ser incompletos; revísalos antes de confiar en el resultado.
        """
    )
