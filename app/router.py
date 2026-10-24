"""Rule-based routing engine for VoltKart SupportDesk AI (pure Python, no LLM)."""

from typing import Optional

from app.config import settings


def compute_confidence(retrieval_score: float, self_confidence: float) -> float:
    """Calculate weighted confidence from retrieval quality and LLM self-confidence."""
    combined = (0.4 * retrieval_score) + (0.6 * self_confidence)
    return round(combined, 3)


def decide(
    confidence: float,
    sentiment: str,
    priority: str,
    is_injection: bool,
    missing_info: Optional[list[str]] = None,
) -> tuple[str, str]:
    """Determine the final routing decision and explanation for a ticket.

    Returns:
        (decision, reason) where decision is one of:
        - "escalate": send directly to human support
        - "draft": save draft for human agent approval
        - "auto_send": reply sent directly to the customer
    """
    missing = missing_info or []

    # 1. Prompt injection -> escalate
    if is_injection:
        return ("escalate", "Possible prompt injection detected")

    # 2. Urgent priority -> escalate
    if priority == "urgent":
        return ("escalate", "Urgent priority requires human agent handling")

    # 3. Angry sentiment -> draft (human review)
    if sentiment == "angry":
        return ("draft", "Customer is angry; response requires human review")

    # 4. High confidence and no missing info -> auto_send
    if confidence >= settings.auto_threshold and not missing:
        return (
            "auto_send",
            f"High confidence ({confidence:.3f}) with complete info",
        )

    # 5. Moderate confidence or missing info -> draft
    if confidence >= settings.draft_threshold:
        reason = (
            f"Missing info ({missing})"
            if missing and confidence >= settings.auto_threshold
            else f"Moderate confidence ({confidence:.3f})"
        )
        return ("draft", f"{reason}; response requires human review")

    # 6. Otherwise -> escalate
    return (
        "escalate",
        f"Low confidence ({confidence:.3f}) below draft threshold ({settings.draft_threshold})",
    )
