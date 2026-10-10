"""State definition for VERA LangGraph Investigator.

Architecture Rule 5: Evidence uses one canonical schema.
Architecture Rule 6 & 7: Risk scoring is deterministic.
Architecture Rule 8: Tri-state verification.
Architecture Rule 9: Failsafe defaults.
"""

from typing import Any, TypedDict

from pydantic import BaseModel, Field


class InvestigationAction(BaseModel):
    """Action / tool invocation selected by the investigator."""
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    priority: int = 1


class ToolExecutionRecord(BaseModel):
    """Audit record for a single tool call."""
    tool_name: str
    arguments: dict[str, Any]
    status: str  # SUCCESS | FAILED | TIMED_OUT | SKIPPED
    duration_ms: float = 0.0
    evidence_count: int = 0
    error: str | None = None


class InvestigationState(TypedDict, total=False):
    """Complete LangGraph state payload passed between graph nodes."""
    investigation_id: str
    inputs: list[dict[str, Any]]

    # Understanding & extracted facts
    extracted_entities: list[dict[str, Any]]
    extracted_claims: list[dict[str, Any]]

    # Evidence & Verification (One canonical format)
    evidence_items: list[dict[str, Any]]
    verification_records: list[dict[str, Any]]

    # Actions & Execution Tracking
    pending_actions: list[dict[str, Any]]
    action_history: list[dict[str, Any]]
    executed_tool_signatures: list[str]
    iteration_count: int
    max_iterations: int
    max_tool_calls: int

    # Assessment & Loop termination
    is_sufficient: bool
    missing_evidence: list[str]
    scam_lifecycle_stage: str

    # Risk Dimensions (Strictly Kept Separate)
    risk_signals: list[dict[str, Any]]
    risk_score: float
    risk_level: str
    investigation_status: str
    model_confidence: float
    has_unavailable_analyzer: bool

    # Internal Reasoning & Failsafes
    reasoning_log: list[str]
    errors: list[str]

    # Final Output Report
    final_report: dict[str, Any]
