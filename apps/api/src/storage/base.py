"""Storage Provider abstraction and file metadata models.

Architecture Rule 10: Persistent files must never depend on Render local filesystem.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from ..contracts.evidence import StorageReference


class FileValidationResult(BaseModel):
    is_valid: bool
    mime_type: str
    sha256: str
    size_bytes: int
    filename: str
    error_message: str | None = None


class StorageProvider(ABC):
    """Abstract interface for persistent object storage."""

    @property
    @abstractmethod
    def bucket_name(self) -> str:
        pass

    @abstractmethod
    async def upload(
        self,
        key: str,
        content: bytes,
        mime_type: str,
    ) -> StorageReference:
        """Upload raw evidence bytes to cloud store and return canonical reference."""
        pass

    @abstractmethod
    async def get_download_url(self, storage_ref: StorageReference, expires_in_seconds: int = 3600) -> str:
        """Generate signed URL for authorized access."""
        pass

    @abstractmethod
    async def delete(self, storage_ref: StorageReference) -> bool:
        """Delete object from storage."""
        pass
