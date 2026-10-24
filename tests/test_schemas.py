"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas import ResolverResult, TicketIn, TriageResult


def test_ticket_in_valid():
    """Verify that TicketIn accepts valid input data."""
    ticket = TicketIn(
        customer_email="rahul@example.com",
        subject="Order inquiry",
        body="When will my phone arrive?",
    )
    assert ticket.customer_email == "rahul@example.com"
    assert ticket.subject == "Order inquiry"
    assert ticket.body == "When will my phone arrive?"


def test_triage_result_valid():
    """Verify that TriageResult accepts valid categories and priorities."""
    triage = TriageResult(
        category="shipping",
        priority="high",
        sentiment="frustrated",
        is_possible_injection=False,
        summary="Customer asking about late delivery",
    )
    assert triage.category == "shipping"
    assert triage.priority == "high"
    assert triage.sentiment == "frustrated"
    assert triage.is_possible_injection is False


def test_triage_result_invalid_category():
    """Verify that TriageResult rejects an unknown category."""
    with pytest.raises(ValidationError):
        TriageResult(
            category="unknown_category",
            priority="medium",
            sentiment="calm",
            is_possible_injection=False,
            summary="Invalid category test",
        )


def test_resolver_result_defaults():
    """Verify that ResolverResult sets default empty lists for missing_info and citations."""
    res = ResolverResult(
        reply="Your delivery will arrive in 2-3 business days.",
        self_confidence=0.92,
    )
    assert res.citations == []
    assert res.missing_info == []
    assert res.self_confidence == 0.92


def test_resolver_result_confidence_range():
    """Verify that ResolverResult rejects self_confidence greater than 1.0."""
    with pytest.raises(ValidationError):
        ResolverResult(
            reply="Invalid confidence test",
            self_confidence=1.5,
        )
