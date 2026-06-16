"""
Authentication request/response schemas.

Strict Pydantic v2 validation for all auth-related API payloads.
"""

import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.enums import UserRole
from app.schemas.profile import ProfileResponse


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

_PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")
_EMP_ID_RE = re.compile(r"^[A-Za-z0-9\-_]{2,20}$")


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

    # Optional profile fields
    employee_id: Optional[str] = Field(
        default=None,
        description="Company-assigned employee identifier.",
        examples=["EMP-001"],
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

    @field_validator("employee_id")
    @classmethod
    def validate_employee_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not _EMP_ID_RE.match(v):
            raise ValueError(
                "Employee ID must be 2–20 alphanumeric characters, hyphens, or underscores."
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


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


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
