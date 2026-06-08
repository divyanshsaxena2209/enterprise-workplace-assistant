import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from supabase import create_client, Client
from typing import Dict, Any

security_scheme = HTTPBearer()

# Initialize Supabase Admin Client
supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> Dict[str, Any]:
    """
    Decodes and verifies the Supabase JWT token.
    Returns the decoded token payload.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False} # Supabase aud can be 'authenticated' or 'anon'
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

def get_current_user(payload: Dict[str, Any] = Security(verify_token)) -> Dict[str, Any]:
    """
    Fetches the profile details of the current authenticated user from PostgreSQL.
    """
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user identifier"
        )
    
    # Query profiles table using Supabase Admin client
    try:
        response = supabase_admin.table("profiles").select("*").eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database lookup error: {str(e)}"
        )

def require_role(allowed_roles: list[str]):
    """
    Dependency factory that checks if the current user has one of the allowed roles.
    """
    def dependency(current_user: Dict[str, Any] = Security(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        
        # Support new string-based roles and legacy enums compatibly
        effective_roles = [user_role]
        if user_role == "Management":
            effective_roles.extend(["HR_ADMIN", "SUPER_ADMIN", "management", "admin"])
        elif user_role == "Employee":
            effective_roles.extend(["EMPLOYEE", "employee"])
        elif user_role in ["HR_ADMIN", "SUPER_ADMIN"]:
            effective_roles.extend(["Management", "management"])
            
        if not any(r in allowed_roles for r in effective_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not authorized for your user role"
            )
        return current_user
    return dependency
