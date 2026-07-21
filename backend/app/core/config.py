"""
Application configuration via pydantic-settings.

All settings are loaded from environment variables (or .env file).
Use the singleton `settings` object throughout the codebase.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    PROJECT_NAME: str = "Enterprise Workplace Assistant"
    PROJECT_DESCRIPTION: str = (
        "Production-grade backend for an Enterprise Workplace platform — "
        "powering authentication, hiring (ATS), knowledge RAG, meetings, and onboarding."
    )
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production

    # -------------------------------------------------------------------------
    # Supabase
    # -------------------------------------------------------------------------
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""

    # JWT Secret — from Supabase Dashboard → Settings → API → JWT Secret
    # Required for local token verification without calling Supabase on every request.
    SUPABASE_JWT_SECRET: str = ""

    # -------------------------------------------------------------------------
    # AI Services
    # -------------------------------------------------------------------------
    GEMINI_API_KEY: str = ""

    # -------------------------------------------------------------------------
    # ChromaDB
    # -------------------------------------------------------------------------
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # -------------------------------------------------------------------------
    # Auth
    # -------------------------------------------------------------------------
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
