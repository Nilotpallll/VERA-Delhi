"""Canonical Evidence Schema.

Architecture Rule 5: Evidence uses one canonical schema.
Architecture Rule 10: Persistent files must never depend on Render local filesystem.
"""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from .verification import VerificationResult


class EvidenceMediaType(StrEnum):
    TEXT = "TEXT"
    URL = "URL"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    APK = "APK"
    DOCUMENT = "DOCUMENT"


class StorageReference(BaseModel):
    bucket: str
    storage_path: str
    provider: str = "supabase_storage"
    mime_type: str
    size_bytes: int


class CanonicalEvidenceItem(BaseModel):
    id: str
    investigation_id: str
    media_type: EvidenceMediaType
    sha256: str = Field(..., description="Cryptographic SHA-256 digest of payload")
    title: str
    source_origin: str
    storage_ref: StorageReference | None = None
    content_payload: str | None = None
    extracted_entities: dict[str, list[str]] = Field(default_factory=dict)
    verification: VerificationResult
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: list[str] = Field(default_factory=list)
