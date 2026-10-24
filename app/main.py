"""FastAPI application for VoltKart SupportDesk AI."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import Ticket, get_db, init_db
from app.pipeline import log_step, process_ticket
from app.retriever import index_kb
from app.schemas import ApproveIn, TicketIn, TicketProcessResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run initialization tasks when the FastAPI server starts."""
    # 1. Initialize SQLite database tables
    init_db()
    # 2. Embed and index VoltKart knowledge base articles
    index_kb()
    yield


app = FastAPI(
    title="VoltKart SupportDesk AI",
    description="Automated support-ticket pipeline for VoltKart electronics store.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def root():
    """Redirect home page directly to the interactive documentation."""
    return RedirectResponse(url="/docs")



@app.post("/tickets", response_model=TicketProcessResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketIn,
    db: Session = Depends(get_db),
) -> TicketProcessResponse:
    """Intake a new support ticket, run the 4-step pipeline, and return the result."""
    # 1. Save initial ticket record
    ticket = Ticket(
        customer_email=ticket_in.customer_email,
        subject=ticket_in.subject,
        body=ticket_in.body,
        status="open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 2. Process ticket through triage -> retrieve -> resolve -> route
    processed = process_ticket(db, ticket)
    latest_reply = processed.replies[-1] if processed.replies else None

    return TicketProcessResponse(
        ticket_id=processed.id,
        status=processed.status,
        decision=latest_reply.decision if latest_reply else "escalate",
        confidence=latest_reply.confidence if latest_reply else 0.0,
        reply=latest_reply.draft_text if latest_reply else "",
        citations=latest_reply.citations or [] if latest_reply else [],
    )


@app.get("/tickets")
def list_tickets(
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List tickets with an optional status filter."""
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)

    tickets = query.order_by(Ticket.id.desc()).all()
    return [
        {
            "id": t.id,
            "customer_email": t.customer_email,
            "subject": t.subject,
            "category": t.category,
            "priority": t.priority,
            "sentiment": t.sentiment,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tickets
    ]


@app.get("/tickets/{ticket_id}")
def get_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve full ticket details including its replies and chronological audit log."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} not found",
        )

    return {
        "id": ticket.id,
        "customer_email": ticket.customer_email,
        "subject": ticket.subject,
        "body": ticket.body,
        "category": ticket.category,
        "priority": ticket.priority,
        "sentiment": ticket.sentiment,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "replies": [
            {
                "id": r.id,
                "draft_text": r.draft_text,
                "final_text": r.final_text,
                "citations": r.citations,
                "confidence": r.confidence,
                "decision": r.decision,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in ticket.replies
        ],
        "audit_logs": [
            {
                "id": a.id,
                "step": a.step,
                "payload": a.payload,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in ticket.audit_logs
        ],
    }


@app.post("/tickets/{ticket_id}/approve")
def approve_ticket(
    ticket_id: int,
    approve_in: ApproveIn = ApproveIn(),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Human agent approves a draft reply with optional edits, closing the ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} not found",
        )

    # 1. Update ticket status to closed
    ticket.status = "closed"

    # 2. Update final text on the latest reply
    if ticket.replies:
        latest_reply = ticket.replies[-1]
        if approve_in.edited_text is not None and approve_in.edited_text.strip():
            latest_reply.final_text = approve_in.edited_text.strip()
        else:
            latest_reply.final_text = latest_reply.draft_text

    # 3. Log human approval in audit_log
    log_step(
        db,
        ticket.id,
        "human_approve",
        {"edited": bool(approve_in.edited_text), "status": "closed"},
    )

    db.commit()
    db.refresh(ticket)

    return {
        "ticket_id": ticket.id,
        "status": ticket.status,
        "final_reply": ticket.replies[-1].final_text if ticket.replies else None,
        "message": "Ticket draft approved and status set to closed",
    }
