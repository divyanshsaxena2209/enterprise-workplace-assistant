"""
Application configuration via pydantic-settings.

All settings are loaded from environment variables (or .env file).
Use the singleton `settings` object throughout the codebase.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    
    
    
    PROJECT_NAME: str = "Enterprise Workplace Assistant"
    PROJECT_DESCRIPTION: str = (
        "Production-grade backend for an Enterprise Workplace platform — "
        "powering authentication, hiring (ATS), knowledge RAG, meetings, and onboarding."
    )
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  

    
    
    
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""

    
    
    SUPABASE_JWT_SECRET: str = ""

    
    
    
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    
    
    
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8080

    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""

    
    
    
    PORT: int = 8000
    FRONTEND_URLS: str = "http://localhost:3000,http://localhost:3001"

    
    
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  

    
    
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
