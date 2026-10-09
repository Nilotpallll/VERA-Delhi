"""Contracts module — all schema exports, Phase 1 + Phase 2.

Architecture Rule 1: Frontend communicates only through API contracts.
Architecture Rule 2: API contracts are versioned.
"""

# Phase 1 contracts
from .analyzers import AnalyzerExecutionRecord, AnalyzerMetadata
from .evidence import CanonicalEvidenceItem, EvidenceMediaType, StorageReference
from .investigation import (
    HealthCheckResponse,
    InvestigationCreateRequest,
    InvestigationManifest,
    InvestigationResponse,
)
from .scoring import DeterministicRiskAssessment, RiskSeverityTier, ScoreFactorContribution
from .verification import AnalyzerExecutionStatus, VerificationResult, VerificationState

# Phase 2 enums
from .enums import (
    ClaimStatus,
    EntityType,
    EvidenceCategory,
    EvidenceSeverity,
    InputType,
    InvestigationStatus,
    RelationshipType,
    ReportStatus,
    SourceType,
)

# Phase 2 schemas
from .phase2 import (
    AddInputRequest,
    AnalyzeRequest,
    AnalyzerRun,
    AuditLog,
    Claim,
    Entity,
    EntityRelationship,
    EvidenceItem,
    EvidenceListResponse,
    InvestigationDetailResponse,
    InvestigationInput,
    InvestigationInputCreate,
    InvestigationReport,
    ModelRun,
    RiskSignal,
    UserRecord,
    VerificationResultRecord,
)

__all__ = [
    # Phase 1
    "VerificationState",
    "AnalyzerExecutionStatus",
    "VerificationResult",
    "AnalyzerMetadata",
    "AnalyzerExecutionRecord",
    "EvidenceMediaType",
    "StorageReference",
    "CanonicalEvidenceItem",
    "RiskSeverityTier",
    "ScoreFactorContribution",
    "DeterministicRiskAssessment",
    "InvestigationStatus",
    "InvestigationCreateRequest",
    "InvestigationManifest",
    "InvestigationResponse",
    "HealthCheckResponse",
    # Phase 2 enums
    "InvestigationStatus",
    "SourceType",
    "EvidenceCategory",
    "EvidenceSeverity",
    "EntityType",
    "RelationshipType",
    "InputType",
    "ReportStatus",
    "ClaimStatus",
    # Phase 2 schemas
    "UserRecord",
    "InvestigationInputCreate",
    "InvestigationInput",
    "EvidenceItem",
    "Entity",
    "EntityRelationship",
    "Claim",
    "VerificationResultRecord",
    "RiskSignal",
    "ModelRun",
    "AnalyzerRun",
    "AuditLog",
    "InvestigationReport",
    "AddInputRequest",
    "AnalyzeRequest",
    "EvidenceListResponse",
    "InvestigationDetailResponse",
]
