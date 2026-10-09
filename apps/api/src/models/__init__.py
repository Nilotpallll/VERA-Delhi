"""SQLAlchemy declarative models for VERA.

Architecture Rule 1: Frontend communicates only through API contracts.
Architecture Rule 5: Evidence uses one canonical schema.
Architecture Rule 13: Every investigation must be reproducible from stored versions/configuration.
"""

from .base import Base
from .evidence import EvidenceModel
from .investigation import InvestigationModel

__all__ = ["Base", "InvestigationModel", "EvidenceModel"]
