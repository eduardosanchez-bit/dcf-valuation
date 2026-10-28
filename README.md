# DCF Valuation

An equity valuation model based on **discounted cash flows (DCF)**, written in Python, with sensitivity analysis, scenarios and an interactive Streamlit app.

> Educational project. Not financial advice.

## Features

- **Company dropdown** with 30+ US, Spanish (IBEX) and European companies, plus any Yahoo Finance ticker or fully manual input.
- Projects **unlevered free cash flow (FCFF)** over 3–10 years from editable assumptions.
- Computes **WACC** using CAPM and market-value weights.
- **Terminal value** via perpetual growth (Gordon) or an exit EV/EBITDA multiple, with optional mid-year discounting.
- Outputs enterprise value, equity value and **intrinsic value per share** versus the market price.
- **Charts**: revenue and FCF projections, a cash-flow-to-equity waterfall, a WACC × terminal growth sensitivity heatmap, and bear/base/bull scenarios.

## Methodology

```
FCFF   = EBIT · (1 − t) + D&A − Capex − ΔNWC
Ke     = Rf + β · ERP
WACC   = E/(D+E) · Ke + D/(D+E) · Kd · (1 − t)
TV     = FCFₙ · (1 + g) / (WACC − g)          (Gordon growth)
TV     = EBITDAₙ · multiple                    (exit multiple)
EV     = Σ FCFₜ / (1 + WACC)ᵗ + TV / (1 + WACC)ⁿ
Equity = EV − net debt
```

Scenarios shift annual revenue growth by ±2 percentage points and the EBIT margin by ±3 points around the base case.

## Project structure

```
dcf-valuation/
├── app.py                # Streamlit app
├── .streamlit/config.toml
├── src/dcf/
│   ├── wacc.py           # CAPM, cost of debt, WACC
│   ├── projections.py    # assumptions and FCF projection
│   ├── valuation.py      # terminal value, EV, equity, value per share
│   ├── sensitivity.py    # sensitivity table and scenarios
│   ├── charts.py         # Plotly figures
│   ├── companies.py      # companies offered in the dropdown
│   └── data.py           # market data download (yfinance)
├── tests/                # pytest suite (results checked against hand calculations)
├── notebooks/            # examples and analysis
├── requirements.txt
└── pyproject.toml
```

## Installation

```bash
git clone https://github.com/eduardosanchez-bit/dcf-valuation.git
cd dcf-valuation
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

**Interactive app**

```bash
python -m streamlit run app.py
```

**As a library**

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
print(f"Value per share: {result.value_per_share:.2f}")
print(f"Terminal value share: {result.terminal_value_share:.0%}")

table = sensitivity_table(assumptions, 5_000, 1_000,
                          wacc_values=[w - 0.01, w, w + 0.01],
                          growth_values=[0.02, 0.025, 0.03])
```

## Tests

```bash
python -m pytest
```

The tests compare model output with hand calculations (WACC, terminal value, enterprise value) and check properties such as monotonicity of the sensitivity table.

## Limitations

- Margins and reinvestment ratios are held constant over the projection period.
- No dynamic capital structure, leases, stock options or non-operating assets.
- The terminal value usually carries most of the value; the app warns when it exceeds 75%.
- An unlevered FCF model is a poor fit for banks and insurers; the app flags financial companies.
- Yahoo Finance data can be incomplete or delayed: cross-check it against official filings.

## Roadmap

- [ ] Financial statements from SEC EDGAR
- [ ] Automatic beta and equity risk premium estimates
- [ ] Monte Carlo simulation over the assumptions
- [ ] Comparable-company multiples valuation
- [ ] Export results to Excel / PDF

## License

MIT
