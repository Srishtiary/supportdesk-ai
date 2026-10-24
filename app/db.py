"""Database configuration and models for VoltKart SupportDesk AI."""

from datetime import datetime
from typing import Any, Generator, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

# SQLite database file in the project root
DATABASE_URL: str = "sqlite:///./voltkart.db"

# Create the SQLite engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Session factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for all database models
class Base(DeclarativeBase):
    pass


class Ticket(Base):
    """Stores incoming customer support tickets."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    replies: Mapped[list["Reply"]] = relationship(
        "Reply", back_populates="ticket", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="ticket", cascade="all, delete-orphan"
    )


class Reply(Base):
    """Stores AI-generated replies and routing decisions for a ticket."""

    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tickets.id"), nullable=False
    )
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    final_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citations: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationship back to ticket
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="replies")


class AuditLog(Base):
    """Stores audit records for every pipeline step."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tickets.id"), nullable=True
    )
    step: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationship back to ticket
    ticket: Mapped[Optional["Ticket"]] = relationship(
        "Ticket", back_populates="audit_logs"
    )


def init_db() -> None:
    """Create all database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
