"""Storage provider abstraction for knowledge documents.

When STORAGE_PROVIDER=s3, boto3 uses the Lambda execution role via the default
AWS credential chain; no long-lived AWS access keys belong in environment vars.
The bucket should remain private and Block Public Access should stay enabled.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from app.core.config import settings


def _safe_filename(filename: str) -> str:
    name = os.path.basename(filename or "document").replace(" ", "_")
    return name.replace("\\", "_").replace("/", "_") or "document"


def _s3_client() -> Any:
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError(
            "STORAGE_PROVIDER is set to 's3' but AWS_S3_BUCKET is not configured."
        )
    import boto3

    return boto3.client("s3", region_name=settings.AWS_REGION)


def upload_knowledge_document(
    filename: str,
    file_bytes: bytes,
    content_type: str,
    *,
    prefix: str = "knowledge",
) -> dict[str, str | None]:
    if prefix not in {"knowledge", "resumes"}:
        raise ValueError("Unsupported object prefix.")
    provider = settings.STORAGE_PROVIDER.strip().lower()
    safe_name = _safe_filename(filename)
    object_name = f"{prefix}_{uuid.uuid4()}_{safe_name}"

    if provider == "s3":
        bucket = settings.AWS_S3_BUCKET
        s3 = _s3_client()
        key = f"{prefix}/{object_name}"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=settings.S3_PRESIGNED_URL_TTL_SECONDS,
        )
        return {
            "storage_provider": "s3",
            "file_key": key,
            "file_url": url,
        }

    if provider == "supabase":
        from app.db.supabase import get_supabase_client

        client = get_supabase_client()
        client.storage.from_("resumes").upload(
            path=object_name,
            file=file_bytes,
            file_options={"content-type": content_type},
        )
        return {
            "storage_provider": "supabase",
            "file_key": object_name,
            "file_url": client.storage.from_("resumes").get_public_url(object_name),
        }

    raise RuntimeError(
        f"Unsupported STORAGE_PROVIDER {provider!r}; use 'supabase' or 's3'."
    )


def delete_knowledge_document_object(
    storage_provider: str | None,
    file_key: str | None,
    file_url: str | None,
) -> None:
    # Legacy localStorage records may not contain a provider. Treat those as
    # Supabase URLs so a future S3 cutover does not mis-handle old records.
    provider = (storage_provider or "supabase").strip().lower()

    if provider == "s3":
        if (
            not file_key
            or not file_key.startswith(("knowledge/", "resumes/"))
            or ".." in file_key
        ):
            raise ValueError("Invalid S3 document object key.")
        _s3_client().delete_object(Bucket=settings.AWS_S3_BUCKET, Key=file_key)
        return

    if provider == "supabase":
        from app.db.supabase import get_supabase_client

        key = file_key
        if not key and file_url:
            key = file_url.split("?", 1)[0].rstrip("/").split("/")[-1]
        if key:
            get_supabase_client().storage.from_("resumes").remove([key])
        return

    raise RuntimeError(
        f"Unsupported storage provider {provider!r}; use 'supabase' or 's3'."
    )


def _create_presigned_download_url(file_key: str, prefix: str) -> str:
    if not file_key.startswith(f"{prefix}/") or ".." in file_key:
        raise ValueError("Invalid S3 document object key.")
    s3 = _s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": file_key},
        ExpiresIn=settings.S3_PRESIGNED_URL_TTL_SECONDS,
    )


def create_knowledge_document_download_url(file_key: str) -> str:
    # Knowledge route is deliberately scoped to knowledge objects only.
    return _create_presigned_download_url(file_key, "knowledge")


def create_resume_download_url(file_key: str) -> str:
    # Resume URLs are generated only by authenticated candidate-detail routes.
    return _create_presigned_download_url(file_key, "resumes")
