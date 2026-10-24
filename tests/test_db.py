"""Unit tests for the database models and session management."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import AuditLog, Base, Reply, Ticket


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_create_ticket(db_session):
    """Test saving and retrieving a Ticket."""
    ticket = Ticket(
        customer_email="customer@example.com",
        subject="Shipping delay",
        body="Where is my order?",
        category="shipping",
        priority="high",
        sentiment="negative",
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)

    assert ticket.id is not None
    assert ticket.customer_email == "customer@example.com"
    assert ticket.status == "open"


def test_ticket_relationships(db_session):
    """Test Reply and AuditLog relationships with a Ticket."""
    ticket = Ticket(
        customer_email="user@voltkart.in",
        subject="Warranty check",
        body="How long is the warranty?",
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)

    reply = Reply(
        ticket_id=ticket.id,
        draft_text="All electronics include a standard 1-year warranty.",
        citations=["warranty-and-repairs.md"],
        confidence=0.95,
        decision="auto_reply",
    )
    audit = AuditLog(
        ticket_id=ticket.id,
        step="resolve",
        payload={"confidence": 0.95},
    )
    db_session.add(reply)
    db_session.add(audit)
    db_session.commit()

    assert len(ticket.replies) == 1
    assert ticket.replies[0].confidence == 0.95
    assert len(ticket.audit_logs) == 1
    assert ticket.audit_logs[0].step == "resolve"
