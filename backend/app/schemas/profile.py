"""
Profile request/response schemas.

Controls what profile data is exposed via the API and what can be updated.
"""

import re
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.core.enums import UserRole

_PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ProfileResponse(BaseModel):
    """
    Public-safe representation of a user profile.
    Returned on GET /profile, GET /auth/me, and embedded in TokenResponse.
    """

    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_management_verified: bool
    created_at: datetime
    updated_at: datetime

    # Optional fields
    employee_id: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, model: "ProfileModel") -> "ProfileResponse":  # noqa: F821
        """Build from an internal ProfileModel dataclass."""
        return cls(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            role=model.role,
            is_active=model.is_active,
            is_management_verified=model.is_management_verified,
            created_at=model.created_at,
            updated_at=model.updated_at,
            employee_id=model.employee_id,
            department=model.department,
            job_title=model.job_title,
            phone=model.phone,
            location=model.location,
            bio=model.bio,
            avatar_url=model.avatar_url,
        )


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ProfileUpdateRequest(BaseModel):
    """
    Payload for PATCH /profile.

    All fields are optional — only provided fields are updated.

    Example::

        {
          "full_name": "Jane A. Smith",
          "phone": "+14155559999",
          "department": "Platform Engineering",
          "job_title": "Staff Engineer",
          "location": "Austin, TX",
          "bio": "Building scalable distributed systems.",
          "avatar_url": "https://cdn.example.com/avatars/jane.jpg"
        }
    """

    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=128,
        examples=["Jane A. Smith"],
    )
    phone: Optional[str] = Field(
        default=None,
        description="Phone number in E.164 format.",
        examples=["+14155559999"],
    )
    department: Optional[str] = Field(
        default=None,
        max_length=100,
        examples=["Platform Engineering"],
    )
    job_title: Optional[str] = Field(
        default=None,
        max_length=100,
        examples=["Staff Engineer"],
    )
    location: Optional[str] = Field(
        default=None,
        max_length=128,
        examples=["Austin, TX"],
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Public URL of the user's avatar image.",
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Full name cannot be blank.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not _PHONE_RE.match(v):
            raise ValueError(
                "Phone must be a valid international number (e.g. +14155559999)."
            )
        return v

    def to_update_dict(self) -> dict:
        """Return only the fields that were explicitly set (exclude unset None)."""
        return self.model_dump(exclude_none=True, exclude_unset=True)
