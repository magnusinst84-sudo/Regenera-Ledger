"""
data/matching/carbon_calculator.py
Teammate 2 — Data / Matching

Computes the carbon gap between:
  - Reported emissions (from the company's ESG PDF)
  - Detected emissions (calculated from the shipping manifest)

Output (shared data contract with T1 Gemini carbon-gap route and T3 gap chart):
{
  "reported": 5000.0,          # tCO₂e as claimed in the ESG report
  "detected": 6234.5,          # tCO₂e estimated from manifest data
  "delta": 1234.5,             # detected − reported  (positive = under-reporting)
  "delta_pct": 24.7,           # percentage gap
  "offset_required_tco2e": 1234.5,
  "financial_risk_exposure_usd": 30862.5,   # at $25/tCO₂e carbon price
  "greenwashing_flag": true,
  "explanation": "..."
}
"""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Carbon price used for financial risk estimation (USD / tCO₂e)
_CARBON_PRICE_USD_PER_TCO2E: float = 25.0

# Threshold above which we flag potential greenwashing (%)
_GREENWASHING_THRESHOLD_PCT: float = 10.0


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def calculate_carbon_gap(
    esg_text: str,
    manifest_df: pd.DataFrame,
    carbon_price: float = _CARBON_PRICE_USD_PER_TCO2E,
) -> dict[str, Any]:
    """
    Calculate the carbon gap between reported and detected emissions.

    Args:
        esg_text:     Cleaned ESG report text (from pdf_extractor).
        manifest_df:  Manifest DataFrame (from manifest_parser).
        carbon_price: USD per tCO₂e for financial risk calculation.

    Returns:
        Baseline comparison dict matching the shared data contract.
    """
    reported = _extract_reported_emissions(esg_text)
    detected = _calculate_detected_emissions(manifest_df)

    delta = detected - reported
    delta_pct = (delta / reported * 100) if reported > 0 else 0.0
    offset_required = max(delta, 0.0)
    financial_risk = offset_required * carbon_price
    greenwashing_flag = delta_pct > _GREENWASHING_THRESHOLD_PCT

    explanation = _build_explanation(reported, detected, delta, delta_pct, greenwashing_flag)

    result: dict[str, Any] = {
        "reported": round(reported, 2),
        "detected": round(detected, 2),
        "delta": round(delta, 2),
        "delta_pct": round(delta_pct, 2),
        "offset_required_tco2e": round(offset_required, 2),
        "financial_risk_exposure_usd": round(financial_risk, 2),
        "greenwashing_flag": greenwashing_flag,
        "explanation": explanation,
    }

    logger.info(
        "Carbon gap: reported=%.1f, detected=%.1f, delta=%.1f (%.1f%%)",
        reported, detected, delta, delta_pct,
    )
    return result


# ──────────────────────────────────────────────
# Internals
# ──────────────────────────────────────────────

def _extract_reported_emissions(text: str) -> float:
    """
    Heuristically extract the company's self-reported total emission
    figure (tCO₂e) from the ESG report text.

    Tries multiple patterns in descending confidence order.
    Falls back to 0.0 and logs a warning if nothing is found.
    """
    # Patterns in priority order — all use re.IGNORECASE on original text
    patterns = [
        # 1. "Total emissions: 5,000 tCO2e" — must NOT be followed by "scope"
        r"total\s+(?!scope)emissions?\s*[:\-–]\s*([\d,\.]+)\s*(?:t\s*CO2e?|tonnes?)",
        # 2. Summed scope line: "Total Scope 1 and 2 emissions of 5,000"
        r"scope\s*[12]\s+and\s+scope\s*[12]\s+emissions?\s+of\s+([\d,\.]+)",
        # 3. "carbon footprint of 5,000 tCO2e"
        r"carbon\s+footprint\s+of\s+([\d,\.]+)\s*(?:t\s*CO2e?|tonnes?)?",
        # 4. "GHG emissions: 5,000"
        r"ghg\s+emissions?\s*[:\-–]\s*([\d,\.]+)",
        # 5. Fallback: any number directly followed by tCO2e
        r"([\d,\.]+)\s*t\s*CO2e",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                value = float(raw)
                if 1 < value < 1_000_000_000:
                    logger.debug("Extracted reported emissions: %.1f tCO₂e", value)
                    return value
            except ValueError:
                continue

    logger.warning("Could not extract reported emissions from ESG text; defaulting to 0.0")
    return 0.0


def _calculate_detected_emissions(df: pd.DataFrame) -> float:
    """
    Estimate actual Scope 3 emissions from manifest data.
    Formula: Σ (quantity_tonnes × emissions_factor_kg_per_tkm × distance_km) / 1000
    Assumed distance = 500 km when not provided.
    """
    if df.empty:
        logger.warning("Manifest DataFrame is empty; detected emissions = 0.0")
        return 0.0

    qty = pd.to_numeric(df.get("quantity", pd.Series(dtype=float)), errors="coerce").fillna(0)
    ef = pd.to_numeric(df.get("emissions_factor", pd.Series(dtype=float)), errors="coerce").fillna(0.1)
    dist = pd.to_numeric(df.get("distance_km", pd.Series(dtype=float)), errors="coerce").fillna(500)

    return float((qty * ef * dist / 1000).sum())


def _build_explanation(
    reported: float,
    detected: float,
    delta: float,
    delta_pct: float,
    flag: bool,
) -> str:
    if reported == 0.0:
        return (
            "No explicit emission figure was found in the ESG report. "
            f"Manifest-based estimate: {detected:.1f} tCO₂e. "
            "Manual review recommended."
        )
    direction = "under-reported" if delta > 0 else "over-reported"
    severity = "significantly" if abs(delta_pct) > 20 else "slightly"
    flag_note = (
        " ⚠ Potential greenwashing detected — the gap exceeds the 10% threshold."
        if flag else
        " The gap is within acceptable reporting tolerance."
    )
    return (
        f"The company {severity} {direction} its emissions. "
        f"Reported: {reported:.1f} tCO₂e vs manifest-detected: {detected:.1f} tCO₂e "
        f"(gap: {abs(delta):.1f} tCO₂e, {abs(delta_pct):.1f}%).{flag_note}"
    )


# ──────────────────────────────────────────────
# CLI helper (quick test)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys
    from data.parsers.pdf_extractor import extract_text_from_pdf
    from data.parsers.manifest_parser import parse_manifest

    if len(sys.argv) < 3:
        print("Usage: python carbon_calculator.py <esg_pdf> <manifest_csv_or_pdf>")
        sys.exit(1)

    esg = extract_text_from_pdf(sys.argv[1])
    manifest = parse_manifest(sys.argv[2])
    result = calculate_carbon_gap(esg, manifest)
    print(json.dumps(result, indent=2))
