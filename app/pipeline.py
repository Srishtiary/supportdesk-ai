"""Pipeline orchestrator for VoltKart SupportDesk AI.

Coordinates triage -> retrieve -> resolve -> route, writes audit logs at each step,
and updates ticket status.
"""

from typing import Any
from sqlalchemy.orm import Session

from app.db import AuditLog, Reply, Ticket
from app.resolver import resolve_ticket
from app.router import compute_confidence, decide
from app.triage import triage_ticket

# Map router decisions to ticket status
STATUS_MAP: dict[str, str] = {
    "auto_send": "auto_sent",
    "draft": "pending_approval",
    "escalate": "escalated",
}


def log_step(db: Session, ticket_id: int, step: str, payload: dict[str, Any]) -> None:
    """Record a row in the audit_log table for tracking."""
    audit_entry = AuditLog(
        ticket_id=ticket_id,
        step=step,
        payload=payload,
    )
    db.add(audit_entry)
    db.commit()


def process_ticket(db: Session, ticket: Ticket) -> Ticket:
    """Execute the full support desk pipeline for an incoming ticket."""
    try:
        # Step 1: Triage the ticket
        triage_result = triage_ticket(ticket.subject, ticket.body)
        ticket.category = triage_result.category
        ticket.priority = triage_result.priority
        ticket.sentiment = triage_result.sentiment
        db.commit()

        log_step(db, ticket.id, "triage", triage_result.model_dump())

        # Step 2: Retrieve KB context & draft response
        resolver_result, top_score, chunks = resolve_ticket(ticket.subject, ticket.body)

        log_step(
            db,
            ticket.id,
            "retrieve",
            {
                "top_score": top_score,
                "chunk_count": len(chunks),
                "chunk_ids": [c.get("id", "") for c in chunks],
            },
        )
        log_step(db, ticket.id, "resolve", resolver_result.model_dump())

        # Step 3: Route decision
        confidence = compute_confidence(top_score, resolver_result.self_confidence)
        decision, reason = decide(
            confidence=confidence,
            sentiment=triage_result.sentiment,
            priority=triage_result.priority,
            is_injection=triage_result.is_possible_injection,
            missing_info=resolver_result.missing_info,
        )

        log_step(
            db,
            ticket.id,
            "route",
            {
                "confidence": confidence,
                "decision": decision,
                "reason": reason,
            },
        )

        # Step 4: Save reply and update ticket status
        ticket.status = STATUS_MAP.get(decision, "escalated")
        reply = Reply(
            ticket_id=ticket.id,
            draft_text=resolver_result.reply,
            final_text=resolver_result.reply if decision == "auto_send" else None,
            citations=resolver_result.citations,
            confidence=confidence,
            decision=decision,
        )
        db.add(reply)
        db.commit()
        db.refresh(ticket)
        return ticket

    except Exception as error:
        # If any step fails, escalate the ticket safely instead of crashing
        db.rollback()
        ticket.status = "escalated"
        db.add(ticket)
        db.commit()

        log_step(
            db,
            ticket.id,
            "error",
            {"error": str(error), "action": "escalated"},
        )

        fallback_reply = Reply(
            ticket_id=ticket.id,
            draft_text="Your ticket has been escalated to our human support team for manual assistance.",
            final_text=None,
            citations=[],
            confidence=0.0,
            decision="escalate",
        )
        db.add(fallback_reply)
        db.commit()
        db.refresh(ticket)
        return ticket
