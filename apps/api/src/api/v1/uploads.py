"""Upload endpoints with strict validation, MIME checks, size limits, and SHA256 calculation.

Architecture Rule 10: Persistent files must never depend on Render local filesystem.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ...contracts.evidence import StorageReference
from ...core.security import sanitize_storage_path, validate_file_bytes
from ...storage.supabase import SupabaseStorageProvider
from ..deps import rate_limit

router = APIRouter(prefix="/uploads", tags=["Uploads"])
storage_provider = SupabaseStorageProvider()


@router.post(
    "",
    response_model=StorageReference,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(requests_per_minute=30))],
)
async def upload_evidence_file(
    file: UploadFile = File(...),
) -> StorageReference:
    """Upload an evidence file with SHA-256 calculation and security validation."""
    content = await file.read()
    filename = file.filename or "unnamed_file"

    is_valid, mime_type, sha256_hash, error_msg = validate_file_bytes(content, filename)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {error_msg}",
        )

    storage_key = sanitize_storage_path(f"evidence/{sha256_hash}_{filename}")
    ref = await storage_provider.upload(
        key=storage_key,
        content=content,
        mime_type=mime_type,
    )
    return ref
