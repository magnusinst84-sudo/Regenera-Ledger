"""
Matching Routes
Company-to-farmer carbon credit matching with Gemini AI.
T4 infrastructure + T1 Gemini AI — INTEGRATED.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import require_role
from db import create_document, get_documents_by_field
from utils.audit_logger import log_action
from utils.integration import get_farmer_candidates, calculate_carbon_baseline

# ── T1: Gemini AI ──
from ai.gemini_client import call_gemini_async
from prompts.matching_prompt import build_matching_prompt

router = APIRouter(prefix="/api/matching", tags=["Carbon Credit Matching"])


@router.post("/")
async def match_company_to_farmers(
    user: dict = Depends(require_role("company")),
):
    """
    Match a company's carbon gap to suitable farmers using Gemini AI.
    """
    # ── T4: Get company's analysis results (In-memory sort) ──
    try:
        past_results = get_documents_by_field(
            "analysis_results", "user_id", user["id"],
            limit=50
        )
        past_results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception:
        past_results = []

    if not past_results:
        raise HTTPException(
            status_code=400,
            detail="No analysis results found. Run an ESG analysis first."
        )

    # ── T4: Calculate carbon baseline ──
    baseline = calculate_carbon_baseline(past_results)
    carbon_gap = baseline.get("delta", 0)

    # ── T4: Get all farmer candidates ──
    farmers = get_farmer_candidates()

    if not farmers:
        raise HTTPException(
            status_code=400,
            detail="No farmer profiles available for matching."
        )

    # Build farmer list for Gemini prompt
    farmer_list = []
    for f in farmers:
        est = f.get("latest_estimation", {}).get("result_json", {}) if f.get("latest_estimation") else {}
        farmer_list.append({
            "farmer_id": f.get("id", ""),
            "land_size_hectares": f.get("land_size_hectares", 0),
            "crop_type": f.get("crop_type", ""),
            "sequestration_capacity_tons": est.get("sequestration_capacity_tons", 0),
            "credibility_score": est.get("credibility_score", 0),
            "location": f.get("location", {}),
        })

    # Build company gap dict for prompt
    company_gap = {
        "credits_needed_tco2e": abs(carbon_gap) if carbon_gap else 100,
        "company_location": "India",
        "urgency": "within_1_year",
    }

    # ── T1: Gemini Matching ──
    try:
        prompt = build_matching_prompt(company_gap, farmer_list)
        result = await call_gemini_async(prompt)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=f"Gemini AI error: {e}")

    matches = result.get("ranked_matches", [])

    # ── T4: Save matching result ──
    match_id = create_document("matching_results", {
        "company_user_id": user["id"],
        "carbon_gap": carbon_gap,
        "matches_json": matches,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # ── T4: Audit log ──
    log_action(
        user_id=user["id"],
        action="farmer_matching",
        entity_type="matching_result",
        entity_id=match_id,
        details={"carbon_gap": carbon_gap, "farmer_count": len(matches)},
    )

    return {
        "id": match_id,
        "carbon_gap": carbon_gap,
        "matches": matches,
        "total_farmers_evaluated": len(farmers),
    }


# ════════════════════════════════════════════
# GET /api/matching/farmers — Get all farmers for map display
# ════════════════════════════════════════════
@router.get("/farmers")
async def get_farmers_for_map(
    user: dict = Depends(require_role("company")),
):
    """Get all farmer profiles for map display in matching page."""
    farmers = get_farmer_candidates()
    return [
        {
            "id": f.get("id", ""),
            "name": f.get("user_id", ""),
            "lat": f.get("location", {}).get("lat", 0),
            "lng": f.get("location", {}).get("lng", 0),
            "credits": f.get("latest_estimation", {}).get("sequestration_capacity_tons", 0)
                if f.get("latest_estimation") else 0,
            "crop": f.get("crop_type", ""),
            "score": f.get("latest_estimation", {}).get("credibility_score", 0)
                if f.get("latest_estimation") else 0,
        }
        for f in farmers
    ]


# ════════════════════════════════════════════
# GET /api/matching/history — Get matching history
# ════════════════════════════════════════════
@router.get("/history")
async def get_matching_history(
    user: dict = Depends(require_role("company")),
):
    """Get past matching results for the authenticated company."""
    try:
        results = get_documents_by_field(
            "matching_results", "company_user_id", user["id"],
            limit=100
        )
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception:
        results = []
    return {"results": results, "count": len(results)}
