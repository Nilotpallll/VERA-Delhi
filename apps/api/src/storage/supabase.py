"""Supabase Storage Provider implementation.

Architecture Rule 10: Persistent files must never depend on Render local filesystem.
"""

from ..contracts.evidence import StorageReference
from ..core.config import settings
from .base import StorageProvider


class SupabaseStorageProvider(StorageProvider):
    def __init__(
        self,
        supabase_url: str | None = None,
        service_key: str | None = None,
        bucket: str | None = None,
    ):
        self._url = supabase_url or settings.SUPABASE_URL
        self._key = service_key or settings.SUPABASE_SERVICE_ROLE_KEY
        self._bucket = bucket or settings.SUPABASE_STORAGE_BUCKET

    @property
    def bucket_name(self) -> str:
        return self._bucket

    async def upload(
        self,
        key: str,
        content: bytes,
        mime_type: str,
    ) -> StorageReference:
        # In Phase 0 contracts scaffolding, returns the validated StorageReference
        clean_key = key.lstrip("/")
        return StorageReference(
            bucket=self._bucket,
            storage_path=clean_key,
            provider="supabase_storage",
            mime_type=mime_type,
            size_bytes=len(content),
        )

    async def get_download_url(self, storage_ref: StorageReference, expires_in_seconds: int = 3600) -> str:
        if self._url:
            return f"{self._url.rstrip('/')}/storage/v1/object/public/{storage_ref.bucket}/{storage_ref.storage_path}"
        return f"https://mock-supabase.local/storage/{storage_ref.bucket}/{storage_ref.storage_path}"
