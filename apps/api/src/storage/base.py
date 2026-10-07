"""Storage Provider abstraction.

Architecture Rule 10: Persistent files must never depend on Render local filesystem.
"""

from abc import ABC, abstractmethod

from ..contracts.evidence import StorageReference


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
