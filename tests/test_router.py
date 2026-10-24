"""Unit tests for the rule-based routing engine."""

from app.config import settings
from app.router import compute_confidence, decide


def test_compute_confidence():
    """Verify weighted confidence calculation (0.4 * retrieval + 0.6 * self_confidence)."""
    # 0.4 * 0.8 + 0.6 * 0.9 = 0.32 + 0.54 = 0.86
    assert compute_confidence(0.8, 0.9) == 0.86

    # 0.4 * 0.5 + 0.6 * 0.7 = 0.20 + 0.42 = 0.62
    assert compute_confidence(0.5, 0.7) == 0.62

    # 0.4 * 0.0 + 0.6 * 0.0 = 0.0
    assert compute_confidence(0.0, 0.0) == 0.0


def test_rule_injection_escalates():
    """Verify that any injection attempt is immediately escalated."""
    decision, reason = decide(
        confidence=0.99,
        sentiment="calm",
        priority="low",
        is_injection=True,
    )
    assert decision == "escalate"
    assert "injection" in reason.lower()


def test_rule_urgent_priority_escalates():
    """Verify that urgent priority tickets are immediately escalated."""
    decision, reason = decide(
        confidence=0.95,
        sentiment="calm",
        priority="urgent",
        is_injection=False,
    )
    assert decision == "escalate"
    assert "urgent" in reason.lower()


def test_rule_angry_sentiment_drafts():
    """Verify that angry sentiment routes to human review (draft)."""
    decision, reason = decide(
        confidence=0.95,
        sentiment="angry",
        priority="medium",
        is_injection=False,
    )
    assert decision == "draft"
    assert "angry" in reason.lower()


def test_rule_auto_send():
    """Verify that high confidence with complete information auto-sends."""
    decision, reason = decide(
        confidence=settings.auto_threshold,
        sentiment="calm",
        priority="medium",
        is_injection=False,
        missing_info=[],
    )
    assert decision == "auto_send"
    assert "high confidence" in reason.lower()


def test_rule_high_confidence_with_missing_info_drafts():
    """Verify that high confidence with missing info routes to draft instead of auto_send."""
    decision, reason = decide(
        confidence=0.95,
        sentiment="calm",
        priority="low",
        is_injection=False,
        missing_info=["order_id", "product_model"],
    )
    assert decision == "draft"
    assert "missing info" in reason.lower()


def test_rule_moderate_confidence_drafts():
    """Verify that moderate confidence routes to draft."""
    decision, reason = decide(
        confidence=settings.draft_threshold,
        sentiment="calm",
        priority="low",
        is_injection=False,
    )
    assert decision == "draft"
    assert "moderate confidence" in reason.lower()


def test_rule_low_confidence_escalates():
    """Verify that confidence below the draft threshold escalates."""
    decision, reason = decide(
        confidence=settings.draft_threshold - 0.05,
        sentiment="calm",
        priority="low",
        is_injection=False,
    )
    assert decision == "escalate"
    assert "below draft threshold" in reason.lower()
