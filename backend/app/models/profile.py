"""
Internal profile model representing a row in the public.profiles table.

This is NOT a Pydantic schema — it is a plain dataclass used for type-safe
internal data passing between repository, service, and dependency layers.
Pydantic schemas (in app/schemas/) handle serialization to/from the API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.core.enums import UserRole


@dataclass
class ProfileModel:
    """
    Mirrors the public.profiles table schema.
    All fields that can be NULL in the DB are typed as Optional here.
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

    @classmethod
    def from_dict(cls, data: dict) -> "ProfileModel":
        """
        Construct a ProfileModel from a raw Supabase row dict.
        Handles type coercion and optional-field defaults safely.
        """
        # Coerce role string to enum; fall back to EMPLOYEE for unknown values.
        raw_role = data.get("role", "EMPLOYEE")
        try:
            role = UserRole(raw_role)
        except ValueError:
            role = UserRole.EMPLOYEE

        # Parse timestamps — Supabase returns ISO strings.
        def _parse_dt(val: str | datetime | None) -> datetime:
            if val is None:
                return datetime.utcnow()
            if isinstance(val, datetime):
                return val
            return datetime.fromisoformat(val.replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            email=data["email"],
            full_name=data.get("full_name", ""),
            role=role,
            is_active=data.get("is_active", True),
            is_management_verified=data.get("is_management_verified", False),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
            employee_id=data.get("employee_id"),
            department=data.get("department"),
            job_title=data.get("job_title"),
            phone=data.get("phone"),
            location=data.get("location"),
            bio=data.get("bio"),
            avatar_url=data.get("avatar_url"),
        )

    @property
    def is_management(self) -> bool:
        return self.role in UserRole.management_roles()

    @property
    def is_employee(self) -> bool:
        return self.role in UserRole.employee_roles()
