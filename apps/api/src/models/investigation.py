"""Investigation SQLAlchemy Model.

Stores investigations, metadata, manifest digests, risk assessment, and analyzer records.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .evidence import EvidenceModel


class InvestigationModel(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_entity_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    risk_assessment: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    analyzer_records: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel",
        back_populates="investigation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
