"""
Analysis Routes — ESG forensic audit, Scope 3 cross-doc reasoning, Carbon Gap.
T4 infrastructure (file upload, DB, audit) + T1 Gemini AI calls — INTEGRATED.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from middleware.auth import get_current_user, require_role
from utils.audit_logger import log_action
from utils.file_upload import save_upload, delete_upload
from utils.integration import extract_text, parse_manifest, process_scope3_data
from db import create_document, get_documents_by_field, update_document

# ── T1: Gemini AI ──
from ai.gemini_client import call_gemini_async
from prompts.esg_analysis_prompt import build_esg_analysis_prompt
from prompts.scope3_prompt import build_scope3_prompt
from prompts.carbon_gap_prompt import build_carbon_gap_prompt

router = APIRouter(prefix="/api/analysis", tags=["AI Analysis"])


# ════════════════════════════════════════════
# POST /api/analysis/esg — ESG Intelligence Engine
# ════════════════════════════════════════════
@router.post("/esg")
async def analyze_esg(
    file: UploadFile = File(...),
    user: dict = Depends(require_role("company")),
):
    """
    Upload ESG report PDF → extract text → run Gemini forensic analysis.
    """
    # ── T4: Handle file upload ──
    upload_info = await save_upload(file)

    try:
        # ── T2/T4: Extract text from PDF ──
        extracted_text = extract_text(upload_info["saved_path"])

        # ── Save the report to Firestore ──
        report_id = create_document("esg_reports", {
            "user_id": user["id"],
            "filename": upload_info["original_filename"],
            "extracted_text": extracted_text,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        })

        # ── T1: Gemini ESG Analysis ──
        try:
            prompt = build_esg_analysis_prompt(extracted_text)
            result = await call_gemini_async(prompt)
        except (ValueError, RuntimeError) as e:
            raise HTTPException(status_code=502, detail=f"Gemini AI error: {e}")

        # ── T4: Save analysis result ──
        result_id = create_document("analysis_results", {
            "user_id": user["id"],
            "esg_report_id": report_id,
            "analysis_type": "esg",
            "result_json": result,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        # ── T4: Update Company Profile with latest stats ──
        try:
            # Calculate a summary score (100 - greenwashing_score)
            esg_score = 100 - result.get("greenwashing_score", 0)
            
            profiles = get_documents_by_field("company_profiles", "user_id", user["id"], limit=1)
            profile_data = {
                "user_id": user["id"],
                "latest_esg_score": esg_score,
                "latest_report_id": report_id,
                "latest_analysis_id": result_id,
                "last_audit_date": datetime.now(timezone.utc).isoformat(),
                "reported_emissions": result.get("reported_emissions", {}),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            if profiles:
                update_document("company_profiles", profiles[0]["id"], profile_data)
            else:
                create_document("company_profiles", profile_data)
        except Exception as profile_err:
            # Don't fail the whole analysis if profile update fails
            print(f"Failed to update company profile: {profile_err}")

        # ── T4: Audit log ──
        log_action(
            user_id=user["id"],
            action="esg_analysis",
            entity_type="analysis_result",
            entity_id=result_id,
            details={"filename": upload_info["original_filename"], "report_id": report_id},
        )

        return {
            "id": result_id,
            "report_id": report_id,
            "analysis_type": "esg",
            "result": result,
        }

    finally:
        # Clean up uploaded file
        delete_upload(upload_info["saved_path"])


# ════════════════════════════════════════════
# POST /api/analysis/scope3 — Scope 3 Whistleblower
# ════════════════════════════════════════════
@router.post("/scope3")
async def analyze_scope3(
    esg_file: UploadFile = File(...),
    supplier_file: UploadFile = File(...),
    user: dict = Depends(require_role("company")),
):
    """
    Upload ESG report + supplier doc → cross-document Scope 3 analysis.
    """
    # ── T4: Handle file uploads ──
    esg_upload = await save_upload(esg_file)
    supplier_upload = await save_upload(supplier_file)

    try:
        # ── T2/T4: Extract text from ESG report ──
        esg_text = extract_text(esg_upload["saved_path"])
        
        # ── T2: Parse supplier manifest into structured data ──
        manifest_data = parse_manifest(supplier_upload["saved_path"])
        
        # ── T2: Build supplier network graph (nodes/edges) ──
        graph_data = process_scope3_data(esg_text, manifest_data)

        # ── Save documents to Firestore ──
        report_id = create_document("esg_reports", {
            "user_id": user["id"],
            "filename": esg_upload["original_filename"],
            "extracted_text": esg_text,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        })

        # ── T1: Gemini Scope 3 Analysis ──
        # Provide raw text for reasoning, but the graph_data summary helps too
        supplier_raw_text = extract_text(supplier_upload["saved_path"])
        try:
            prompt = build_scope3_prompt(esg_text, supplier_raw_text)
            ai_result = await call_gemini_async(prompt)
        except (ValueError, RuntimeError) as e:
            raise HTTPException(status_code=502, detail=f"Gemini AI error: {e}")

        # Combine AI reasoning with the calculated graph data
        result = {
            **ai_result,
            "calculated_graph": graph_data
        }

        # ── T4: Save analysis result ──
        result_id = create_document("analysis_results", {
            "user_id": user["id"],
            "esg_report_id": report_id,
            "analysis_type": "scope3",
            "result_json": result,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        # ── T4: Audit log ──
        log_action(
            user_id=user["id"],
            action="scope3_analysis",
            entity_type="analysis_result",
            entity_id=result_id,
            details={
                "esg_filename": esg_upload["original_filename"],
                "supplier_filename": supplier_upload["original_filename"],
            },
        )

        return {
            "id": result_id,
            "report_id": report_id,
            "scope3_doc_id": scope3_doc_id,
            "analysis_type": "scope3",
            "result": result,
        }

    finally:
        delete_upload(esg_upload["saved_path"])
        delete_upload(supplier_upload["saved_path"])


# ════════════════════════════════════════════
# POST /api/analysis/carbon-gap — Carbon Gap
# ════════════════════════════════════════════
@router.post("/carbon-gap")
async def analyze_carbon_gap(
    user: dict = Depends(require_role("company")),
):
    """
    Calculate carbon gap based on previous ESG analysis results.
    """
    # ── T4: Fetch latest analysis results for this company ──
    past_results = get_documents_by_field(
        "analysis_results", "user_id", user["id"],
        order_by="created_at", order_desc=True, limit=5
    )

    if not past_results:
        raise HTTPException(
            status_code=400,
            detail="No ESG analysis results found. Please run an ESG analysis first."
        )

    # Use the latest ESG analysis result for carbon gap
    latest_result = past_results[0].get("result_json", {})

    # ── T1: Gemini Carbon Gap Analysis ──
    try:
        prompt = build_carbon_gap_prompt(latest_result)
        result = await call_gemini_async(prompt)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=f"Gemini AI error: {e}")

    # ── T4: Save result ──
    result_id = create_document("analysis_results", {
        "user_id": user["id"],
        "analysis_type": "carbon_gap",
        "result_json": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # ── T4: Audit log ──
    log_action(
        user_id=user["id"],
        action="carbon_gap_analysis",
        entity_type="analysis_result",
        entity_id=result_id,
        details={"based_on_results": len(past_results)},
    )

    return {
        "id": result_id,
        "analysis_type": "carbon_gap",
        "result": result,
    }


# ════════════════════════════════════════════
# GET /api/analysis/history — Get analysis history
# ════════════════════════════════════════════
@router.get("/history")
async def get_analysis_history(
    analysis_type: str = None,
    user: dict = Depends(get_current_user),
):
    """Get past analysis results for the authenticated user."""
    results = get_documents_by_field(
        "analysis_results", "user_id", user["id"],
        order_by="created_at", order_desc=True, limit=50
    )
    if analysis_type:
        results = [r for r in results if r.get("analysis_type") == analysis_type]

    return {"results": results, "count": len(results)}
