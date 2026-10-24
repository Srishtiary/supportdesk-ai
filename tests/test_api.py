"""Unit tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

# Shared in-memory SQLite database across threads
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_root_redirects_to_docs():
    """Verify that visiting / redirects to /docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"



def test_post_tickets_endpoint():
    """Verify POST /tickets creates and processes a ticket."""
    payload = {
        "customer_email": "priya@example.com",
        "subject": "Return period question",
        "body": "What is the return window for a laptop purchased on VoltKart?",
    }
    response = client.post("/tickets", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "ticket_id" in data
    assert data["ticket_id"] is not None
    assert data["status"] in ["auto_sent", "pending_approval", "escalated"]
    assert "reply" in data
    assert len(data["reply"]) > 0


def test_get_tickets_listing_and_filter():
    """Verify GET /tickets lists tickets and filters by status."""
    res = client.get("/tickets")
    assert res.status_code == 200
    all_tickets = res.json()
    assert len(all_tickets) >= 1

    # Filter by non-matching status
    res_filtered = client.get("/tickets?status=unknown_status")
    assert res_filtered.status_code == 200
    assert len(res_filtered.json()) == 0


def test_get_ticket_details():
    """Verify GET /tickets/{id} returns details with replies and audit log."""
    post_res = client.post(
        "/tickets",
        json={
            "customer_email": "vikram@example.com",
            "subject": "Warranty check",
            "body": "Does my monitor come with a 1 year warranty?",
        },
    )
    ticket_id = post_res.json()["ticket_id"]

    res = client.get(f"/tickets/{ticket_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == ticket_id
    assert "replies" in data
    assert "audit_logs" in data
    assert len(data["audit_logs"]) >= 1

    # Check 404 for non-existent ID
    res_404 = client.get("/tickets/999999")
    assert res_404.status_code == 404


def test_approve_ticket_endpoint():
    """Verify POST /tickets/{id}/approve sets status to closed with edited text."""
    post_res = client.post(
        "/tickets",
        json={
            "customer_email": "neha@example.com",
            "subject": "Exchange question",
            "body": "Can I exchange my old phone?",
        },
    )
    ticket_id = post_res.json()["ticket_id"]

    # Approve with edited reply text
    approve_payload = {"edited_text": "Yes, you can exchange your phone at doorstep."}
    approve_res = client.post(f"/tickets/{ticket_id}/approve", json=approve_payload)
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["status"] == "closed"
    assert approve_data["final_reply"] == "Yes, you can exchange your phone at doorstep."

    # Verify status changed when re-fetching
    get_res = client.get(f"/tickets/{ticket_id}")
    assert get_res.json()["status"] == "closed"
