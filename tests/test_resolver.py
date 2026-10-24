"""Unit tests for the KB resolver module."""

from app.resolver import resolve_ticket
from app.schemas import ResolverResult


def test_resolve_clearly_answerable():
    """Verify high confidence and accurate citations for a clear KB question."""
    subject = "Return window inquiry"
    body = "How many days do I have to return an item on VoltKart, and does it need original packaging?"

    result, top_score, chunks = resolve_ticket(subject, body)

    assert isinstance(result, ResolverResult)
    assert isinstance(top_score, float)
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert top_score > 0.4
    assert result.self_confidence >= 0.85
    assert any("returns-and-replacements.md" in c for c in result.citations)
    assert "30" in result.reply


def test_resolve_partly_answerable():
    """Verify moderate confidence or missing info when customer details are incomplete."""
    subject = "Can I return my item"
    body = "I opened the box yesterday. Can I still return it and get a refund?"

    result, top_score, chunks = resolve_ticket(subject, body)

    assert isinstance(result, ResolverResult)
    assert isinstance(top_score, float)
    # Since product type is unspecified, confidence is moderate and/or missing_info is requested
    assert 0.4 <= result.self_confidence <= 0.85 or len(result.missing_info) > 0


def test_resolve_not_in_kb():
    """Verify low confidence for questions completely outside VoltKart's scope."""
    subject = "Flight ticket cancellation"
    body = "How do I cancel my airline flight from Delhi to London and claim a flight refund?"

    result, top_score, chunks = resolve_ticket(subject, body)

    assert isinstance(result, ResolverResult)
    assert isinstance(top_score, float)
    # The topic is not covered in our electronics KB
    assert result.self_confidence <= 0.4
