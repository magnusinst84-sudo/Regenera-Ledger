"""
Farmer Routes
Profile CRUD (T4 — complete) + Carbon estimation with Gemini AI (T1 — integrated).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from middleware.auth import get_current_user, require_role
from db import create_document, get_document, get_documents_by_field, update_document, get_all_documents
from utils.audit_logger import log_action
from utils.integration import get_farmer_candidates

# ── T1: Gemini AI ──
from ai.gemini_client import call_gemini_async
from prompts.farmer_estimation_prompt import build_farmer_estimation_prompt

router = APIRouter(prefix="/api/farmer", tags=["Farmer"])


# ── Request Models ──

class FarmerProfileRequest(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    state: str = ""
    district: str = ""
    village: str = ""
    land_size: str | float | int = 0.0
    crops: str = ""
    practices: str = ""
    # Fields for estimation compatibility
    soil_practices: str = "Standard"
    irrigation_type: str = "Standard"
    location_lat: str | float | int = 0.0
    location_lng: str | float | int = 0.0
    documents: list = []

@router.post("/profile")
@router.put("/profile")
async def create_or_update_profile(
    req: FarmerProfileRequest,
    user: dict = Depends(require_role("farmer")),
):
    """Create or update farmer profile. Only farmers can access."""

    existing = get_documents_by_field("farmer_profiles", "user_id", user["id"], limit=1)

    # Safe type conversion for numeric fields
    try:
        land_size_val = float(req.land_size) if req.land_size not in [None, ""] else 0.0
        lat_val = float(req.location_lat) if req.location_lat not in [None, ""] else 0.0
        lng_val = float(req.location_lng) if req.location_lng not in [None, ""] else 0.0
    except (ValueError, TypeError):
        land_size_val = 0.0
        lat_val = 0.0
        lng_val = 0.0

    profile_data = {
        "user_id": user["id"],
        "name": req.name,
        "email": req.email,
        "phone": req.phone,
        "state": req.state,
        "district": req.district,
        "village": req.village,
        "land_size_hectares": land_size_val * 0.4047,  # Convert acres to hectares
        "land_size_acres": land_size_val,
        "crops": req.crops,
        "practices": req.practices,
        "crop_type": req.crops,
        "regenerative_practices": req.practices,
        "documents": req.documents,
        "soil_practices": req.soil_practices,
        "irrigation_type": req.irrigation_type,
        "location": {
            "lat": lat_val,
            "lng": lng_val,
            "state": req.state,
            "district": req.district,
            "village": req.village,
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if existing:
        profile_id = existing[0]["id"]
        update_document("farmer_profiles", profile_id, profile_data)
        action = "profile_updated"
    else:
        profile_data["created_at"] = datetime.now(timezone.utc).isoformat()
        profile_id = create_document("farmer_profiles", profile_data)
        action = "profile_created"

    log_action(
        user_id=user["id"],
        action=action,
        entity_type="farmer_profile",
        entity_id=profile_id,
        details={"crops": req.crops, "land_size": req.land_size},
    )

    profile_data["id"] = profile_id
    
    # ── T1: Smart Auto-Estimate (NEW) ──
    # Only trigger if this is a NEW profile or if core data changed
    trigger_estimation = False
    
    if action == "profile_created":
        trigger_estimation = True
    elif existing:
        # Detect if any AI-relevant field changed
        old = existing[0]
        changed_fields = []
        for field in ["crops", "land_size", "practices", "soil_practices", "irrigation_type"]:
            if str(getattr(req, field, "")) != str(old.get(field, "")):
                changed_fields.append(field)
        
        if changed_fields:
            print(f"Detected changes in {changed_fields}. Triggering re-estimation.")
            trigger_estimation = True
        else:
            print("No core data changes. Skipping auto-estimation.")

    if trigger_estimation:
        try:
            # Run estimation logic so dashboard is ready immediately
            await run_estimation_logic(user)
        except Exception as e:
            # We don't want to crash the profile save if estimation fails
            print(f"Auto-estimation background failure: {e}")

    return profile_data


# ════════════════════════════════════════════
# GET /api/farmer/profile — Get farmer profile
# ════════════════════════════════════════════
@router.get("/profile")
async def get_profile(user: dict = Depends(require_role("farmer"))):
    """Get the authenticated farmer's profile."""
    profiles = get_documents_by_field("farmer_profiles", "user_id", user["id"], limit=1)
    if not profiles:
        raise HTTPException(status_code=404, detail="Farmer profile not found. Please create one first.")
    return profiles[0]


# ════════════════════════════════════════════
# GET /api/farmer/all — Get all farmer profiles (for company matching)
# ════════════════════════════════════════════
@router.get("/all")
async def get_all_farmers(user: dict = Depends(require_role("company"))):
    """Get all farmer profiles with latest estimations. Only companies can access."""
    farmers = get_farmer_candidates()
    return {"farmers": farmers, "count": len(farmers)}


# ════════════════════════════════════════════
# GET /api/farmer/dashboard — Farmer dashboard stats
# ════════════════════════════════════════════
@router.get("/dashboard")
async def get_farmer_dashboard(user: dict = Depends(require_role("farmer"))):
    """Get farmer dashboard stats: credits, earnings, active matches."""
    profiles = get_documents_by_field("farmer_profiles", "user_id", user["id"], limit=1)
    if not profiles:
        return {
            "credits_earned": 0, "earnings": 0, "active_matches": 0,
            "acres": 0, "credibility": 0, "credit_history": [],
        }

    profile = profiles[0]

    # Get latest estimations (Remove order_by to avoid index requirement)
    try:
        estimations = get_documents_by_field(
            "carbon_estimations", "farmer_id", profile["id"],
            limit=100
        )
        # Sort in-memory instead of delegating to Firestore index
        estimations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception as e:
        print(f"Error fetching estimations: {e}")
        estimations = []

    latest = estimations[0].get("result_json", {}) if estimations else {}

    # Calculate acres from hectares or fallback to original acres field
    hectares = profile.get("land_size_hectares", 0)
    acres = hectares * 2.471 if hectares else float(profile.get("land_size_acres", 0) or 0)

    return {
        "id": profile["id"],
        "name": profile.get("name", ""),
        "credits_earned": latest.get("sequestration_capacity_tons", 0),
        "earnings": latest.get("yearly_credit_potential", {}).get("estimated_revenue_usd_low", 0),
        "active_matches": 0,
        "acres": round(acres, 2),
        "credibility": latest.get("credibility_score", 0),
        "credit_history": [
            {
                "id": e["id"],
                "credits": e.get("sequestration_capacity_tons", 0),
                "date": e.get("created_at", ""),
            }
            for e in estimations[:5]
        ],
    }


# ════════════════════════════════════════════
# POST /api/farmer/estimate — Carbon Estimation (T1 Gemini AI)
# ════════════════════════════════════════════
async def run_estimation_logic(user: dict, req: FarmerProfileRequest = None):
    """Helper to run Gemini estimation logic."""
    profiles = get_documents_by_field("farmer_profiles", "user_id", user["id"], limit=1)
    if not profiles and not req:
        return None

    profile = profiles[0] if profiles else {}
    
    # Use request data or fallback to profile
    def get_val(key, default):
        if req and hasattr(req, key):
            val = getattr(req, key)
            if val not in [None, "", 0, 0.0]: return val
        return profile.get(key, default)

    # Specific land size logic
    land_size = 0
    if req and req.land_size:
        try: land_size = float(req.land_size)
        except: pass
    
    if not land_size:
        land_size = float(profile.get("land_size_acres", 0) or 0)

    farmer_data = {
        "land_size_hectares": land_size * 0.4047,
        "crop_type": get_val("crops", profile.get("crops", "Standard")),
        "soil_type": get_val("soil_practices", "Alluvial"),
        "irrigation_method": get_val("irrigation_type", "Drip"),
        "farming_practices": [get_val("practices", profile.get("practices", "No-till"))],
        "location": profile.get("location", {}),
    }

    # If no data at all, fail
    if not profiles and not land_size:
        return None

    # ── T1: Gemini Farmer Estimation ──
    from ai.gemini_client import call_gemini_async
    from prompts.farmer_estimation_prompt import build_farmer_estimation_prompt
    
    try:
        prompt = build_farmer_estimation_prompt(farmer_data)
        result = await call_gemini_async(prompt)
    except Exception as e:
        err_msg = str(e)
        print(f"Gemini estimation failed: {err_msg}")
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            raise HTTPException(status_code=429, detail="Gemini AI is currently busy. Please try again in 60 seconds.")
        # If it's a real failure, don't return None (which masks it), raise the error
        raise HTTPException(status_code=500, detail=f"Gemini AI failed: {err_msg}")

    # ── T4: Save estimation result ──
    est_id = create_document("carbon_estimations", {
        "farmer_id": profile.get("id", "temp_profile_id"),
        "user_id": user["id"],
        "farmer_data": farmer_data,
        "result_json": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    
    return {"id": est_id, "result": result}


@router.post("/estimate")
async def estimate_carbon(
    req: FarmerProfileRequest = None,
    user: dict = Depends(require_role("farmer")),
):
    """
    Estimate carbon sequestration potential for a farmer using Gemini AI.
    If req is provided, use its values for estimation (simulation mode).
    Otherwise, fetch the saved profile.
    """
    res = await run_estimation_logic(user, req)
    if not res:
        raise HTTPException(status_code=400, detail="Create a profile or provide land details first.")
    return res


# ════════════════════════════════════════════
# GET /api/farmer/estimations — Get estimation history
# ════════════════════════════════════════════
@router.get("/estimations")
async def get_estimations(user: dict = Depends(require_role("farmer"))):
    """Get carbon estimation history for the authenticated farmer."""
    profiles = get_documents_by_field("farmer_profiles", "user_id", user["id"], limit=1)
    if not profiles:
        return {"estimations": [], "count": 0}

    try:
        estimations = get_documents_by_field(
            "carbon_estimations", "farmer_id", profiles[0]["id"],
            limit=100
        )
        # In-memory sort to avoid index errors
        estimations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception as e:
        print(f"Error fetching estimations list: {e}")
        estimations = []
        
    return {"estimations": estimations[:20], "count": len(estimations)}
