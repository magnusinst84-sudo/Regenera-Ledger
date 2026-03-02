"""
Integration Glue — Connects T2's data parsers into the backend pipeline.

This module bridges T2's standalone parser scripts (in backend/data/)
and the FastAPI analysis routes.

Usage in routes:
    from utils.integration import extract_text, parse_manifest, process_scope3_data
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

# Add the backend directory to Python path so we can import T2's data modules
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def extract_text(file_path: str) -> str:
    """
    Extract text from a file (PDF or TXT).
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # ── Handle Plain Text ──
    if ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Text file reading failed: {str(e)}")

    # ── Handle PDF ──
    try:
        from data.parsers.pdf_extractor import extract_text_from_pdf
        return extract_text_from_pdf(file_path)
    except ImportError:
        logger.warning("T2 pdf_extractor not available, using pdfminer fallback")
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
            return pdfminer_extract(file_path)
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {str(e)}")


def parse_manifest(file_path: str) -> dict:
    """
    Parse a shipping manifest (CSV/PDF) using T2's manifest_parser.
    Returns structured supplier data as a dict.
    """
    try:
        from data.parsers.manifest_parser import parse_manifest as t2_parse
        result = t2_parse(file_path)
        # T2 returns a DataFrame, convert to dict for route usage
        if hasattr(result, 'to_dict'):
            return {"suppliers": result.to_dict(orient="records"), "count": len(result)}
        return result
    except ImportError:
        logger.warning("T2 manifest_parser not available, using pandas fallback")
        try:
            import pandas as pd
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(file_path)
                return {"suppliers": df.to_dict(orient="records"), "count": len(df)}
            else:
                return {"error": "Manifest parser not available", "suppliers": []}
        except Exception as e:
            raise RuntimeError(f"Manifest parsing failed: {str(e)}")


def process_scope3_data(esg_text: str, supplier_data: dict) -> dict:
    """
    Cross-reference ESG report text with supplier data using T2's scope3_processor.
    Returns structured scope3 data including supplier network graph.
    """
    try:
        from data.processors.scope3_processor import build_supplier_graph
        import pandas as pd
        # If supplier_data is a dict with "suppliers" key, convert to DataFrame
        if isinstance(supplier_data, dict) and "suppliers" in supplier_data:
            df = pd.DataFrame(supplier_data["suppliers"])
        else:
            df = pd.DataFrame()
        return build_supplier_graph(esg_text, df)
    except ImportError:
        logger.warning("T2 scope3_processor not available, returning raw data")
        return {
            "esg_text": esg_text[:5000],
            "supplier_data": supplier_data,
            "preprocessed": False,
        }


def get_farmer_candidates(company_location: dict = None) -> list:
    """
    Get pre-filtered farmer candidates for matching.
    Prioritizes Firestore data, falls back to T2 sample data if DB is empty.
    """
    from db import get_all_documents, get_documents_by_field
    
    # 1. Try to get real farmers from Firestore
    try:
        farmers = get_all_documents("farmer_profiles")
        enriched_farmers = []
        
        for f in farmers:
            # Flatten location for easy Map access
            f["lat"] = f.get("location", {}).get("lat", 0)
            f["lng"] = f.get("location", {}).get("lng", 0)
            
            # ── Unified Field Mapping ──
            # Ensure owner/lead names show up for both types
            f["owner_name"] = f.get("owner_name") or f.get("name") or "Project Lead"
            f["email"] = f.get("email") or "contact@carbon-india.org"

            # Fetch latest AI estimation — sort in-memory to guarantee recency
            estimations = get_documents_by_field(
                "carbon_estimations", "farmer_id", f["id"], limit=10
            )
            estimations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            if estimations:
                est = estimations[0].get("result_json", {})
                f["category"] = est.get("project_category") or f.get("crop_type") or "Regen-Ag"
                f["price_per_ton_usd"] = est.get("yearly_credit_potential", {}).get("estimated_revenue_usd_low", 12.0)
                f["credits_available"] = est.get("sequestration_capacity_tons", 0)
                f["durability_years"] = est.get("durability_years", 25)
                f["credibility_score"] = est.get("credibility_score", 80)
                f["is_pending_audit"] = False
            else:
                # ── Live Demo Resilience ──
                # Default for manual farmers who haven't run estimation yet.
                # These fields ensure the UI doesn't crash and shows a professional 'Audit Pending' state.
                f["category"] = f.get("crop_type") or "Regen-Ag"
                f["price_per_ton_usd"] = 10.0 # Standard demo floor price
                f["credits_available"] = 150 # Placeholder demo credits
                f["durability_years"] = 25
                f["credibility_score"] = "Audit Pending" 
                f["is_pending_audit"] = True

            enriched_farmers.append(f)
        
        farmers = enriched_farmers
        if farmers:
            logger.info(f"Found {len(farmers)} farmers in Firestore")
            
    except Exception as e:
        logger.warning(f"Error fetching from Firestore ({e})")
        farmers = []

    # 3. Apply T2 matching logic if location is provided
    try:
        if company_location and farmers:
            from data.matching.farmer_matcher import match_farmers
            return match_farmers(
                farmer_profiles=farmers,
                company_location=company_location,
                carbon_gap_tco2e=100,  # Default threshold
            )
    except Exception as e:
        logger.warning(f"Matching logic failed ({e}), returning raw list")
    
    return farmers


def calculate_carbon_baseline(analysis_results: list) -> dict:
    """
    Calculate carbon baseline from past analysis results using T2's carbon_calculator.
    Falls back to extracting from the latest analysis result JSON.
    """
    try:
        from data.matching.carbon_calculator import calculate_carbon_gap
        # Use first available ESG text and manifest
        return calculate_carbon_gap("", None)
    except (ImportError, Exception):
        # Fallback: extract from latest result
        if not analysis_results:
            return {"reported": 0, "detected": 0, "delta": 0}

        latest = analysis_results[0].get("result_json", {})
        reported_emissions = latest.get("reported_emissions", {})
        reported = reported_emissions.get("total_tco2e", 0) if isinstance(reported_emissions, dict) else 0
        detected = latest.get("estimated_actual_tco2e", reported)
        return {
            "reported": reported,
            "detected": detected,
            "delta": detected - reported,
        }
