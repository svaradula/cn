"""
amfi_loader.py - Fetches and parses live NAV data from AMFI India.
AMFI URL: https://www.amfiindia.com/spages/NAVAll.txt
Format: semicolon-separated, category headers interspersed.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

AMFI_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"  # moved from www. in 2024

# These are the official SEBI categories we care about
CATEGORY_MAP = {
    "large cap": ("equity", "large_cap", "moderate"),
    "mid cap": ("equity", "mid_cap", "high"),
    "small cap": ("equity", "small_cap", "high"),
    "multi cap": ("equity", "multi_cap", "high"),
    "flexi cap": ("equity", "flexi_cap", "high"),
    "elss": ("equity", "elss", "high"),
    "index fund": ("index", "index", "moderate"),
    "etf": ("index", "etf", "moderate"),
    "liquid": ("debt", "liquid", "low"),
    "overnight": ("debt", "overnight", "low"),
    "ultra short": ("debt", "ultra_short", "low"),
    "short duration": ("debt", "short_duration", "low"),
    "medium duration": ("debt", "medium_duration", "moderate"),
    "long duration": ("debt", "long_duration", "moderate"),
    "gilt": ("debt", "gilt", "moderate"),
    "corporate bond": ("debt", "corporate_bond", "moderate"),
    "credit risk": ("debt", "credit_risk", "high"),
    "balanced advantage": ("hybrid", "balanced_advantage", "moderate"),
    "aggressive hybrid": ("hybrid", "aggressive_hybrid", "high"),
    "conservative hybrid": ("hybrid", "conservative_hybrid", "low"),
    "arbitrage": ("hybrid", "arbitrage", "low"),
}


@dataclass
class FundRecord:
    scheme_code: str
    scheme_name: str
    nav: float
    date: str
    raw_category: str
    broad_category: str        # equity / debt / hybrid / index / other
    sub_category: str          # large_cap / liquid / etc.
    risk_rating: str           # low / moderate / high

    # Enriched fields (filled after AMFI fetch - requires a data vendor or estimation)
    isin_growth: str = ""
    returns_1y: Optional[float] = None
    returns_3y: Optional[float] = None
    returns_5y: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    expense_ratio: Optional[float] = None
    aum_crores: Optional[float] = None
    rating_stars: Optional[int] = None
    fund_manager: str = ""
    amc_name: str = ""

    def to_chunk_text(self) -> str:
        """
        Build a rich, information-dense text chunk for embedding.
        Quality of this text directly determines retrieval accuracy.
        """
        lines = [
            f"Mutual Fund: {self.scheme_name}",
            f"AMC: {self.amc_name or 'N/A'}",
            f"Category: {self.raw_category}",
            f"Type: {self.broad_category.title()} - {self.sub_category.replace('_', ' ').title()}",
            f"NAV: Rs.{self.nav:.4f} (as of {self.date})",
            f"Scheme Code: {self.scheme_code}",
            "",
            "Performance:",
        ]
        if self.returns_1y is not None:
            lines.append(f"  1-Year Return: {self.returns_1y:.2f}%")
        if self.returns_3y is not None:
            lines.append(f"  3-Year CAGR: {self.returns_3y:.2f}%")
        if self.returns_5y is not None:
            lines.append(f"  5-Year CAGR: {self.returns_5y:.2f}%")
        if self.sharpe_ratio is not None:
            lines.append(f"  Sharpe Ratio: {self.sharpe_ratio:.2f}")
        if self.expense_ratio is not None:
            lines.append(f"  Expense Ratio: {self.expense_ratio:.2f}%")
        if self.aum_crores is not None:
            lines.append(f"  AUM: Rs.{self.aum_crores:,.0f} Crores")
        if self.rating_stars is not None:
            lines.append(f"  Star Rating: {self.rating_stars}/5")
        lines += [
            "",
            f"Risk Profile: {self.risk_rating.title()}",
            f"Fund Manager: {self.fund_manager or 'N/A'}",
            "",
            "Suitable for:",
        ]
        if self.broad_category == "equity":
            lines.append("  Investors with 5+ year horizon seeking wealth creation.")
        elif self.broad_category == "debt":
            lines.append("  Conservative investors or short-term (< 3 year) goals.")
        elif self.broad_category == "hybrid":
            lines.append("  Moderate risk investors wanting equity + debt balance.")
        elif self.broad_category == "index":
            lines.append("  Passive investors wanting market-linked returns at low cost.")
        return "\n".join(lines)

    def to_metadata(self) -> dict:
        """Metadata stored in Pinecone alongside the vector for filtered retrieval."""
        return {
            "scheme_code": self.scheme_code,
            "scheme_name": self.scheme_name[:100],   # Pinecone metadata string limit
            "amc_name": self.amc_name[:60],
            "broad_category": self.broad_category,
            "sub_category": self.sub_category,
            "risk_rating": self.risk_rating,
            "nav": float(self.nav),
            "returns_3y": float(self.returns_3y or 0),
            "returns_5y": float(self.returns_5y or 0),
            "sharpe_ratio": float(self.sharpe_ratio or 0),
            "expense_ratio": float(self.expense_ratio or 1.5),
            "aum_crores": float(self.aum_crores or 0),
            "rating_stars": int(self.rating_stars or 3),
            "doc_type": "fund",
        }


def _classify_category(raw: str) -> tuple[str, str, str]:
    """Map AMFI's verbose category string -> (broad, sub, risk)."""
    low = raw.lower()
    for key, val in CATEGORY_MAP.items():
        if key in low:
            return val
    if "equity" in low or "growth" in low:
        return ("equity", "other_equity", "high")
    if "debt" in low or "income" in low or "bond" in low:
        return ("debt", "other_debt", "moderate")
    if "hybrid" in low or "balanced" in low:
        return ("hybrid", "other_hybrid", "moderate")
    return ("other", "other", "moderate")


async def fetch_amfi_nav(url: str = AMFI_URL) -> list[FundRecord]:
    """
    Fetch and parse AMFI NAV file.
    
    AMFI file format:
      Open Ended Schemes(Debt Schemes)
      
      Aditya Birla Sun Life Mutual Fund
      
      Scheme Code;ISIN Div Payout/IDCW Payout;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Repurchase Price;Sale Price;Date
      119551;INF209K01VN7;-;Aditya Birla Sun Life Arbitrage Fund...;12.3456;12.3456;12.3456;18-Apr-2026
    """
    logger.info("Fetching AMFI NAV data from %s", url)
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    text = response.text
    records: list[FundRecord] = []
    current_category = ""
    current_amc = ""

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Detect category headers (no semicolons, not numeric start)
        if ";" not in line:
            if line[0].isdigit():
                continue
            # Could be AMC name or category header
            if "Scheme" in line or "Open Ended" in line or "Close Ended" in line or "Interval" in line:
                current_category = line
            else:
                current_amc = line
            continue

        # Parse data rows
        parts = [p.strip() for p in line.split(";")]

        # AMFI updated their format in 2024 - dropped RepurchasePrice and SalePrice columns.
        # New format (6 fields): SchemeCode;ISIN1;ISIN2;SchemeName;NAV;Date
        # Old format (8 fields): SchemeCode;ISIN1;ISIN2;SchemeName;NAV;RepurchasePrice;SalePrice;Date
        if len(parts) < 6:
            continue

        scheme_code = parts[0]
        if not scheme_code.isdigit():
            continue  # skip header rows

        try:
            nav_str = parts[4]
            nav = float(nav_str) if nav_str and nav_str not in ("N.A.", "", "-") else None
        except ValueError:
            continue

        if nav is None or nav <= 0:
            continue

        broad, sub, risk = _classify_category(current_category)

        # Date is parts[5] in new format, parts[7] in old - handle both
        date = parts[5] if len(parts) == 6 else (parts[7] if len(parts) >= 8 else "")

        records.append(FundRecord(
            scheme_code=scheme_code,
            isin_growth=parts[1],
            scheme_name=parts[3],
            nav=nav,
            date=date,
            raw_category=current_category,
            broad_category=broad,
            sub_category=sub,
            risk_rating=risk,
            amc_name=current_amc,
        ))

    logger.info("Parsed %d fund records from AMFI", len(records))
    return records


def filter_investable_funds(records: list[FundRecord]) -> list[FundRecord]:
    """
    Keep only growth option funds - skip IDCW (dividend) variants,
    skip plans with negative NAV, skip very small/illiquid funds.
    """
    seen_names: set[str] = set()
    filtered = []

    for r in records:
        name_lower = r.scheme_name.lower()
        # Skip IDCW / Dividend variants - only keep Growth plans
        if any(kw in name_lower for kw in ["idcw", "dividend", "weekly", "monthly dividend"]):
            continue
        # Skip duplicate scheme names (different share classes of same fund)
        base_name = r.scheme_name[:60]
        if base_name in seen_names:
            continue
        seen_names.add(base_name)
        filtered.append(r)

    logger.info("After filtering: %d investable fund records", len(filtered))
    return filtered