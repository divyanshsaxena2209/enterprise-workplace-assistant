"""Safe, idempotent migration of referenced staging files from Supabase Storage to S3.

The operation deliberately retains all source objects in Supabase. Database references
are switched only after the destination object is uploaded and verified byte-for-byte.
"""
from __future__ import annotations

import hashlib
import mimetypes
import logging
from typing import Any

from app.core.config import settings
from app.db.supabase import get_supabase_client
from app.services import object_storage

logger = logging.getLogger(__name__)


def _validated_source_key(value: str | None, *, prefix: str) -> str | None:
    """Resolve only legacy Supabase references for the expected file family."""
    if not value:
        return None

    key: str | None = None
    if value.startswith("supabase://"):
        key = value[len("supabase://"):]
    elif value.startswith(("https://", "http://")):
        try:
            key = object_storage.extract_supabase_object_key_from_url(
                value, prefix=prefix
            )
        except ValueError:
            return None
    else:
        # knowledge_documents.file_key stores a bucket-relative key, not a URL.
        # The strict prefix/path validation below prevents arbitrary references.
        key = value

    expected = f"{prefix}_"
    if (
        not key
        or not key.startswith(expected)
        or "/" in key
        or "\\\\" in key
        or ".." in key
    ):
        return None
    return key


def _copy_and_verify(source_key: str, *, prefix: str, filename: str) -> str:
    """Copy one source object into its deterministic S3 key and verify bytes."""
    if prefix not in {"knowledge", "resumes"}:
        raise ValueError("Unsupported migration prefix.")
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError("S3 bucket is not configured.")
    if settings.STORAGE_PROVIDER.strip().lower() != "s3":
        raise RuntimeError("S3 storage provider is not enabled.")

    data = object_storage.download_supabase_object_bytes(
        source_key, prefix=prefix
    )
    if not data:
        raise ValueError("The source object is empty.")
    destination_key = f"{prefix}/{source_key}"

    import boto3

    content_type = mimetypes.guess_type(filename or source_key)[0]
    s3 = boto3.client("s3", region_name=settings.AWS_REGION)
    s3.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=destination_key,
        Body=data,
        ContentType=content_type or "application/octet-stream",
        ServerSideEncryption="AES256",
        Metadata={"migration-source": "supabase-staging"},
    )

    copied = object_storage.download_s3_object_bytes(
        destination_key, prefix=prefix
    )
    if hashlib.sha256(copied).digest() != hashlib.sha256(data).digest():
        raise RuntimeError("Destination checksum did not match source.")
    return destination_key


def migrate_supabase_objects_to_s3(*, dry_run: bool = True) -> dict[str, Any]:
    """Migrate referenced knowledge files and resumes, preserving source objects."""
    if settings.ENVIRONMENT.strip().lower() != "staging":
        raise RuntimeError("This migration is allowed only in staging.")
    if settings.STORAGE_PROVIDER.strip().lower() != "s3":
        raise RuntimeError("S3 must be enabled before migration.")
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError("S3 bucket is not configured.")

    client = get_supabase_client()
    result: dict[str, Any] = {
        "dry_run": dry_run,
        "source_objects_retained": True,
        "knowledge_documents": {
            "eligible": 0, "migrated": 0, "already_s3": 0,
            "skipped": 0, "failed": 0,
        },
        "resumes": {
            "eligible": 0, "migrated": 0, "already_s3": 0,
            "skipped": 0, "failed": 0,
        },
        "errors": [],
    }

    knowledge_response = (
        client.table("knowledge_documents")
        .select("id,filename,storage_provider,file_key,file_url")
        .order("created_at")
        .execute()
    )
    knowledge_rows = knowledge_response.data or []
    for row in knowledge_rows:
        counts = result["knowledge_documents"]
        provider = (row.get("storage_provider") or "supabase").strip().lower()
        if provider == "s3":
            counts["already_s3"] += 1
            continue
        if provider != "supabase":
            counts["skipped"] += 1
            continue

        source_key = _validated_source_key(row.get("file_key"), prefix="knowledge")
        if source_key is None:
            source_key = _validated_source_key(row.get("file_url"), prefix="knowledge")
        if source_key is None:
            counts["skipped"] += 1
            result["errors"].append({
                "entity": "knowledge_document",
                "id": str(row.get("id")),
                "reason": "unsupported_or_missing_supabase_reference",
            })
            continue

        counts["eligible"] += 1
        if dry_run:
            continue

        try:
            destination_key = _copy_and_verify(
                source_key,
                prefix="knowledge",
                filename=str(row.get("filename") or source_key),
            )
            update_query = (
                client.table("knowledge_documents")
                .update({
                    "storage_provider": "s3",
                    "file_key": destination_key,
                    "file_url": None,
                })
                .eq("id", str(row["id"]))
                .eq("storage_provider", "supabase")
            )
            # Avoid overwriting a reference that another request changed mid-copy.
            if row.get("file_key"):
                update_query = update_query.eq("file_key", row["file_key"])
            elif row.get("file_url"):
                update_query = update_query.eq("file_url", row["file_url"])
            update = update_query.select("id").execute()
            if not update.data:
                counts["failed"] += 1
                result["errors"].append({
                    "entity": "knowledge_document",
                    "id": str(row.get("id")),
                    "reason": "reference_changed_or_database_update_not_confirmed",
                })
                continue
            counts["migrated"] += 1
        except Exception as exc:
            counts["failed"] += 1
            logger.warning("Storage migration failed for knowledge document (exception_type=%s).", type(exc).__name__)
            result["errors"].append({
                "entity": "knowledge_document",
                "id": str(row.get("id")),
                "reason": type(exc).__name__,
            })

    resume_response = (
        client.table("resumes")
        .select("id,file_name,file_url")
        .order("uploaded_at")
        .execute()
    )
    resume_rows = resume_response.data or []
    for row in resume_rows:
        counts = result["resumes"]
        reference = str(row.get("file_url") or "")
        if reference.startswith("s3://resumes/"):
            counts["already_s3"] += 1
            continue

        source_key = _validated_source_key(reference, prefix="resumes")
        if source_key is None:
            counts["skipped"] += 1
            result["errors"].append({
                "entity": "resume",
                "id": str(row.get("id")),
                "reason": "unsupported_or_missing_supabase_reference",
            })
            continue

        counts["eligible"] += 1
        if dry_run:
            continue

        try:
            destination_key = _copy_and_verify(
                source_key,
                prefix="resumes",
                filename=str(row.get("file_name") or source_key),
            )
            new_reference = f"s3://{destination_key}"
            update = (
                client.table("resumes")
                .update({"file_url": new_reference})
                .eq("id", str(row["id"]))
                .eq("file_url", reference)
                .select("id")
                .execute()
            )
            if not update.data:
                counts["failed"] += 1
                result["errors"].append({
                    "entity": "resume",
                    "id": str(row.get("id")),
                    "reason": "reference_changed_or_database_update_not_confirmed",
                })
                continue
            counts["migrated"] += 1
        except Exception as exc:
            counts["failed"] += 1
            logger.warning("Storage migration failed for resume (exception_type=%s).", type(exc).__name__)
            result["errors"].append({
                "entity": "resume",
                "id": str(row.get("id")),
                "reason": type(exc).__name__,
            })

    result["success"] = (
        not result["errors"]
        and result["knowledge_documents"]["failed"] == 0
        and result["resumes"]["failed"] == 0
    )
    return result
