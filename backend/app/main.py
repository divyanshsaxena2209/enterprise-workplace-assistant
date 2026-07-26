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




logging.basicConfig(
    level=logging.DEBUG if settings.is_development else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)




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






app.add_middleware(AuthMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[url.strip() for url in settings.FRONTEND_URLS.split(",") if url.strip()] if settings.FRONTEND_URLS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




register_exception_handlers(app)




from app.routers import auth, profile  

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)




from app.routers import resume, candidates  

app.include_router(resume.router, prefix=settings.API_V1_STR)
app.include_router(candidates.router, prefix=settings.API_V1_STR)




from app.routers import jobs  

app.include_router(jobs.router, prefix=settings.API_V1_STR)




from app.routers import applications  

app.include_router(applications.router, prefix=settings.API_V1_STR)




from app.routers import evaluations  

app.include_router(evaluations.router, prefix=settings.API_V1_STR)




from app.routers import pipeline, recruiter_notes  

app.include_router(pipeline.router, prefix=settings.API_V1_STR)
app.include_router(recruiter_notes.router, prefix=settings.API_V1_STR)




from app.routers import knowledge  

app.include_router(knowledge.router, prefix=settings.API_V1_STR + "/knowledge", tags=["Knowledge"])






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


