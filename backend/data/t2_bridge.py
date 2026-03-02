"""
data/t2_bridge.py
Teammate 2 — Integration Bridge

This is the single entry point that Teammate 1's Gemini API scripts import
to access all T2 data-processing functionality.

T1 usage:
    from data.t2_bridge import T2Bridge

    bridge = T2Bridge()
    text     = bridge.parse_esg_pdf(file_bytes)
    manifest = bridge.parse_manifest(file_bytes_or_path)
    graph    = bridge.build_scope3_graph(text, manifest)
    gap      = bridge.calculate_gap(text, manifest)
    farmers  = bridge.get_ranked_farmers(gap["detected"], company_location)
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, Union

import pandas as pd
from dotenv import load_dotenv

from data.parsers.pdf_extractor import extract_text_from_pdf
from data.parsers.manifest_parser import parse_manifest
from data.processors.scope3_processor import build_supplier_graph
from data.matching.carbon_calculator import calculate_carbon_gap
from data.matching.farmer_matcher import match_farmers, load_sample_farmers
from data.validators import (
    validate_esg_text,
    validate_manifest_df,
    validate_farmer_profiles,
    validate_company_location,
)

load_dotenv()
logger = logging.getLogger(__name__)

_DEFAULT_FARMERS_PATH = Path(__file__).parent / "sample" / "sample_farmers.json"


class T2Bridge:
    """
    Facade over all Teammate 2 data-processing modules.
    Instantiate once and call methods from Gemini API scripts.
    """

    def __init__(
        self,
        max_pdf_size: int = int(os.getenv("MAX_PDF_SIZE_BYTES", 20_971_520)),
        pdf_min_chars: int = int(os.getenv("PDF_MIN_CHARS", 200)),
        default_distance: float = float(os.getenv("DEFAULT_DISTANCE_KM", 500)),
        carbon_price: float = float(os.getenv("CARBON_PRICE_USD", 25.0)),
        farmer_max_distance: float = float(os.getenv("FARMER_MAX_DISTANCE_KM", 500)),
        farmer_top_n: int = int(os.getenv("FARMER_TOP_N", 20)),
        farmers_path: Union[str, Path, None] = None,
    ):
        self.max_pdf_size = max_pdf_size
        self.pdf_min_chars = pdf_min_chars
        self.default_distance = default_distance
        self.carbon_price = carbon_price
        self.farmer_max_distance = farmer_max_distance
        self.farmer_top_n = farmer_top_n
        self._farmers_path = Path(farmers_path) if farmers_path else _DEFAULT_FARMERS_PATH

    # ─────────────────────────────────────────
    # 1. ESG PDF / Text Parsing
    # ─────────────────────────────────────────

    def parse_esg_pdf(self, source: Union[bytes, BytesIO, str, Path]) -> str:
        """
        Extract and validate text from an ESG PDF.

        Args:
            source: Raw bytes (from FastAPI UploadFile.read()), BytesIO, or file path.

        Returns:
            Clean validated text string ready for Gemini prompt.

        Raises:
            ValueError: If the file is too large or extracted text too short.
            RuntimeError: If extraction fails.
        """
        if isinstance(source, bytes) and len(source) > self.max_pdf_size:
            raise ValueError(
                f"PDF exceeds max size ({len(source)} > {self.max_pdf_size} bytes)."
            )
        raw_text = extract_text_from_pdf(source)
        return validate_esg_text(raw_text, min_chars=self.pdf_min_chars)

    def parse_esg_text(self, text: str) -> str:
        """
        Validate pre-extracted ESG text (e.g. from a .txt file or test stub).
        Skips PDF parsing — useful for integration tests and text-only inputs.

        Returns:
            Validated text string.
        """
        return validate_esg_text(text, min_chars=self.pdf_min_chars)

    # ─────────────────────────────────────────
    # 2. Manifest Parsing
    # ─────────────────────────────────────────

    def parse_manifest(
        self, source: Union[bytes, BytesIO, str, Path]
    ) -> pd.DataFrame:
        """
        Parse and validate a shipping manifest (CSV or PDF).

        Returns:
            Clean validated DataFrame.
        """
        df = parse_manifest(source)
        return validate_manifest_df(df)

    # ─────────────────────────────────────────
    # 3. Scope 3 Supplier Graph
    # ─────────────────────────────────────────

    def build_scope3_graph(
        self,
        esg_text: str,
        manifest_df: pd.DataFrame,
        company_name: str = "Company",
    ) -> dict[str, Any]:
        """
        Build supplier network graph for T1 Gemini scope3 route + T3 viz.

        Returns:
            { nodes, edges, summary }
        """
        return build_supplier_graph(esg_text, manifest_df, company_name)

    # ─────────────────────────────────────────
    # 4. Carbon Gap Calculation
    # ─────────────────────────────────────────

    def calculate_gap(
        self,
        esg_text: str,
        manifest_df: pd.DataFrame,
    ) -> dict[str, Any]:
        """
        Calculate carbon gap and greenwashing flag.

        Returns:
            { reported, detected, delta, delta_pct, offset_required_tco2e,
              financial_risk_exposure_usd, greenwashing_flag, explanation }
        """
        return calculate_carbon_gap(esg_text, manifest_df, self.carbon_price)

    # ─────────────────────────────────────────
    # 5. Farmer Matching
    # ─────────────────────────────────────────

    def get_ranked_farmers(
        self,
        carbon_gap_tco2e: float,
        company_location: dict[str, float],
        farmer_profiles: Union[list[dict], None] = None,
    ) -> list[dict[str, Any]]:
        """
        Return a ranked list of farmers scoped to the company's carbon gap.

        Args:
            carbon_gap_tco2e:  Gap in tCO2e (from calculate_gap output).
            company_location:  { "lat": float, "lng": float }
            farmer_profiles:   Optional override; uses sample_farmers.json by default.

        Returns:
            Ranked farmer list with distance_km and coverage_pct fields added.
        """
        loc = validate_company_location(company_location)
        profiles = farmer_profiles or load_sample_farmers(self._farmers_path)
        validated = validate_farmer_profiles(profiles)
        return match_farmers(
            farmer_profiles=validated,
            company_location=loc,
            carbon_gap_tco2e=carbon_gap_tco2e,
            max_distance_km=self.farmer_max_distance,
            top_n=self.farmer_top_n,
        )

    # ─────────────────────────────────────────
    # 6. Full Pipeline (convenience)
    # ─────────────────────────────────────────

    def run_full_pipeline(
        self,
        esg_pdf: Union[bytes, BytesIO, str, Path],
        manifest: Union[bytes, BytesIO, str, Path],
        company_name: str = "Company",
        company_location: Union[dict[str, float], None] = None,
        esg_text_override: Union[str, None] = None,
    ) -> dict[str, Any]:
        """
        Run all T2 steps end-to-end. Useful for integration tests and demo.

        Args:
            esg_pdf:           PDF bytes/path (ignored if esg_text_override is set).
            manifest:          CSV/PDF path or bytes for the shipping manifest.
            company_name:      Root node label for supplier graph.
            company_location:  { "lat", "lng" } for farmer matching.
            esg_text_override: Pass a raw string to skip PDF extraction (for tests).

        Returns:
            { esg_text, manifest_df, supplier_graph, carbon_gap, farmers }
        """
        esg_text = (
            self.parse_esg_text(esg_text_override)
            if esg_text_override
            else self.parse_esg_pdf(esg_pdf)
        )
        manifest_df = self.parse_manifest(manifest)
        graph = self.build_scope3_graph(esg_text, manifest_df, company_name)
        gap = self.calculate_gap(esg_text, manifest_df)

        farmers: list[dict] = []
        if company_location:
            farmers = self.get_ranked_farmers(
                carbon_gap_tco2e=gap["detected"],
                company_location=company_location,
            )

        return {
            "esg_text": esg_text,
            "manifest_df": manifest_df,
            "supplier_graph": graph,
            "carbon_gap": gap,
            "farmers": farmers,
        }


# ── Singleton helper ──
@lru_cache(maxsize=1)
def get_t2_bridge() -> T2Bridge:
    """Returns a cached T2Bridge instance. Call once, reuse everywhere."""
    return T2Bridge()
