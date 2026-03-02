"""
data/matching/farmer_matcher.py
Teammate 2 — Data / Matching

Pre-filters and ranks farmer profiles based on:
  - Geographic proximity to the company
  - Carbon sequestration capacity vs the company's carbon gap
  - Credibility score

Input:
  - farmer_profiles: list of farmer dicts (or path to sample JSON)
  - company_location: { "lat": float, "lng": float }
  - carbon_gap_tco2e: float (from carbon_calculator)
  - max_distance_km: radius filter (default 500 km)

Output: pre-filtered, ranked list of farmer dicts passed to T1's
        /api/matching route for final Gemini scoring:
[
  {
    "farmer_id": 1,
    "land_size_hectares": 50,
    "crop_type": "Rice",
    "sequestration_capacity_tons": 120,
    "credibility_score": 82,
    "location": { "lat": 28.6, "lng": 77.2 },
    "distance_km": 143.2,
    "coverage_pct": 9.7
  },
  ...
]
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Union

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def match_farmers(
    farmer_profiles: Union[list[dict], str, Path],
    company_location: dict[str, float],
    carbon_gap_tco2e: float,
    max_distance_km: float = 500.0,
    top_n: int = 20,
) -> list[dict[str, Any]]:
    """
    Pre-filter and rank farmers for Gemini matching.

    Args:
        farmer_profiles:  List of farmer dicts OR path to a JSON file.
        company_location: { "lat": float, "lng": float }
        carbon_gap_tco2e: The company's carbon gap (tCO₂e).
        max_distance_km:  Hard distance cutoff (km).
        top_n:            Maximum candidates to return for Gemini.

    Returns:
        Sorted list of farmer dicts enriched with 'distance_km' and 'coverage_pct'.
    """
    profiles = _load_profiles(farmer_profiles)
    if not profiles:
        logger.warning("No farmer profiles provided.")
        return []

    enriched = []
    for farmer in profiles:
        loc = farmer.get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng")
        if lat is None or lng is None:
            continue

        dist = _haversine(
            company_location["lat"], company_location["lng"], lat, lng
        )
        if dist > max_distance_km:
            continue

        capacity = float(farmer.get("sequestration_capacity_tons", 0))
        coverage = (capacity / carbon_gap_tco2e * 100) if carbon_gap_tco2e > 0 else 0.0

        enriched.append({
            **farmer,
            "distance_km": round(dist, 1),
            "coverage_pct": round(coverage, 2),
        })

    # Composite ranking score:
    # - Higher credibility is better
    # - Closer distance is better
    # - Coverage closer to 100% is better (sweet spot, penalise tiny coverage)
    ranked = sorted(
        enriched,
        key=lambda f: _rank_score(f, max_distance_km),
        reverse=True,
    )

    top = ranked[:top_n]
    logger.info(
        "Farmer matching: %d profiles → %d within %.0f km → top %d returned",
        len(profiles), len(enriched), max_distance_km, len(top),
    )
    return top


def load_sample_farmers(path: Union[str, Path, None] = None) -> list[dict]:
    """
    Load sample farmer data for development / demo purposes.
    Looks for data/sample/farmers.json relative to repo root, or uses
    built-in defaults if the file doesn't exist.
    """
    if path:
        return _load_profiles(path)

    # Built-in sample data (15 demo farmers across India)
    return _SAMPLE_FARMERS


# ──────────────────────────────────────────────
# Internals
# ──────────────────────────────────────────────

def _load_profiles(source: Union[list, str, Path]) -> list[dict]:
    if isinstance(source, list):
        return source
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Farmer profiles file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _rank_score(farmer: dict, max_dist: float) -> float:
    """
    Composite score in [0, 1].
    Weights: credibility 40%, distance proximity 30%, coverage 30%
    """
    credibility = float(farmer.get("credibility_score", 50)) / 100.0
    dist_score = max(0.0, 1.0 - farmer.get("distance_km", max_dist) / max_dist)
    coverage = min(farmer.get("coverage_pct", 0.0), 100.0) / 100.0
    return 0.4 * credibility + 0.3 * dist_score + 0.3 * coverage


# ──────────────────────────────────────────────
# Built-in sample farmer data (demo)
# ──────────────────────────────────────────────

_SAMPLE_FARMERS: list[dict] = [
    {"farmer_id": 1,  "land_size_hectares": 50,  "crop_type": "Rice",   "sequestration_capacity_tons": 120, "credibility_score": 82, "location": {"lat": 28.6139, "lng": 77.2090}},
    {"farmer_id": 2,  "land_size_hectares": 80,  "crop_type": "Wheat",  "sequestration_capacity_tons": 200, "credibility_score": 91, "location": {"lat": 29.0588, "lng": 76.0856}},
    {"farmer_id": 3,  "land_size_hectares": 30,  "crop_type": "Cotton", "sequestration_capacity_tons":  80, "credibility_score": 74, "location": {"lat": 21.1702, "lng": 72.8311}},
    {"farmer_id": 4,  "land_size_hectares": 120, "crop_type": "Soy",    "sequestration_capacity_tons": 310, "credibility_score": 88, "location": {"lat": 22.3072, "lng": 73.1812}},
    {"farmer_id": 5,  "land_size_hectares": 60,  "crop_type": "Maize",  "sequestration_capacity_tons": 155, "credibility_score": 79, "location": {"lat": 18.5204, "lng": 73.8567}},
    {"farmer_id": 6,  "land_size_hectares": 90,  "crop_type": "Rice",   "sequestration_capacity_tons": 230, "credibility_score": 95, "location": {"lat": 26.9124, "lng": 75.7873}},
    {"farmer_id": 7,  "land_size_hectares": 45,  "crop_type": "Wheat",  "sequestration_capacity_tons": 105, "credibility_score": 67, "location": {"lat": 30.7333, "lng": 76.7794}},
    {"farmer_id": 8,  "land_size_hectares": 200, "crop_type": "Forest", "sequestration_capacity_tons": 600, "credibility_score": 97, "location": {"lat": 12.9716, "lng": 77.5946}},
    {"farmer_id": 9,  "land_size_hectares": 35,  "crop_type": "Cotton", "sequestration_capacity_tons":  88, "credibility_score": 72, "location": {"lat": 17.3850, "lng": 78.4867}},
    {"farmer_id": 10, "land_size_hectares": 55,  "crop_type": "Soy",    "sequestration_capacity_tons": 140, "credibility_score": 83, "location": {"lat": 23.0225, "lng": 72.5714}},
    {"farmer_id": 11, "land_size_hectares": 70,  "crop_type": "Rice",   "sequestration_capacity_tons": 175, "credibility_score": 86, "location": {"lat": 25.3176, "lng": 82.9739}},
    {"farmer_id": 12, "land_size_hectares": 40,  "crop_type": "Maize",  "sequestration_capacity_tons":  95, "credibility_score": 70, "location": {"lat": 19.0760, "lng": 72.8777}},
    {"farmer_id": 13, "land_size_hectares": 100, "crop_type": "Forest", "sequestration_capacity_tons": 280, "credibility_score": 93, "location": {"lat": 15.2993, "lng": 74.1240}},
    {"farmer_id": 14, "land_size_hectares": 25,  "crop_type": "Wheat",  "sequestration_capacity_tons":  60, "credibility_score": 65, "location": {"lat": 31.1048, "lng": 77.1734}},
    {"farmer_id": 15, "land_size_hectares": 150, "crop_type": "Bamboo", "sequestration_capacity_tons": 450, "credibility_score": 90, "location": {"lat": 26.1445, "lng": 91.7362}},
]


# ──────────────────────────────────────────────
# CLI helper (quick test)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import json, sys

    company_loc = {"lat": 28.6139, "lng": 77.2090}  # Delhi
    gap = float(sys.argv[1]) if len(sys.argv) > 1 else 500.0

    results = match_farmers(
        farmer_profiles=load_sample_farmers(),
        company_location=company_loc,
        carbon_gap_tco2e=gap,
    )
    print(json.dumps(results, indent=2))
