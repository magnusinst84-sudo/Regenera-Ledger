"""
ESG Intelligence & Carbon Transparency Platform — Backend
FastAPI Application Entry Point
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# ── Initialize FastAPI ──
app = FastAPI(
    title="ESG Intelligence Platform API",
    description="AI-powered ESG forensic analysis, carbon gap calculation, and farmer matching",
    version="1.0.0",
)

# ── Error handling & request logging ──
from middleware.error_handler import setup_error_handlers
setup_error_handlers(app)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",       # React dev server
        "http://localhost:5173",       # Vite dev server
        os.getenv("FRONTEND_URL", ""),  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Import and mount routes ──
from routes.auth import router as auth_router
from routes.audit import router as audit_router
from routes.analysis import router as analysis_router
from routes.farmer import router as farmer_router
from routes.matching import router as matching_router
from routes.dashboard import router as dashboard_router

app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(analysis_router)
app.include_router(farmer_router)
app.include_router(matching_router)
app.include_router(dashboard_router)


# ── Health check ──
@app.get("/")
async def root():
    return {"status": "healthy", "service": "ESG Intelligence Platform API"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
