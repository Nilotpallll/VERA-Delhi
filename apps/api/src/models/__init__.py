"""SQLAlchemy declarative models for VERA — Phase 2.

Architecture Rule 1:  Frontend communicates only through API contracts.
Architecture Rule 5:  Evidence uses one canonical schema.
Architecture Rule 13: Every investigation must be reproducible from stored versions/configuration.
"""

from .base import Base
from .phase2 import (
    AuditLogModel,
    AnalyzerRunModel,
    ClaimModel,
    EntityModel,
    EvidenceModel,
    InputModel,
    InvestigationModel,
    ModelRunModel,
    RelationshipModel,
    ReportModel,
    RiskSignalModel,
    UserModel,
    VerificationResultModel,
)
from .knowledge import KnowledgeChunkModel, KnowledgeDocumentModel

__all__ = [
    "Base",
    "UserModel",
    "InvestigationModel",
    "InputModel",
    "EvidenceModel",
    "EntityModel",
    "RelationshipModel",
    "ClaimModel",
    "VerificationResultModel",
    "RiskSignalModel",
    "ModelRunModel",
    "AnalyzerRunModel",
    "ReportModel",
    "AuditLogModel",
    "KnowledgeDocumentModel",
    "KnowledgeChunkModel",
]
