"""Evidence SQLAlchemy Model.

Stores canonical evidence items, cryptographic SHA256 hashes, storage references, and verification.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .investigation import InvestigationModel


class EvidenceModel(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    media_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_origin: Mapped[str] = mapped_column(String(255), nullable=False)

    storage_ref: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    content_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_entities: Mapped[dict[str, list[str]]] = mapped_column(JSON, default=dict, nullable=False)
    verification: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel",
        back_populates="evidence",
    )
