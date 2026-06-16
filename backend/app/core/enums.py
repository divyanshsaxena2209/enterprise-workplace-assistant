"""
Centralized enumerations for the Enterprise Workplace Assistant backend.

All role checks, comparisons, and database writes MUST use these enums.
Never hard-code role strings elsewhere in the codebase.
"""

from enum import Enum


class UserRole(str, Enum):
    """Supported user roles across the platform."""

    MANAGEMENT = "MANAGEMENT"
    EMPLOYEE = "EMPLOYEE"

    @classmethod
    def values(cls) -> list[str]:
        """Return all valid role value strings."""
        return [role.value for role in cls]

    @classmethod
    def management_roles(cls) -> list["UserRole"]:
        """Roles that carry management-level privileges."""
        return [cls.MANAGEMENT]

    @classmethod
    def employee_roles(cls) -> list["UserRole"]:
        """Roles that carry standard employee privileges."""
        return [cls.EMPLOYEE]


class JobStatus(str, Enum):
    """Supported statuses for job listings."""

    DRAFT = "Draft"
    PUBLISHED = "Published"
    CLOSED = "Closed"
    ARCHIVED = "Archived"

    @classmethod
    def values(cls) -> list[str]:
        """Return all valid job status strings."""
        return [status.value for status in cls]
