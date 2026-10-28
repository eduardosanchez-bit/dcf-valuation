"""Curated list of companies offered in the app's dropdown.

Tickers follow Yahoo Finance conventions (e.g. ``ITX.MC`` for Madrid).
Any other ticker can still be typed in manually.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Company:
    ticker: str
    name: str
    sector: str

    @property
    def label(self) -> str:
        return f"{self.name} ({self.ticker}) · {self.sector}"


COMPANIES: tuple[Company, ...] = (
    # United States
    Company("AAPL", "Apple", "Technology"),
    Company("MSFT", "Microsoft", "Technology"),
    Company("GOOGL", "Alphabet", "Communication"),
    Company("AMZN", "Amazon", "Consumer"),
    Company("NVDA", "NVIDIA", "Technology"),
    Company("META", "Meta Platforms", "Communication"),
    Company("TSLA", "Tesla", "Consumer"),
    Company("NFLX", "Netflix", "Communication"),
    Company("DIS", "Walt Disney", "Communication"),
    Company("KO", "Coca-Cola", "Consumer"),
    Company("PEP", "PepsiCo", "Consumer"),
    Company("MCD", "McDonald's", "Consumer"),
    Company("NKE", "Nike", "Consumer"),
    Company("WMT", "Walmart", "Consumer"),
    Company("COST", "Costco", "Consumer"),
    Company("PG", "Procter & Gamble", "Consumer"),
    Company("JNJ", "Johnson & Johnson", "Healthcare"),
    Company("XOM", "Exxon Mobil", "Energy"),
    Company("JPM", "JPMorgan Chase", "Financials"),
    Company("V", "Visa", "Financials"),
    # Spain (IBEX 35)
    Company("ITX.MC", "Inditex", "Consumer"),
    Company("IBE.MC", "Iberdrola", "Utilities"),
    Company("TEF.MC", "Telefónica", "Communication"),
    Company("REP.MC", "Repsol", "Energy"),
    Company("AMS.MC", "Amadeus", "Technology"),
    Company("AENA.MC", "Aena", "Industrials"),
    Company("FER.MC", "Ferrovial", "Industrials"),
    Company("SAN.MC", "Banco Santander", "Financials"),
    Company("BBVA.MC", "BBVA", "Financials"),
    Company("CABK.MC", "CaixaBank", "Financials"),
    # Rest of Europe
    Company("ASML", "ASML", "Technology"),
    Company("SAP", "SAP", "Technology"),
    Company("MC.PA", "LVMH", "Consumer"),
    Company("NESN.SW", "Nestlé", "Consumer"),
)

BY_TICKER = {c.ticker: c for c in COMPANIES}
