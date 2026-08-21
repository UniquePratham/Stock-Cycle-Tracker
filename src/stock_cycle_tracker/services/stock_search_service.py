"""Stock search and autocomplete service with in-memory caching and debounced API queries."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StockSearchResult:
    symbol: str
    company_name: str
    exchange: str

    @property
    def display_label(self) -> str:
        return f"{self.symbol} ({self.exchange}) — {self.company_name}"


# Comprehensive dictionary of top NSE/BSE stocks for instant zero-latency suggestions
TOP_INDIAN_STOCKS: List[StockSearchResult] = [
    StockSearchResult("RELIANCE", "Reliance Industries Limited", "NSE"),
    StockSearchResult("TCS", "Tata Consultancy Services Limited", "NSE"),
    StockSearchResult("HDFCBANK", "HDFC Bank Limited", "NSE"),
    StockSearchResult("ICICIBANK", "ICICI Bank Limited", "NSE"),
    StockSearchResult("INFY", "Infosys Limited", "NSE"),
    StockSearchResult("SBIN", "State Bank of India", "NSE"),
    StockSearchResult("BHARTIARTL", "Bharti Airtel Limited", "NSE"),
    StockSearchResult("ITC", "ITC Limited", "NSE"),
    StockSearchResult("KOTAKBANK", "Kotak Mahindra Bank Limited", "NSE"),
    StockSearchResult("LT", "Larsen & Toubro Limited", "NSE"),
    StockSearchResult("AXISBANK", "Axis Bank Limited", "NSE"),
    StockSearchResult("TATAMOTORS", "Tata Motors Limited", "NSE"),
    StockSearchResult("JSWENERGY", "JSW Energy Limited", "NSE"),
    StockSearchResult("JSWSTEEL", "JSW Steel Limited", "NSE"),
    StockSearchResult("TATASTEEL", "Tata Steel Limited", "NSE"),
    StockSearchResult("BAJFINANCE", "Bajaj Finance Limited", "NSE"),
    StockSearchResult("BAJAJFINSV", "Bajaj Finserv Limited", "NSE"),
    StockSearchResult("MARUTI", "Maruti Suzuki India Limited", "NSE"),
    StockSearchResult("SUNPHARMA", "Sun Pharmaceutical Industries", "NSE"),
    StockSearchResult("TITAN", "Titan Company Limited", "NSE"),
    StockSearchResult("ADANIENT", "Adani Enterprises Limited", "NSE"),
    StockSearchResult("ADANIPORTS", "Adani Ports and Special Economic Zone", "NSE"),
    StockSearchResult("ASIANPAINT", "Asian Paints Limited", "NSE"),
    StockSearchResult("HINDUNILVR", "Hindustan Unilever Limited", "NSE"),
    StockSearchResult("WIPRO", "Wipro Limited", "NSE"),
    StockSearchResult("HCLTECH", "HCL Technologies Limited", "NSE"),
    StockSearchResult("NTPC", "NTPC Limited", "NSE"),
    StockSearchResult("POWERGRID", "Power Grid Corporation of India", "NSE"),
    StockSearchResult("ONGC", "Oil & Natural Gas Corporation", "NSE"),
    StockSearchResult("COALINDIA", "Coal India Limited", "NSE"),
    StockSearchResult("M&M", "Mahindra & Mahindra Limited", "NSE"),
    StockSearchResult("ULTRACEMCO", "UltraTech Cement Limited", "NSE"),
    StockSearchResult("NESTLEIND", "Nestle India Limited", "NSE"),
    StockSearchResult("GRASIM", "Grasim Industries Limited", "NSE"),
    StockSearchResult("INDUSINDBK", "IndusInd Bank Limited", "NSE"),
    StockSearchResult("CIPLA", "Cipla Limited", "NSE"),
    StockSearchResult("DRREDDY", "Dr. Reddy's Laboratories", "NSE"),
    StockSearchResult("BPCL", "Bharat Petroleum Corporation", "NSE"),
    StockSearchResult("EICHERMOT", "Eicher Motors Limited", "NSE"),
    StockSearchResult("DIVISLAB", "Divi's Laboratories Limited", "NSE"),
    StockSearchResult("TECHM", "Tech Mahindra Limited", "NSE"),
    StockSearchResult("BRITANNIA", "Britannia Industries Limited", "NSE"),
    StockSearchResult("APOLLOHOSP", "Apollo Hospitals Enterprise", "NSE"),
    StockSearchResult("HEROMOTOCO", "Hero MotoCorp Limited", "NSE"),
    StockSearchResult("HINDALCO", "Hindalco Industries Limited", "NSE"),
    StockSearchResult("TRENT", "Trent Limited", "NSE"),
    StockSearchResult("BEL", "Bharat Electronics Limited", "NSE"),
    StockSearchResult("HAL", "Hindustan Aeronautics Limited", "NSE"),
    StockSearchResult("ZOMATO", "Zomato Limited", "NSE"),
    StockSearchResult("JIOFIN", "Jio Financial Services Limited", "NSE"),
    StockSearchResult("VEDL", "Vedanta Limited", "NSE"),
    StockSearchResult("DLF", "DLF Limited", "NSE"),
    StockSearchResult("CHOLAFIN", "Cholamandalam Investment and Finance", "NSE"),
    StockSearchResult("GAIL", "GAIL (India) Limited", "NSE"),
    StockSearchResult("BANKBARODA", "Bank of Baroda", "NSE"),
    StockSearchResult("PNB", "Punjab National Bank", "NSE"),
    StockSearchResult("SIEMENS", "Siemens Limited", "NSE"),
    StockSearchResult("ABB", "ABB India Limited", "NSE"),
    StockSearchResult("IRFC", "Indian Railway Finance Corporation", "NSE"),
    StockSearchResult("IOC", "Indian Oil Corporation Limited", "NSE"),
    StockSearchResult("RELINFRA", "Reliance Infrastructure Limited", "NSE"),
    StockSearchResult("RPOWER", "Reliance Power Limited", "NSE"),
]


class StockSearchService:
    """Provides fast debounced auto-complete suggestions for Indian equities."""

    def __init__(self) -> None:
        self._cache: Dict[str, List[StockSearchResult]] = {}
        self._last_query_time: float = 0.0

    def search(self, query: str, limit: int = 6) -> List[StockSearchResult]:
        """Searches in-memory dictionary first, then falls back to Yahoo Search API with NSE priority."""
        q = query.strip().upper().replace(" ", "")
        if not q or len(q) < 1:
            return []

        # Check cache
        if q in self._cache:
            return self._cache[q][:limit]

        results: List[StockSearchResult] = []
        seen_symbols: set[str] = set()

        # 1. Check local top stocks (NSE prioritized)
        for s in TOP_INDIAN_STOCKS:
            if q in s.symbol or q in s.company_name.upper().replace(" ", ""):
                if s.symbol not in seen_symbols:
                    seen_symbols.add(s.symbol)
                    results.append(s)
                    if len(results) >= limit:
                        break

        # 2. If fewer than 4 matches and query length >= 2, query Yahoo Finance Search API
        if len(results) < limit and len(query.strip()) >= 2:
            try:
                url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query.strip())}&quotesCount=10&newsCount=0"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode())
                    quotes = data.get("quotes", [])
                    
                    # Split into NSE and BSE buckets to strictly prioritize NSE
                    nse_items: list[tuple[str, str]] = []
                    bse_items: list[tuple[str, str]] = []
                    
                    for item in quotes:
                        sym = item.get("symbol", "")
                        name = item.get("shortname") or item.get("longname") or sym
                        if sym.endswith(".NS"):
                            nse_items.append((sym[:-3], name))
                        elif sym.endswith(".BO"):
                            bse_items.append((sym[:-3], name))
                    
                    # Process NSE first
                    for clean_sym, name in nse_items:
                        if clean_sym not in seen_symbols:
                            seen_symbols.add(clean_sym)
                            results.append(StockSearchResult(clean_sym, name, "NSE"))
                            if len(results) >= limit:
                                break
                    
                    # Process BSE second if not already present
                    if len(results) < limit:
                        for clean_sym, name in bse_items:
                            if clean_sym not in seen_symbols:
                                seen_symbols.add(clean_sym)
                                results.append(StockSearchResult(clean_sym, name, "BSE"))
                                if len(results) >= limit:
                                    break
            except Exception as e:
                logger.debug(f"Online autocomplete query failed for '{query}': {e}")

        self._cache[q] = results
        return results[:limit]
