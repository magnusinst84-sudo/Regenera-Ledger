"""
data/parsers/manifest_parser.py
Teammate 2 — Data / Matching

Parses CSV or PDF shipping manifests into a structured Pandas DataFrame.
Output schema: supplier, quantity, origin, destination, transport_mode, emissions_factor
Feeds into scope3_processor.py to build the supplier graph.
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Union

import pandas as pd

from data.parsers.pdf_extractor import extract_text_from_pdf

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Expected column aliases  →  canonical name
# ──────────────────────────────────────────────
_COLUMN_MAP: dict[str, str] = {
    # supplier
    "supplier": "supplier",
    "supplier_name": "supplier",
    # supplier_id intentionally excluded — it's a numeric ID not a name
    "vendor": "supplier",
    "vendor_name": "supplier",
    "company": "supplier",
    "company_name": "supplier",
    "partner": "supplier",
    "manufacturer": "supplier",
    "factory": "supplier",
    "plant": "supplier",
    "entity": "supplier",
    "name": "supplier",
    # quantity
    "qty": "quantity",
    "quantity": "quantity",
    "volume": "quantity",
    "amount": "quantity",
    "units": "quantity",
    "total_volume": "quantity",
    "total_volume_tons": "quantity",
    "weight": "quantity",
    "tonnes": "quantity",
    "tons": "quantity",
    "kg": "quantity",
    "shipment_qty": "quantity",
    "order_quantity": "quantity",
    # origin
    "origin": "origin",
    "source": "origin",
    "from": "origin",
    "ship_from": "origin",
    "location": "origin",
    "city": "origin",
    "country": "origin",
    "region": "origin",
    "plant_location": "origin",
    "factory_location": "origin",
    "source_location": "origin",
    "origin_country": "origin",
    "origin_city": "origin",
    "manufacturing_location": "origin",
    # destination
    "destination": "destination",
    "dest": "destination",
    "to": "destination",
    "ship_to": "destination",
    "delivery_location": "destination",
    "delivery_city": "destination",
    "destination_country": "destination",
    "receiving_location": "destination",
    # transport
    "transport": "transport_mode",
    "transport_mode": "transport_mode",
    "mode": "transport_mode",
    "shipping_mode": "transport_mode",
    "logistics_mode": "transport_mode",
    "freight_mode": "transport_mode",
    "shipment_mode": "transport_mode",
    "delivery_mode": "transport_mode",
    # emission factor
    "emissions_factor": "emissions_factor",
    "emission_factor": "emissions_factor",
    "co2_factor": "emissions_factor",
    "ef": "emissions_factor",
    "co2e_per_unit": "emissions_factor",
    "carbon_factor": "emissions_factor",
}

# Default emission factors (kg CO₂e / tonne-km) by mode
_DEFAULT_EF: dict[str, float] = {
    "road": 0.062,
    "truck": 0.062,
    "sea": 0.008,
    "ship": 0.008,
    "air": 0.602,
    "rail": 0.022,
    "train": 0.022,
    "unknown": 0.10,
}


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def parse_manifest(source: Union[str, Path, bytes, io.BytesIO]) -> pd.DataFrame:
    """
    Parse a shipping manifest from CSV or PDF into a clean DataFrame.

    Args:
        source: File path (str / Path), raw bytes, or BytesIO object.

    Returns:
        DataFrame with columns:
            supplier, quantity, origin, destination, transport_mode, emissions_factor

    Raises:
        ValueError: If the file type cannot be determined.
        RuntimeError: If parsing fails.
    """
    try:
        suffix = _detect_type(source)
        if suffix == ".csv":
            df = _parse_csv(source)
        elif suffix == ".pdf":
            df = _parse_pdf_manifest(source)
        else:
            raise ValueError(f"Unsupported manifest type: {suffix}")

        df = _normalise_columns(df)
        df = _fill_defaults(df)
        df = _validate(df)
        return df
    except Exception as exc:
        logger.error("Manifest parsing failed: %s", exc)
        raise RuntimeError(f"Manifest parsing failed: {exc}") from exc


# ──────────────────────────────────────────────
# Internals — file loading
# ──────────────────────────────────────────────

def _detect_type(source: Union[str, Path, bytes, io.BytesIO]) -> str:
    """Return '.csv' or '.pdf' based on source type / content."""
    if isinstance(source, (str, Path)):
        return Path(source).suffix.lower()
    if isinstance(source, bytes):
        # PDF magic bytes: %PDF
        return ".pdf" if source[:4] == b"%PDF" else ".csv"
    if isinstance(source, io.BytesIO):
        header = source.read(4)
        source.seek(0)
        return ".pdf" if header == b"%PDF" else ".csv"
    raise ValueError(f"Cannot detect type for: {type(source)}")


def _parse_csv(source: Union[str, Path, bytes, io.BytesIO]) -> pd.DataFrame:
    """Load CSV into DataFrame."""
    if isinstance(source, (str, Path)):
        return pd.read_csv(source)
    if isinstance(source, bytes):
        return pd.read_csv(io.BytesIO(source))
    if isinstance(source, io.BytesIO):
        source.seek(0)
        return pd.read_csv(source)
    raise ValueError("Cannot parse CSV from given source.")


def _parse_pdf_manifest(source: Union[str, Path, bytes, io.BytesIO]) -> pd.DataFrame:
    """
    Extract tabular data from a PDF manifest by parsing the raw text.
    Assumes a delimited or space-aligned table structure within the PDF.
    Falls back to a line-by-line regex parse if no clean table is found.
    """
    text = extract_text_from_pdf(source)
    return _text_to_manifest_df(text)


def _text_to_manifest_df(text: str) -> pd.DataFrame:
    """Heuristically convert raw PDF text into a manifest DataFrame."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    rows: list[dict] = []
    # Try CSV-like lines (comma or tab or pipe separated with >=4 fields)
    delimiters = [",", "\t", "|", ";"]
    for delim in delimiters:
        candidate_rows = [l.split(delim) for l in lines if l.count(delim) >= 3]
        if len(candidate_rows) >= 2:
            headers = [h.strip().lower() for h in candidate_rows[0]]
            for row in candidate_rows[1:]:
                if len(row) == len(headers):
                    rows.append(dict(zip(headers, [c.strip() for c in row])))
            if rows:
                return pd.DataFrame(rows)

    # Fallback: regex capture of keyword-value patterns per line
    pattern = re.compile(
        r"(?P<supplier>[\w\s]+?)\s*[,|]\s*"
        r"(?P<quantity>[\d.]+)\s*[,|]\s*"
        r"(?P<origin>[\w\s]+?)\s*[,|]\s*"
        r"(?P<destination>[\w\s]+?)\s*[,|]\s*"
        r"(?P<transport_mode>\w+)",
        re.IGNORECASE,
    )
    for line in lines:
        m = pattern.search(line)
        if m:
            rows.append(m.groupdict())

    if not rows:
        logger.warning("No structured rows found in PDF manifest; returning empty DataFrame.")
        return pd.DataFrame(columns=list(_COLUMN_MAP.values()))

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# Internals — normalisation & validation
# ──────────────────────────────────────────────

def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical names using _COLUMN_MAP, with fuzzy fallback."""
    # Normalise: lowercase, strip spaces, replace spaces with underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Drop supplier_id if supplier_name also exists (prefer the human-readable name)
    if "supplier_id" in df.columns and "supplier_name" in df.columns:
        df = df.drop(columns=["supplier_id"])

    # Step 1: exact alias map match
    df = df.rename(columns={k: v for k, v in _COLUMN_MAP.items() if k in df.columns})

    # De-duplicate: if renaming created duplicate column names, keep the last occurrence
    df = df.loc[:, ~df.columns.duplicated(keep="last")]

    # Step 2: fuzzy fallback — if a column name *contains* a canonical keyword, map it
    _FUZZY_KEYWORDS = {
        "supplier": "supplier",
        "vendor": "supplier",
        "manufacturer": "supplier",
        "factory": "supplier",
        "quantity": "quantity",
        "volume": "quantity",
        "weight": "quantity",
        "tonnes": "quantity",
        "tons": "quantity",
        "origin": "origin",
        "location": "origin",
        "city": "origin",
        "country": "origin",
        "from": "origin",
        "source": "origin",
        "destination": "destination",
        "dest": "destination",
        "delivery": "destination",
        "transport": "transport_mode",
        "mode": "transport_mode",
        "shipping": "transport_mode",
        "emission": "emissions_factor",
        "factor": "emissions_factor",
        "co2": "emissions_factor",
    }
    rename_map = {}
    canonical_already_present = set(df.columns)
    for col in list(df.columns):
        if col not in set(_COLUMN_MAP.values()):  # not already canonical
            for keyword, canonical in _FUZZY_KEYWORDS.items():
                if keyword in col and canonical not in canonical_already_present:
                    rename_map[col] = canonical
                    canonical_already_present.add(canonical)
                    break
    if rename_map:
        logger.info("Fuzzy column mapping applied: %s", rename_map)
        df = df.rename(columns=rename_map)

    return df


def _fill_defaults(df: pd.DataFrame) -> pd.DataFrame:
    """Add missing canonical columns with sensible defaults."""
    required = ["supplier", "quantity", "origin", "destination", "transport_mode", "emissions_factor"]
    for col in required:
        if col not in df.columns:
            df[col] = None

    # Numeric coercions
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0)

    # Fill transport_mode unknowns
    df["transport_mode"] = df["transport_mode"].fillna("unknown").str.lower().str.strip()

    # Fill emission factors from lookup table
    def _ef(row):
        if pd.notna(row["emissions_factor"]) and row["emissions_factor"] not in (None, ""):
            try:
                return float(row["emissions_factor"])
            except (ValueError, TypeError):
                pass
        mode = str(row.get("transport_mode", "unknown")).lower()
        return _DEFAULT_EF.get(mode, _DEFAULT_EF["unknown"])

    df["emissions_factor"] = df.apply(_ef, axis=1)

    return df


def _validate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where supplier or origin are missing."""
    before = len(df)
    df = df.dropna(subset=["supplier", "origin"])
    after = len(df)
    if before != after:
        logger.warning("Dropped %d rows with missing supplier/origin.", before - after)
    return df.reset_index(drop=True)


# ──────────────────────────────────────────────
# CLI helper (quick test)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python manifest_parser.py <path_to_csv_or_pdf>")
        sys.exit(1)

    result = parse_manifest(sys.argv[1])
    print(result.to_string())
