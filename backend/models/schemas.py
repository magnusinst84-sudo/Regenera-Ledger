"""
Pydantic request/response schemas for all API routes.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    role: str = Field(..., pattern="^(company|farmer)$")
    company_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


# ── ESG Analysis ──────────────────────────────────────────────────────────────

class ESGAnalysisRequest(BaseModel):
    extracted_text: str = Field(..., min_length=50, description="Parsed ESG report text")
    report_id: Optional[int] = None
    filename: Optional[str] = None


class ESGAnalysisResponse(BaseModel):
    reported_emissions: dict
    greenwashing_score: int
    risk_score: int
    explanation: str
    extracted_entities: dict
    analysis_id: Optional[int] = None


# ── Scope 3 ───────────────────────────────────────────────────────────────────

class Scope3Request(BaseModel):
    esg_text: str = Field(..., min_length=50, description="Primary ESG report text")
    supplier_data: str = Field(..., min_length=10, description="Shipping manifest / supplier data text")
    esg_report_id: Optional[int] = None


class Scope3Response(BaseModel):
    hidden_suppliers: List[dict]
    emission_discrepancy: dict
    network_graph: dict
    forensic_explanation: str
    analysis_id: Optional[int] = None


# ── Carbon Gap ────────────────────────────────────────────────────────────────

class CarbonGapRequest(BaseModel):
    analysis_result: dict = Field(..., description="Output from ESG analysis route")


class CarbonGapResponse(BaseModel):
    emission_gap: dict
    offset_required: dict
    financial_risk_exposure: dict
    explanation: str
    analysis_id: Optional[int] = None


# ── Farmer Estimation ─────────────────────────────────────────────────────────

class FarmerLocation(BaseModel):
    lat: float
    lng: float


class FarmerEstimationRequest(BaseModel):
    land_size_hectares: float
    crop_type: str
    soil_type: Optional[str] = None
    irrigation_method: Optional[str] = None
    farming_practices: Optional[List[str]] = []
    location: Optional[FarmerLocation] = None
    years_farming: Optional[int] = None
    certifications: Optional[List[str]] = []


class FarmerEstimationResponse(BaseModel):
    sequestration_capacity_tons: float
    credibility_score: int
    yearly_credit_potential: dict
    improvement_recommendations: List[str]
    eligible_standards: List[str]
    explanation: str
    estimation_id: Optional[int] = None


# ── Matching ──────────────────────────────────────────────────────────────────

class CompanyGapInput(BaseModel):
    credits_needed_tco2e: float
    company_location: Optional[str] = None
    urgency: Optional[str] = "within_1_year"
    budget_usd: Optional[str] = None
    preferred_crop_types: Optional[List[str]] = []


class MatchingRequest(BaseModel):
    company_gap: CompanyGapInput
    farmer_ids: Optional[List[int]] = None  # If None, fetch all from DB


class MatchingResponse(BaseModel):
    ranked_matches: List[dict]
    matching_summary: dict
    matching_id: Optional[int] = None


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    details: Optional[Any]
    timestamp: str


class AuditResponse(BaseModel):
    logs: List[AuditLogEntry]
    total: int
