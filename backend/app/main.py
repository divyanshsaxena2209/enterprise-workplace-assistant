"""
Enterprise Workplace Assistant — FastAPI Application Entry Point

Architecture:
  middleware → dependency → router → service → repository → Supabase
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.error_middleware import register_exception_handlers

# ---------------------------------------------------------------------------
# Configure logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.is_development else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ---------------------------------------------------------------------------
# FastAPI app instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Enterprise Workplace Assistant Team",
        "email": "support@enterprise-assistant.io",
    },
    license_info={"name": "Private — All Rights Reserved"},
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Signup, login, logout, and current-user endpoints.",
        },
        {
            "name": "Profile",
            "description": "Read and update the authenticated user's profile.",
        },
        {
            "name": "Jobs",
            "description": "Job listings management (ATS module — Phase 2).",
        },
        {
            "name": "Applications",
            "description": "Job applications management (ATS module — Phase 2).",
        },
        {
            "name": "Hiring",
            "description": "AI-powered resume screening (ATS module — Phase 2).",
        },
        {
            "name": "Knowledge",
            "description": "Company knowledge base RAG (Phase 3).",
        },
        {
            "name": "Onboarding",
            "description": "Employee onboarding workflows (Phase 4).",
        },
    ],
)

# ---------------------------------------------------------------------------
# Middleware (order matters — outermost registered last in Starlette)
# ---------------------------------------------------------------------------

# 1. CORS — must be outermost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Auth — populates request.state.user for all routes
app.add_middleware(AuthMiddleware)

# ---------------------------------------------------------------------------
# Exception handlers (centralized error formatting)
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Routers — Phase 1: Auth & Profiles
# ---------------------------------------------------------------------------
from app.routers import auth, profile  # noqa: E402

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Routers — Phase 2A: Resume Screening
# ---------------------------------------------------------------------------
from app.routers import resume, candidates  # noqa: E402

app.include_router(resume.router, prefix=settings.API_V1_STR)
app.include_router(candidates.router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Routers — Phase 2B: Job Management
# ---------------------------------------------------------------------------
from app.routers import jobs  # noqa: E402

app.include_router(jobs.router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Routers — Phase 2C: Applications
# ---------------------------------------------------------------------------
from app.routers import applications  # noqa: E402

app.include_router(applications.router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Routers — Phase 2D: AI Evaluations
# ---------------------------------------------------------------------------
from app.routers import evaluations  # noqa: E402

app.include_router(evaluations.router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Routers — Phase 2E: ATS Workflow Management
# ---------------------------------------------------------------------------
from app.routers import pipeline, recruiter_notes  # noqa: E402

app.include_router(pipeline.router, prefix=settings.API_V1_STR)
app.include_router(recruiter_notes.router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns server status. Used by load balancers and monitoring.",
    response_description="Server is healthy.",
)
def health_check() -> dict:
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
