"""
Authentication request/response schemas.

Strict Pydantic v2 validation for all auth-related API payloads.
"""

import re
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.enums import UserRole
from app.schemas.profile import ProfileResponse






_PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


class SignupRequest(BaseModel):
    """
    Payload for POST /auth/signup.

    Example::

        {
          "full_name": "Jane Smith",
          "email": "jane@acme.com",
          "password": "Str0ng!pass",
          "role": "EMPLOYEE",
          "employee_id": "EMP-001",
          "department": "Engineering",
          "job_title": "Software Engineer",
          "phone": "+14155552671",
          "location": "San Francisco, CA",
          "bio": "Passionate about distributed systems."
        }
    """

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=128,
        description="User's full legal name.",
        examples=["Jane Smith"],
    )
    email: EmailStr = Field(
        ...,
        description="Corporate email address.",
        examples=["jane@acme.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password — minimum 8 characters.",
    )
    role: UserRole = Field(
        default=UserRole.EMPLOYEE,
        description="User role. One of: MANAGEMENT, EMPLOYEE.",
        examples=["EMPLOYEE"],
    )

    
    department: Optional[str] = Field(
        default=None,
        max_length=100,
        examples=["Engineering"],
    )
    job_title: Optional[str] = Field(
        default=None,
        max_length=100,
        examples=["Software Engineer"],
    )
    phone: Optional[str] = Field(
        default=None,
        description="Phone number in E.164 format.",
        examples=["+14155552671"],
    )
    location: Optional[str] = Field(
        default=None,
        max_length=128,
        examples=["San Francisco, CA"],
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be blank.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not _PHONE_RE.match(v):
            raise ValueError(
                "Phone must be a valid international number (e.g. +14155552671)."
            )
        return v



class LoginRequest(BaseModel):
    """
    Payload for POST /auth/login.

    Example::

        {
          "email": "jane@acme.com",
          "password": "Str0ng!pass"
        }
    """

    email: EmailStr = Field(
        ...,
        description="Registered email address.",
        examples=["jane@acme.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Account password.",
    )







class TokenResponse(BaseModel):
    """
    Returned on successful login or signup.

    Example::

        {
          "access_token": "eyJ...",
          "refresh_token": "eyJ...",
          "token_type": "bearer",
          "expires_in": 3600,
          "user": { ... }
        }
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds.")
    user: ProfileResponse


class CognitoSignupProfile(BaseModel):
    """Non-authoritative profile fields plus an unprivileged access request."""
    model_config = {"extra": "forbid"}

    full_name: str = Field(..., min_length=2, max_length=128)
    department: str = Field(..., min_length=1, max_length=100)
    job_title: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    location: Optional[str] = Field(default=None, max_length=128)
    bio: Optional[str] = Field(default=None, max_length=500)
    avatar_url: Optional[str] = Field(default=None, max_length=1024)
    requested_access_level: Literal["EMPLOYEE", "MANAGEMENT"] = Field(
        default="EMPLOYEE",
        description="Requested application access. MANAGEMENT is only a request and never grants privileges by itself.",
    )

    @field_validator("full_name", "department", "job_title")
    @classmethod
    def trim_required_profile_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This profile field cannot be blank.")
        return value


class CognitoLinkRequest(BaseModel):
    """Verified Cognito ID token used to link or provision an existing application identity."""
    id_token: str = Field(
        ...,
        min_length=20,
        max_length=10000,
        description="Cognito ID token from the staging authorization-code flow. Never log this value.",
    )
    nonce: str = Field(
        ...,
        min_length=16,
        max_length=256,
        description="OAuth nonce kept in the server-side flow cookie; never log this value.",
    )
    profile: Optional[CognitoSignupProfile] = Field(
        default=None,
        description="Profile fields supplied during Cognito signup. Any role selection remains non-authoritative unless the staging-only demo switch is enabled.",
    )
    requested_access_level: Optional[Literal["EMPLOYEE", "MANAGEMENT"]] = Field(
        default=None,
        description="Requested application role for the staging demo selector; ignored for grants unless the staging-only server flag is enabled or trusted authorization applies.",
    )


