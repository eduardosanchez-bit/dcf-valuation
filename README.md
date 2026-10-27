# DCF Valuation

Modelo de valoración de empresas por **descuento de flujos de caja (DCF)** en Python, con análisis de sensibilidad, escenarios y una app interactiva en Streamlit.

> Proyecto educativo. No constituye asesoramiento financiero.

## Qué hace

- Descarga datos de una empresa a partir de su ticker (Yahoo Finance) o permite introducirlos a mano.
- Proyecta el **flujo de caja libre a la empresa (FCFF)** a 3–10 años.
- Calcula el **WACC** con CAPM y ponderación a valores de mercado.
- Estima el **valor terminal** por crecimiento perpetuo (Gordon) o por múltiplo de salida EV/EBITDA.
- Obtiene valor de empresa, valor del equity y **valor intrínseco por acción**, comparado con el precio de mercado.
- Genera una **tabla de sensibilidad** (WACC × crecimiento terminal) y **escenarios** pesimista / base / optimista.

## Metodología

```
FCFF   = EBIT · (1 − t) + D&A − Capex − ΔNWC
Ke     = Rf + β · ERP
WACC   = E/(D+E) · Ke + D/(D+E) · Kd · (1 − t)
TV     = FCFₙ · (1 + g) / (WACC − g)          (Gordon)
TV     = EBITDAₙ · múltiplo                    (múltiplo de salida)
EV     = Σ FCFₜ / (1 + WACC)ᵗ + TV / (1 + WACC)ⁿ
Equity = EV − deuda neta
```

Opcionalmente se puede usar la convención de mitad de año para descontar los flujos.

## Estructura

```
dcf-valuation/
├── app.py                # app Streamlit
├── src/dcf/
│   ├── wacc.py           # CAPM, coste de deuda, WACC
│   ├── projections.py    # hipótesis y proyección de FCF
│   ├── valuation.py      # valor terminal, EV, equity, valor por acción
│   ├── sensitivity.py    # sensibilidad y escenarios
│   └── data.py           # descarga de datos (yfinance)
├── tests/                # tests con pytest (cálculos verificados a mano)
├── notebooks/            # ejemplos y análisis
├── requirements.txt
└── pyproject.toml
```

## Instalación

```bash
git clone https://github.com/<tu-usuario>/dcf-valuation.git
cd dcf-valuation
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

**App interactiva**

```bash
streamlit run app.py
```

**Como librería**

```python
from dcf import Assumptions, fade_growth, run_dcf, sensitivity_table, wacc, capm_cost_of_equity

ke = capm_cost_of_equity(risk_free=0.04, beta=1.1, equity_risk_premium=0.05)
w = wacc(equity_value=50_000, debt_value=10_000, cost_of_equity=ke,
         pre_tax_cost_of_debt=0.05, tax_rate=0.21)

assumptions = Assumptions(
    base_revenue=10_000,
    revenue_growth=fade_growth(0.08, 0.03, 5),
    ebit_margin=0.22,
)

result = run_dcf(assumptions, wacc=w, terminal_growth=0.025, net_debt=5_000, shares=1_000)
print(f"Valor por acción: {result.value_per_share:.2f}")
print(f"Peso del valor terminal: {result.terminal_value_share:.0%}")

table = sensitivity_table(assumptions, 5_000, 1_000,
                          wacc_values=[w - 0.01, w, w + 0.01],
                          growth_values=[0.02, 0.025, 0.03])
```

## Tests

```bash
pytest
```

Los tests comparan los resultados del modelo con cálculos hechos a mano (WACC, valor terminal, valor de empresa) y comprueban propiedades como la monotonía de la tabla de sensibilidad.

## Limitaciones

- Márgenes y ratios de reinversión constantes durante la proyección.
- No modela estructura de capital dinámica, arrendamientos, stock options ni activos no operativos.
- El valor terminal suele concentrar la mayor parte del valor; la app avisa cuando supera el 75 %.
- Los datos de Yahoo Finance pueden ser incompletos o tener retrasos: conviene contrastarlos con las cuentas oficiales.

## Próximos pasos

- [ ] Descarga de estados financieros desde SEC EDGAR
- [ ] Beta y prima de riesgo calculadas automáticamente
- [ ] Simulación Monte Carlo sobre las hipótesis
- [ ] Valoración por múltiplos comparables (comps)
- [ ] Exportar resultados a Excel / PDF

## Licencia

MIT
