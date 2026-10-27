"""Descarga de datos financieros con yfinance y estimación de hipótesis de partida."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompanySnapshot:
    """Datos básicos de una empresa para alimentar el modelo."""

    ticker: str
    name: str
    currency: str
    price: float
    shares: float
    market_cap: float
    total_debt: float
    cash: float
    beta: float
    revenue: float
    ebit_margin: float
    tax_rate: float
    da_pct: float
    capex_pct: float

    @property
    def net_debt(self) -> float:
        return self.total_debt - self.cash


def _first_value(df, labels):
    """Primer valor disponible (último ejercicio) para alguna de las etiquetas dadas."""
    for label in labels:
        if label in df.index:
            series = df.loc[label].dropna()
            if not series.empty:
                return float(series.iloc[0])
    return None


def fetch_company(ticker: str) -> CompanySnapshot:
    """Descarga datos de Yahoo Finance y calcula ratios históricos del último ejercicio.

    Raises:
        RuntimeError: si no se pueden obtener los datos mínimos necesarios.
    """
    import yfinance as yf  # import diferido: el resto del paquete no lo necesita

    t = yf.Ticker(ticker)
    info = t.info or {}
    income = t.income_stmt
    cash_flow = t.cash_flow

    revenue = _first_value(income, ["Total Revenue", "Operating Revenue"])
    ebit = _first_value(income, ["EBIT", "Operating Income"])
    if not revenue or ebit is None:
        raise RuntimeError(f"No se pudieron obtener ingresos/EBIT para '{ticker}'.")

    pretax = _first_value(income, ["Pretax Income"])
    tax = _first_value(income, ["Tax Provision"])
    tax_rate = tax / pretax if pretax and tax is not None and pretax > 0 else 0.21
    tax_rate = min(max(tax_rate, 0.0), 0.40)

    da = _first_value(cash_flow, ["Depreciation And Amortization", "Depreciation Amortization Depletion"]) or 0.0
    capex = _first_value(cash_flow, ["Capital Expenditure"]) or 0.0

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    shares = info.get("sharesOutstanding")
    if not price or not shares:
        raise RuntimeError(f"No se pudo obtener precio/acciones para '{ticker}'.")

    return CompanySnapshot(
        ticker=ticker.upper(),
        name=info.get("longName") or ticker.upper(),
        currency=info.get("currency", "USD"),
        price=float(price),
        shares=float(shares),
        market_cap=float(info.get("marketCap") or price * shares),
        total_debt=float(info.get("totalDebt") or 0.0),
        cash=float(info.get("totalCash") or 0.0),
        beta=float(info.get("beta") or 1.0),
        revenue=revenue,
        ebit_margin=ebit / revenue,
        tax_rate=tax_rate,
        da_pct=abs(da) / revenue,
        capex_pct=abs(capex) / revenue,
    )
