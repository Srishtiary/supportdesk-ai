"""Unit tests for the end-to-end ticket processing pipeline."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, Ticket
from app.pipeline import process_ticket


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database session for pipeline tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_pipeline_happy_path(test_db):
    """Verify that a standard inquiry flows through triage, retrieve, resolve, and route."""
    ticket = Ticket(
        customer_email="anita@example.com",
        subject="30-day return policy",
        body="How many days do I have to return an unopened item to VoltKart?",
    )
    test_db.add(ticket)
    test_db.commit()
    test_db.refresh(ticket)

    processed_ticket = process_ticket(test_db, ticket)

    assert processed_ticket.id is not None
    assert processed_ticket.category == "returns"
    assert processed_ticket.status in ["auto_sent", "pending_approval"]

    # Verify Reply was saved
    assert len(processed_ticket.replies) == 1
    reply = processed_ticket.replies[0]
    assert reply.decision in ["auto_send", "draft"]
    assert "30" in reply.draft_text

    # Verify AuditLog entries were created for every step
    step_names = [log.step for log in processed_ticket.audit_logs]
    assert "triage" in step_names
    assert "retrieve" in step_names
    assert "resolve" in step_names
    assert "route" in step_names


def test_pipeline_error_handling_escalation(test_db, monkeypatch):
    """Verify that if an LLM fails, the pipeline catches the error and escalates safely."""
    ticket = Ticket(
        customer_email="error_test@example.com",
        subject="Simulated failure",
        body="This will trigger a mock failure.",
    )
    test_db.add(ticket)
    test_db.commit()
    test_db.refresh(ticket)

    # Simulate an LLM failure
    def mock_failing_triage(subject, body):
        raise RuntimeError("Simulated Gemini connection timeout")

    monkeypatch.setattr("app.pipeline.triage_ticket", mock_failing_triage)

    processed_ticket = process_ticket(test_db, ticket)

    # Verify graceful degradation
    assert processed_ticket.status == "escalated"
    assert len(processed_ticket.replies) == 1
    assert processed_ticket.replies[0].decision == "escalate"

    # Verify error step is logged
    step_names = [log.step for log in processed_ticket.audit_logs]
    assert "error" in step_names
