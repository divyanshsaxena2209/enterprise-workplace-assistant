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
    # Comma-separated, verified emails explicitly trusted for immediate Management access.
    COGNITO_MANAGEMENT_EMAIL_ALLOWLIST: str = ""
    # Demo-only role picker. Effective only when Cognito is enabled and ENVIRONMENT=staging.
    # Leave disabled in every production deployment.
    COGNITO_DEMO_ROLE_SELECTION_ENABLED: bool = False

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
    def cognito_management_email_allowlist(self) -> set[str]:
        """Normalized allowlist supplied only by trusted server-side configuration."""
        return {
            email.strip().lower()
            for email in self.COGNITO_MANAGEMENT_EMAIL_ALLOWLIST.split(",")
            if email.strip()
        }

    @property
    def cognito_demo_role_selection_enabled(self) -> bool:
        """Enable self-service role switching only for an explicitly configured Cognito staging demo."""
        return (
            self.COGNITO_DEMO_ROLE_SELECTION_ENABLED
            and self.COGNITO_ENABLED
            and self.ENVIRONMENT.strip().lower() == "staging"
        )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
