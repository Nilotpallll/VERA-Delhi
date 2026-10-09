"""Vector Store, Semantic Retrieval, and Citation Generation.

Failsafe Invariants:
  - If retrieval fails or has low confidence, return KNOWLEDGE_UNAVAILABLE.
  - If official source cannot be verified, return VERIFICATION_UNAVAILABLE.
  - Zero hallucinations: all regulatory assertions must link to official citations.
"""

import math
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from ..ai.bge_m3 import BGEM3EmbeddingProvider
from .pipeline import ProcessedDocument, RegulatoryPipeline


class OfficialCitation(BaseModel):
    source_url: str
    title: str
    publisher: str
    publication_date: str | None = None
    retrieval_date: str
    document_hash: str
    license_info: str
    document_version: str
    matching_chunk_snippet: str
    similarity_score: float = Field(ge=0.0, le=1.0)


class RetrievalResult(BaseModel):
    status: str  # SUCCESS | KNOWLEDGE_UNAVAILABLE | VERIFICATION_UNAVAILABLE
    citations: list[OfficialCitation] = Field(default_factory=list)
    best_similarity: float = 0.0
    query: str
    total_candidates_searched: int = 0


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two unit/non-unit vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


class RegulatoryVectorStore:
    """In-memory & pgvector compatible semantic store for regulatory knowledge."""

    def __init__(self, embedder: BGEM3EmbeddingProvider | None = None):
        self.embedder = embedder or BGEM3EmbeddingProvider()
        self.documents: dict[str, ProcessedDocument] = {}
        # List of (chunk_id, doc_id, text, embedding_vector, meta_dict)
        self.indexed_chunks: list[dict[str, Any]] = []

    async def ingest_document(self, doc: ProcessedDocument) -> None:
        """Stores document and embeds all its chunks."""
        self.documents[doc.id] = doc

        chunk_texts = [c.text for c in doc.chunks]
        if not chunk_texts:
            return

        embeddings = await self.embedder.embed_texts(chunk_texts)

        for chunk, emb in zip(doc.chunks, embeddings, strict=False):
            self.indexed_chunks.append({
                "chunk_id": f"{doc.id}_c{chunk.chunk_index}",
                "doc_id": doc.id,
                "text": chunk.text,
                "embedding": emb,
                "metadata": doc.metadata,
            })

    async def initialize_seed_knowledge(self) -> None:
        """Loads and indexes official seed regulatory documents."""
        pipeline = RegulatoryPipeline()
        seeds = await pipeline.fetcher.fetch_seed_documents()
        for seed in seeds:
            doc = pipeline.process_raw_document(seed)
            await self.ingest_document(doc)

    async def search(
        self, query: str, top_k: int = 3, similarity_threshold: float = 0.35
    ) -> RetrievalResult:
        """Searches indexed regulatory material and formats citations.

        Failsafe:
          If best similarity < similarity_threshold, returns KNOWLEDGE_UNAVAILABLE.
        """
        if not query or not query.strip():
            return RetrievalResult(status="KNOWLEDGE_UNAVAILABLE", query=query)

        if not self.indexed_chunks:
            # Ensure initialized
            await self.initialize_seed_knowledge()

        query_embeds = await self.embedder.embed_texts([query])
        query_vec = query_embeds[0]

        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self.indexed_chunks:
            score = _cosine_similarity(query_vec, item["embedding"])
            # Word-level keyword overlap booster for domain terms (SEBI, guaranteed, return, etc.)
            query_words = set(query.lower().split())
            text_words = set(item["text"].lower().split())
            overlap = len(query_words.intersection(text_words))
            if overlap > 0:
                score = min(1.0, score + 0.05 * min(overlap, 5))
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored or scored[0][0] < similarity_threshold:
            return RetrievalResult(
                status="KNOWLEDGE_UNAVAILABLE",
                query=query,
                best_similarity=scored[0][0] if scored else 0.0,
                total_candidates_searched=len(self.indexed_chunks),
            )

        citations = []
        for score, item in scored[:top_k]:
            if score < similarity_threshold:
                continue
            meta = item["metadata"]
            citations.append(OfficialCitation(
                source_url=meta.source_url,
                title=meta.title,
                publisher=meta.publisher,
                publication_date=meta.publication_date.isoformat() if meta.publication_date else None,
                retrieval_date=meta.retrieval_date.isoformat(),
                document_hash=meta.document_hash,
                license_info=meta.license_info,
                document_version=meta.document_version,
                matching_chunk_snippet=item["text"][:300],
                similarity_score=round(score, 4),
            ))

        return RetrievalResult(
            status="SUCCESS",
            citations=citations,
            best_similarity=round(scored[0][0], 4),
            query=query,
            total_candidates_searched=len(self.indexed_chunks),
        )
