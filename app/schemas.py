"""Pydantic data models for VoltKart SupportDesk AI."""

from typing import Literal
from pydantic import BaseModel, Field


class TicketIn(BaseModel):
    """Incoming support ticket received from a customer."""

    customer_email: str = Field(..., description="Email address of the customer")
    subject: str = Field(..., description="Subject line of the ticket")
    body: str = Field(..., description="Full text description of the customer request")


class TriageResult(BaseModel):
    """Structured output from the triage step."""

    category: Literal[
        "billing", "shipping", "returns", "technical", "account", "other"
    ] = Field(..., description="Topic category of the ticket")
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        ..., description="Urgency priority of the ticket"
    )
    sentiment: Literal["calm", "frustrated", "angry"] = Field(
        ..., description="Detected customer emotional state"
    )
    is_possible_injection: bool = Field(
        ..., description="Whether the text contains a prompt injection attempt"
    )
    summary: str = Field(..., description="Short summary of the ticket content")


class ResolverResult(BaseModel):
    """Structured output from the resolution step."""

    reply: str = Field(..., description="Draft response to the customer")
    citations: list[str] = Field(
        default_factory=list, description="List of knowledge base articles cited"
    )
    self_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    missing_info: list[str] = Field(
        default_factory=list, description="Missing details needed from the customer"
    )


class ApproveIn(BaseModel):
    """Optional human edited text for approving a draft reply."""

    edited_text: str | None = Field(
        default=None, description="Edited final text approved by a human agent"
    )


class TicketProcessResponse(BaseModel):
    """Response returned after creating and processing a ticket."""

    ticket_id: int
    status: str
    decision: str
    confidence: float
    reply: str
    citations: list[str] = Field(default_factory=list)

