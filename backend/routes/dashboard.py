"""
Dashboard Routes — Company dashboard statistics.
"""

from fastapi import APIRouter, Depends
from middleware.auth import get_current_user, require_role
from db import get_documents_by_field

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    user: dict = Depends(require_role("company")),
):
    """
    Get company dashboard stats: latest ESG score, CO2 reported,
    risk flags, farmer matches, and recent analyses.
    """
    # 1. Try to get stats from company_profiles for speed
    profile = None
    try:
        profiles = get_documents_by_field("company_profiles", "user_id", user["id"], limit=1)
        if profiles:
            profile = profiles[0]
    except Exception:
        profile = None

    # 2. Fetch recent analyses for the list
    try:
        analyses = get_documents_by_field(
            "analysis_results", "user_id", user["id"],
            limit=50
        )
        analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception:
        analyses = []

    # Fallback to scanning analyses if profile is missing
    esg_result = None
    if not profile:
        for a in analyses:
            if a.get("analysis_type") == "esg":
                esg_result = a.get("result_json", {})
                break
    
    # 3. Fetch matching results
    try:
        matches = get_documents_by_field(
            "matching_results", "company_user_id", user["id"],
            limit=50
        )
    except Exception:
        matches = []

    if profile:
        esg_score = profile.get("latest_esg_score", 0)
        co2_reported = profile.get("reported_emissions", {}).get("total_tco2e", 0)
        # Handle None in risk_score
        risk_flags = sum(
            1 for a in analyses 
            if (a.get("result_json") or {}).get("risk_score", 0) is not None 
            and (a.get("result_json") or {}).get("risk_score", 0) > 50
        )
    else:
        raw_risk = (esg_result.get("risk_score", 0) if esg_result else 0) or 0
        greenwashing = (esg_result.get("greenwashing_score", 0) if esg_result else 0) or 0
        # ESG score = inverse of greenwashing (0 greenwash = 100 ESG)
        esg_score = max(0, 100 - int(greenwashing))
        co2_reported = (esg_result.get("reported_emissions") or {}).get("total_tco2e", 0) if esg_result else 0
        risk_flags = 1 if int(raw_risk) > 50 else 0

    return {
        "esg_score": esg_score,
        "co2_reported": co2_reported,
        "risk_flags": risk_flags,
        "farmer_matches": len(matches),
        "recent_analyses": [
            {
                "id": a["id"],
                "type": a.get("analysis_type", ""),
                "date": a.get("created_at", "")[:10] if a.get("created_at") else "—",
                # int(x or 0) handles None values gracefully
                "score": max(0, 100 - int((a.get("result_json") or {}).get("greenwashing_score", 0) or 0)),
                "status": "Flagged" if int((a.get("result_json") or {}).get("risk_score", 0) or 0) > 50 else "Clean",
                "company": (a.get("result_json") or {}).get("company_name") or a.get("filename", "ESG Report")
            }
            for a in analyses[:5]
        ],
    }
