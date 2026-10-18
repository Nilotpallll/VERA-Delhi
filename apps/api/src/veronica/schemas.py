"""Pydantic data schemas for Veronica Chatbot Service."""

from typing import Literal

from pydantic import BaseModel, Field


class VeronicaAction(BaseModel):
    """Interactive client action button attached to an assistant message."""
    type: Literal["navigate", "open_helpline", "run_sample", "external_link"] = Field(
        ..., description="Type of client action triggered on click"
    )
    label: str = Field(..., description="Human-readable button label")
    payload: str = Field(..., description="Target route, anchor, URL, or sample identifier")


class VeronicaMessage(BaseModel):
    """Individual turn in a Veronica conversation."""
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Sender role"
    )
    content: str = Field(
        ..., min_length=1, max_length=1000, description="Text body of the message"
    )
    timestamp: str | None = Field(default=None, description="ISO timestamp of message")


class VeronicaChatRequest(BaseModel):
    """Payload sent by web client to /api/veronica/chat."""
    messages: list[VeronicaMessage] = Field(
        ..., min_length=1, max_length=20, description="Conversation history with newest message at end"
    )
    language: Literal["en", "hi"] = Field(
        default="en", description="Active user language code"
    )
    session_id: str | None = Field(
        default=None, description="Client session identifier for per-session rate tracking"
    )


class VeronicaChatResponse(BaseModel):
    """Payload returned by /api/veronica/chat."""
    reply: str = Field(..., description="Assistant response text")
    language: Literal["en", "hi"] = Field(..., description="Language of generated response")
    source: Literal["canned", "cached", "gemini", "fallback", "guard"] = Field(
        ..., description="Origin of the response"
    )
    actions: list[VeronicaAction] = Field(
        default_factory=list, description="Optional interactive action chips"
    )
    suggested_chips: list[str] = Field(
        default_factory=list, description="Follow-up quick reply suggestions"
    )


class VeronicaHealthResponse(BaseModel):
    """Status probe for Veronica endpoint."""
    status: str = "operational"
    enabled: bool = True
    provider: str = "gemini-free-tier"
    budget_remaining: int = 10
    active_cache_size: int = 0
