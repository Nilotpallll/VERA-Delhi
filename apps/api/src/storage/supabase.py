"""Supabase Storage Provider implementation with validation and error handling.

Architecture Rule 10: Persistent files must never depend on Render local filesystem.
"""

import httpx

from ..contracts.evidence import StorageReference
from ..core.config import settings
from ..core.observability import logger
from ..core.security import sanitize_storage_path, validate_file_bytes
from .base import FileValidationResult, StorageProvider


class SupabaseStorageProvider(StorageProvider):
    def __init__(
        self,
        supabase_url: str | None = None,
        service_key: str | None = None,
        bucket: str | None = None,
    ):
        raw_url = supabase_url or settings.SUPABASE_URL or ""
        self._url = raw_url.rstrip("/") if raw_url else ""
        self._key = service_key or settings.SUPABASE_SERVICE_ROLE_KEY or ""
        self._bucket = bucket or settings.SUPABASE_STORAGE_BUCKET or "evidence"


    @property
    def bucket_name(self) -> str:
        return self._bucket

    def validate_content(self, content: bytes, original_filename: str) -> FileValidationResult:
        """Validate content size, MIME, and sha256."""
        is_valid, mime_type, sha256, err = validate_file_bytes(content, original_filename)
        return FileValidationResult(
            is_valid=is_valid,
            mime_type=mime_type,
            sha256=sha256,
            size_bytes=len(content),
            filename=original_filename,
            error_message=err,
        )

    async def upload(
        self,
        key: str,
        content: bytes,
        mime_type: str,
    ) -> StorageReference:
        clean_key = sanitize_storage_path(key)

        # In production with Supabase configured, execute REST call
        if self._url and self._key and not self._url.startswith("http://placeholder"):
            upload_url = f"{self._url}/storage/v1/object/{self._bucket}/{clean_key}"
            headers = {
                "Authorization": f"Bearer {self._key}",
                "apikey": self._key,
                "Content-Type": mime_type,
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(upload_url, content=content, headers=headers)
                if res.status_code not in (200, 201):
                    logger.warning("Supabase storage upload returned %d: %s", res.status_code, res.text)

        return StorageReference(
            bucket=self._bucket,
            storage_path=clean_key,
            provider="supabase_storage",
            mime_type=mime_type,
            size_bytes=len(content),
        )

    async def get_download_url(self, storage_ref: StorageReference, expires_in_seconds: int = 3600) -> str:
        if self._url and not self._url.startswith("http://placeholder"):
            return f"{self._url}/storage/v1/object/public/{storage_ref.bucket}/{storage_ref.storage_path}"
        return f"https://mock-supabase.local/storage/{storage_ref.bucket}/{storage_ref.storage_path}"

    async def delete(self, storage_ref: StorageReference) -> bool:
        if self._url and self._key and not self._url.startswith("http://placeholder"):
            delete_url = f"{self._url}/storage/v1/object/{storage_ref.bucket}/{storage_ref.storage_path}"
            headers = {
                "Authorization": f"Bearer {self._key}",
                "apikey": self._key,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.delete(delete_url, headers=headers)
                return res.status_code in (200, 204)
        return True
