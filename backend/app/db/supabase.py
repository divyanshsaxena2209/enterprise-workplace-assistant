from supabase import create_client, Client, ClientOptions
from app.core.config import settings

_supabase_client: Client | None = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise Exception("Supabase credentials not configured")
        
    _supabase_client = create_client(
        settings.SUPABASE_URL, 
        settings.SUPABASE_SERVICE_ROLE_KEY,
        options=ClientOptions(postgrest_client_timeout=60, storage_client_timeout=60)
    )
    return _supabase_client


def get_db():
    return get_supabase_client()
