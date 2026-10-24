"""Simple test script to save a ticket and print its generated ID."""

from app.db import SessionLocal, Ticket, init_db


def main() -> None:
    # 1. Initialize tables
    init_db()

    # 2. Open a database session
    db = SessionLocal()

    try:
        # 3. Create a sample VoltKart ticket
        sample_ticket = Ticket(
            customer_email="rahul.sharma@example.com",
            subject="Question regarding 30-day return policy",
            body="Hi VoltKart team, I received my headphones 5 days ago and want to know how reverse pickup works.",
            category="returns",
            priority="medium",
            sentiment="neutral",
            status="open",
        )

        # 4. Save ticket to the database
        db.add(sample_ticket)
        db.commit()
        db.refresh(sample_ticket)

        # 5. Print the ticket ID
        print(f"Ticket saved successfully with ID: {sample_ticket.id}")

    finally:
        # 6. Always close the database session
        db.close()


if __name__ == "__main__":
    main()
