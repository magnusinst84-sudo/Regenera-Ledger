"""
data/validators.py
Teammate 2 — Data / Matching

Shared validation and cleaning utilities used across parsers and processors.
Provides input validation for API request payloads and dataframe sanity checks.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# PDF / Text Validation
# ──────────────────────────────────────────────

class TextValidationError(ValueError):
    pass


def validate_esg_text(text: str, min_chars: int = 200) -> str:
    """
    Ensure extracted ESG text meets minimum quality requirements.

    Args:
        text:      Cleaned text from pdf_extractor.
        min_chars: Minimum acceptable character count.

    Returns:
        The validated text string.

    Raises:
        TextValidationError: If text is too short or empty.
    """
    if not text or not text.strip():
        raise TextValidationError("ESG text is empty after extraction.")
    if len(text.strip()) < min_chars:
        raise TextValidationError(
            f"ESG text too short ({len(text.strip())} chars); minimum is {min_chars}. "
            "The PDF may be scanned/image-based or contain no readable text."
        )
    return text.strip()


# ──────────────────────────────────────────────
# Manifest DataFrame Validation
# ──────────────────────────────────────────────

class ManifestValidationError(ValueError):
    pass


REQUIRED_MANIFEST_COLS = {"supplier", "quantity", "origin", "transport_mode"}


def validate_manifest_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean a manifest DataFrame.

    Returns:
        Cleaned DataFrame with valid rows.

    Raises:
        ManifestValidationError: If the DataFrame is empty or missing critical columns.
    """
    if df is None or df.empty:
        raise ManifestValidationError("Manifest DataFrame is empty.")

    missing_cols = REQUIRED_MANIFEST_COLS - set(df.columns)
    if missing_cols:
        raise ManifestValidationError(
            f"Manifest is missing required columns: {missing_cols}"
        )

    # Coerce numeric fields
    df = df.copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["emissions_factor"] = pd.to_numeric(df.get("emissions_factor", pd.Series(dtype=float)), errors="coerce")

    # Drop rows with non-positive quantity
    before = len(df)
    df = df[df["quantity"] > 0].copy()
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d manifest rows with non-positive quantity.", dropped)

    if df.empty:
        raise ManifestValidationError("No valid rows remain after cleaning.")

    return df.reset_index(drop=True)


# ──────────────────────────────────────────────
# Farmer Profile Validation
# ──────────────────────────────────────────────

class FarmerValidationError(ValueError):
    pass


REQUIRED_FARMER_KEYS = {"farmer_id", "land_size_hectares", "sequestration_capacity_tons",
                         "credibility_score", "location"}


def validate_farmer_profiles(profiles: list[dict]) -> list[dict]:
    """
    Validate a list of farmer profile dicts.

    Returns:
        List of valid profiles (invalid ones are logged and skipped).
    """
    if not profiles:
        raise FarmerValidationError("Farmer profiles list is empty.")

    valid: list[dict] = []
    for i, profile in enumerate(profiles):
        errors = []

        missing = REQUIRED_FARMER_KEYS - set(profile.keys())
        if missing:
            errors.append(f"Missing keys: {missing}")

        loc = profile.get("location", {})
        if not isinstance(loc, dict) or "lat" not in loc or "lng" not in loc:
            errors.append("Location must have 'lat' and 'lng' keys.")

        if not (0 <= float(profile.get("credibility_score", -1)) <= 100):
            errors.append("credibility_score must be between 0 and 100.")

        if float(profile.get("sequestration_capacity_tons", -1)) < 0:
            errors.append("sequestration_capacity_tons must be >= 0.")

        if errors:
            logger.warning("Farmer profile #%d invalid, skipping: %s", i, errors)
            continue
        valid.append(profile)

    if not valid:
        raise FarmerValidationError("No valid farmer profiles after validation.")

    return valid


# ──────────────────────────────────────────────
# Company Location Validation
# ──────────────────────────────────────────────

def validate_company_location(location: dict[str, Any]) -> dict[str, float]:
    """
    Validate a company location dict.

    Args:
        location: { "lat": float, "lng": float }

    Returns:
        Validated location dict.

    Raises:
        ValueError: If lat/lng are missing or out of range.
    """
    if "lat" not in location or "lng" not in location:
        raise ValueError("Company location must have 'lat' and 'lng' keys.")

    lat = float(location["lat"])
    lng = float(location["lng"])

    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} out of range [-90, 90].")
    if not (-180 <= lng <= 180):
        raise ValueError(f"Longitude {lng} out of range [-180, 180].")

    return {"lat": lat, "lng": lng}
