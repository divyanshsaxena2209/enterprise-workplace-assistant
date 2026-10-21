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

    # Cognito remains disabled until identity-to-profile mapping and staging tests
    # are implemented. These public identifiers are not secrets.
    COGNITO_ENABLED: bool = False
    COGNITO_REGION: str = "ap-south-1"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""

    # Object storage provider. Keep "supabase" until the private S3 bucket and IAM
    # permissions have been created and the S3 upload flow has been verified.
    STORAGE_PROVIDER: str = "supabase"
    AWS_REGION: str = "ap-south-1"
    AWS_S3_BUCKET: str = ""
    S3_PRESIGNED_URL_TTL_SECONDS: int = 900

    
    
    
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
