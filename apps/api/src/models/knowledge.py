"""SQLAlchemy models for SEBI Knowledge Base and pgvector store.

Architecture Rule 1: Schema-driven contracts.
Architecture Rule 13: Every investigation reproducible.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class KnowledgeDocumentModel(Base):
    """Authoritative regulatory or advisory document (SEBI, RBI, NSE, BSE, MCA)."""
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    publisher: Mapped[str] = mapped_column(String(128), nullable=False, index=True)  # SEBI | RBI | NSE | BSE | MCA
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)   # circular | regulation | investor_material | advisory
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    retrieval_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    document_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    license_info: Mapped[str] = mapped_column(String(255), default="Government of India Public Information / Open Data", nullable=False)
    document_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    chunks: Mapped[list["KnowledgeChunkModel"]] = relationship(
        "KnowledgeChunkModel", back_populates="document", cascade="all, delete-orphan", lazy="selectin"
    )


class KnowledgeChunkModel(Base):
    """Semantic chunk embedded for dense vector search (BGE-M3 1024-d)."""
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Embedding vector stored as JSON array of floats for portable pgvector/SQLite support
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(64), default="BAAI/bge-m3", nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    document: Mapped["KnowledgeDocumentModel"] = relationship(
        "KnowledgeDocumentModel", back_populates="chunks"
    )
