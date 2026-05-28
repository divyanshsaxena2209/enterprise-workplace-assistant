from supabase import create_client, Client
from app.core.config import settings

# Initialize Supabase client using Service Role Key for backend administration
def get_supabase_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise Exception("Supabase credentials not configured")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

# Dependency to inject the client in routes
def get_db():
    return get_supabase_client()
