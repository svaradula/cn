"""
enricher.py - Enrich FundRecord objects with calculated financial metrics.

Data source: mfapi.in (free, no API key required)
  GET https://api.mfapi.in/mf/{scheme_code}
  Returns full historical NAV data for any AMFI scheme code.

Metrics calculated:
  - 1Y / 3Y / 5Y CAGR  (Compound Annual Growth Rate)
  - Volatility          (annualised standard deviation of daily returns)
  - Sharpe Ratio        (excess return per unit of risk, assuming 6.5% risk-free rate)
  - Estimated expense ratio by category (SEBI TER caps)
"""
from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Optional

import httpx

from ingestion.amfi_loader import FundRecord

logger = logging.getLogger(__name__)

MFAPI_BASE  = "https://api.mfapi.in/mf"
RISK_FREE   = 0.065          # 6.5% - approx India 10-yr gilt yield
TRADING_DAYS = 252

# SEBI TER caps by category (approximate midpoints used as estimates)
EXPENSE_RATIO_ESTIMATES = {
    "large_cap":          1.05,
    "mid_cap":            1.40,
    "small_cap":          1.60,
    "flexi_cap":          1.30,
    "multi_cap":          1.30,
    "elss":               1.20,
    "index":              0.20,
    "etf":                0.15,
    "liquid":             0.20,
    "overnight":          0.10,
    "ultra_short":        0.40,
    "short_duration":     0.60,
    "medium_duration":    0.80,
    "long_duration":      0.90,
    "gilt":               0.50,
    "corporate_bond":     0.70,
    "credit_risk":        1.00,
    "balanced_advantage": 1.10,
    "aggressive_hybrid":  1.30,
    "conservative_hybrid":0.80,
    "arbitrage":          0.50,
    "other":              1.00,
}


def _parse_date(date_str: str) -> Optional[datetime]:
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _cagr(nav_start: float, nav_end: float, years: float) -> Optional[float]:
    """Compound Annual Growth Rate as percentage."""
    if nav_start <= 0 or years <= 0:
        return None
    return round(((nav_end / nav_start) ** (1 / years) - 1) * 100, 2)


def _sharpe(daily_returns: list[float]) -> Optional[float]:
    """Annualised Sharpe ratio using daily NAV returns."""
    if len(daily_returns) < 30:
        return None
    n    = len(daily_returns)
    mean = sum(daily_returns) / n
    var  = sum((r - mean) ** 2 for r in daily_returns) / (n - 1)
    std  = math.sqrt(var) if var > 0 else 0
    if std == 0:
        return None
    annual_return = (1 + mean) ** TRADING_DAYS - 1
    annual_std    = std * math.sqrt(TRADING_DAYS)
    return round((annual_return - RISK_FREE) / annual_std, 3)


async def fetch_nav_history(
    scheme_code: str,
    client: httpx.AsyncClient,
) -> list[dict]:
    """Fetch full NAV history from mfapi.in for a single scheme."""
    url = f"{MFAPI_BASE}/{scheme_code}"
    try:
        resp = await client.get(url, timeout=15.0)
        if resp.status_code != 200:
            return []
        data = resp.json()
        if data.get("status") != "SUCCESS":
            return []
        return data.get("data", [])          # [{date, nav}, ...] newest first
    except Exception as e:
        logger.debug("mfapi fetch failed for %s: %s", scheme_code, e)
        return []


def _calc_metrics(history: list[dict]) -> dict:
    """
    Calculate returns and Sharpe from historical NAV data.
    history is sorted newest-first: [{"date": "25-Apr-2026", "nav": "493.26"}, ...]
    """
    if not history:
        return {}

    # Parse into (date, nav) list sorted oldest-first
    parsed = []
    for row in history:
        dt = _parse_date(row.get("date", ""))
        try:
            nav = float(row["nav"])
        except (KeyError, ValueError):
            continue
        if dt and nav > 0:
            parsed.append((dt, nav))

    if not parsed:
        return {}

    parsed.sort(key=lambda x: x[0])   # oldest first
    today_nav = parsed[-1][1]
    today_dt  = parsed[-1][0]

    result = {}

    # 1Y / 3Y / 5Y returns
    for years, key in [(1, "returns_1y"), (3, "returns_3y"), (5, "returns_5y")]:
        target_dt = today_dt - timedelta(days=int(years * 365.25))
        # Find the NAV closest to the target date
        closest = min(parsed, key=lambda x: abs((x[0] - target_dt).days))
        actual_years = (today_dt - closest[0]).days / 365.25
        if actual_years >= years * 0.8:        # accept if we have 80% of desired history
            result[key] = _cagr(closest[1], today_nav, actual_years)

    # Sharpe ratio from last 1 year of daily returns
    one_yr_ago = today_dt - timedelta(days=365)
    recent = [(dt, nav) for dt, nav in parsed if dt >= one_yr_ago]
    if len(recent) >= 50:
        daily_returns = [
            (recent[i][1] / recent[i - 1][1]) - 1
            for i in range(1, len(recent))
        ]
        result["sharpe_ratio"] = _sharpe(daily_returns)

    return result


async def enrich_batch(
    records: list[FundRecord],
    max_concurrent: int = 20,
    progress_every: int = 100,
) -> list[FundRecord]:
    """
    Enrich a list of FundRecord objects with calculated metrics.
    Uses mfapi.in in parallel batches for speed.

    Args:
        records:         List of FundRecord from AMFI loader
        max_concurrent:  Max parallel HTTP requests
        progress_every:  Log progress every N records

    Returns:
        Same list with returns_1y / returns_3y / returns_5y /
        sharpe_ratio / expense_ratio populated where available.
    """
    total    = len(records)
    enriched = 0
    sem      = asyncio.Semaphore(max_concurrent)

    async def _enrich_one(record: FundRecord, client: httpx.AsyncClient) -> FundRecord:
        nonlocal enriched
        async with sem:
            history = await fetch_nav_history(record.scheme_code, client)
            metrics = _calc_metrics(history)

            if metrics.get("returns_1y") is not None:
                record.returns_1y = metrics["returns_1y"]
            if metrics.get("returns_3y") is not None:
                record.returns_3y = metrics["returns_3y"]
            if metrics.get("returns_5y") is not None:
                record.returns_5y = metrics["returns_5y"]
            if metrics.get("sharpe_ratio") is not None:
                record.sharpe_ratio = metrics["sharpe_ratio"]

            # Estimate expense ratio from SEBI TER caps if not already set
            if record.expense_ratio is None:
                record.expense_ratio = EXPENSE_RATIO_ESTIMATES.get(
                    record.sub_category, 1.0
                )

            enriched += 1
            if enriched % progress_every == 0:
                pct = enriched / total * 100
                logger.info(
                    "  Enriched %d/%d (%.0f%%)...", enriched, total, pct
                )
            return record

    logger.info("Enriching %d funds from mfapi.in (parallel=%d)...", total, max_concurrent)
    limits = httpx.Limits(max_connections=max_concurrent, max_keepalive_connections=10)

    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        tasks = [_enrich_one(r, client) for r in records]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out any exceptions (treat as unenriched records)
    final = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.debug("Enrichment failed for record %d: %s", i, r)
            final.append(records[i])
        else:
            final.append(r)

    enriched_count = sum(1 for r in final if r.returns_1y is not None)
    logger.info(
        "Enrichment complete: %d/%d funds have returns data",
        enriched_count, total,
    )
    return final