"""VERA canonical enumeration types.

All domain enums for Phase 2 investigation system.
Architecture Rule 5: Evidence uses one canonical schema.
Architecture Rule 8: Verification must distinguish tri-states.
"""

from enum import StrEnum


# ── Investigation Status ──────────────────────────────────────────────────────
# ── Investigation Status ──────────────────────────────────────────────────────
class InvestigationStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PARTIAL = "PARTIAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# ── Evidence source provenance ────────────────────────────────────────────────
class SourceType(StrEnum):
    """Distinguishes the origin provenance of every evidence object."""
    USER_INPUT = "user_input"
    LLM = "llm"
    ML_MODEL = "ml_model"
    OCR = "ocr"
    STT = "stt"
    DETERMINISTIC_ANALYZER = "deterministic_analyzer"
    OFFICIAL_SOURCE = "official_source"
    WEB_SOURCE = "web_source"
    DATABASE = "database"
    SYSTEM = "system"


# ── Evidence taxonomy ─────────────────────────────────────────────────────────
class EvidenceCategory(StrEnum):
    MEDIA = "MEDIA"
    IDENTITY = "IDENTITY"
    FINANCIAL = "FINANCIAL"
    COMMUNICATION = "COMMUNICATION"
    TECHNICAL = "TECHNICAL"
    REGULATORY = "REGULATORY"
    BEHAVIORAL = "BEHAVIORAL"
    CLAIM = "CLAIM"
    SYSTEM_EVENT = "SYSTEM_EVENT"


class EvidenceSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ── Entity types for graph ────────────────────────────────────────────────────
class EntityType(StrEnum):
    PERSON = "PERSON"
    COMPANY = "COMPANY"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    UPI = "UPI"
    DOMAIN = "DOMAIN"
    URL = "URL"
    PROFILE = "PROFILE"
    APK = "APK"
    MESSAGE = "MESSAGE"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


# ── Relationship types ────────────────────────────────────────────────────────
class RelationshipType(StrEnum):
    OWNS = "OWNS"
    CONTROLS = "CONTROLS"
    PROMOTES = "PROMOTES"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    IMPERSONATES = "IMPERSONATES"
    COMMUNICATES_WITH = "COMMUNICATES_WITH"
    HOSTS = "HOSTS"
    SENDS = "SENDS"
    MENTIONED_IN = "MENTIONED_IN"
    LINKED_TO = "LINKED_TO"


# ── Input types ───────────────────────────────────────────────────────────────
class InputType(StrEnum):
    TEXT = "TEXT"
    URL = "URL"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    APK = "APK"
    DOCUMENT = "DOCUMENT"
    PHONE_NUMBER = "PHONE_NUMBER"
    UPI_ID = "UPI_ID"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    TELEGRAM_CHANNEL = "TELEGRAM_CHANNEL"
    WHATSAPP_GROUP = "WHATSAPP_GROUP"
    SOCIAL_PROFILE = "SOCIAL_PROFILE"


# ── Report types ──────────────────────────────────────────────────────────────
class ReportStatus(StrEnum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"
    SUPERSEDED = "SUPERSEDED"


# ── Claim confidence levels ───────────────────────────────────────────────────
class ClaimStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"
