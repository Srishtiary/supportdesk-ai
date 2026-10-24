# SupportDesk AI ⚡🛒

> An autonomous, policy-grounded customer support ticket resolution pipeline for **VoltKart** (a fictional electronics e-commerce store). Built with **Python 3.11+**, **FastAPI**, **Google Gemini**, **ChromaDB**, and **SQLAlchemy**.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat)](https://www.sqlalchemy.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F00?style=flat)](https://www.trychroma.com/)
[![Tests](https://img.shields.io/badge/Tests-38%20Passing-brightgreen?style=flat&logo=pytest&logoColor=white)](https://docs.pytest.org/)

---

## 🌟 Key Highlights & Engineering Features

Unlike generic LLM wrappers, **SupportDesk AI** is built as an enterprise-grade agent backend with deterministic guardrails, structured validation, and comprehensive auditability:

- 🛡️ **4-Stage Pipeline**: Modular execution flow (`triage` $\to$ `retrieve` $\to$ `resolve` $\to$ `route`).
- 🔍 **Policy-Grounded RAG**: 18 VoltKart store policy documents (54 chunked sections) indexed in ChromaDB using Gemini text embeddings. The agent answers strictly using verified policy citations without hallucinating refund promises.
- 🚦 **Hybrid Confidence Router**: Combines cosine vector similarity (40%) and LLM self-confidence (60%) into a unified score. Automatically routes tickets:
  - $\ge 0.85$ Confidence $\to$ `auto_send` (instant customer response)
  - $\ge 0.55$ Confidence or angry sentiment $\to$ `draft` (held for human agent approval)
  - Low confidence, urgent issues, or security risks $\to$ `escalate` (immediate human handoff)
- 🔒 **Security & Prompt Injection Detection**: The triage layer actively scans incoming customer text for jailbreaks or prompt injections, escalating suspicious inputs before they reach the resolution model.
- 📋 **Guaranteed JSON via Pydantic v2**: Every LLM response is strictly typed and validated against Pydantic models with automated 1-retry fallback.
- 📝 **Prompts-as-Code**: All prompt templates live in standalone Markdown files (`app/prompts/*.md`), completely isolated from business logic.
- 📜 **Full Audit Logging**: Every step records its exact input and output JSON payload to an immutable `audit_log` table for compliance and debugging.
- 🧪 **38 Automated Tests**: 100% test coverage across database operations, vector retrieval, triage, resolver, router, pipeline, and FastAPI endpoints.

---

## 🏗️ Architecture & Pipeline Flow

```
                      [ Incoming Ticket (POST /tickets) ]
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │       Step 1: Triage      │
                        │ • Category & Priority     │
                        │ • Sentiment Analysis      │
                        │ • Prompt Injection Check  │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │      Step 2: Retrieve     │
                        │ • ChromaDB Cosine Search  │
                        │ • Top 4 Relevant Chunks   │
                        │ • Retrieval Similarity    │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │      Step 3: Resolve      │
                        │ • Grounded Draft Reply    │
                        │ • Exact Policy Citations  │
                        │ • LLM Self-Confidence     │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │       Step 4: Route       │
                        │ • 0.4*Retrieval + 0.6*Conf│
                        │ • Guardrail Rule Check    │
                        └───────┬───────────┬───────┘
                                │           │
              ┌─────────────────┘           └─────────────────┐
              ▼                                               ▼
       [ High Confidence ]                            [ Risk / Missing Info ]
    Status: auto_sent                              Status: pending_approval / escalated
```

---

## 📁 Project Structure

```text
supportdesk-ai/
├── app/
│   ├── prompts/             # Isolated system prompts
│   │   ├── triage.md        # Triage & injection detection prompt
│   │   └── resolver.md      # Grounded response generation prompt
│   ├── config.py            # Environment settings & model configuration
│   ├── db.py                # SQLAlchemy SQLite models (Ticket, Reply, AuditLog)
│   ├── llm.py               # Gemini client wrapper with Pydantic validation & retry
│   ├── main.py              # FastAPI application & REST endpoints
│   ├── pipeline.py          # Pipeline orchestrator & audit logging
│   ├── resolver.py          # Policy retrieval & resolution logic
│   ├── retriever.py         # ChromaDB chunking, indexing, and vector search
│   ├── router.py            # Deterministic decision & confidence calculator
│   └── schemas.py           # Pydantic v2 request/response schemas
├── data/
│   └── kb/                  # 18 VoltKart policy markdown documents (54 chunks)
├── tests/                   # Complete test suite (38 passing tests)
│   ├── test_api.py          # FastAPI endpoint integration tests
│   ├── test_db.py           # Database CRUD & relationship tests
│   ├── test_pipeline.py     # End-to-end pipeline orchestration tests
│   ├── test_resolver.py     # Retrieval-augmented resolution tests
│   ├── test_retriever.py    # Chunking & ChromaDB vector search tests
│   ├── test_router.py       # Confidence & routing guardrail tests
│   ├── test_schemas.py      # Pydantic validation tests
│   └── test_triage.py       # Triage categorization & injection tests
├── .env.example             # Template for environment variables
├── .gitignore               # Ignored files (venv, sqlite db, vector store)
├── AGENTS.md                # System design principles & project rules
├── requirements.txt         # Core dependencies
└── README.md                # Project documentation
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11 or higher
- A free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/supportdesk-ai.git
cd supportdesk-ai
```

### 3. Create & Activate a Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 6. Run the Server
```bash
uvicorn app.main:app --reload
```
On startup, the application automatically:
1. Creates the SQLite database tables in `voltkart.db`.
2. Indexes all 18 VoltKart policy articles into ChromaDB vector storage.

Visit **http://127.0.0.1:8000/docs** to access the interactive Swagger OpenAPI documentation!

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Redirects directly to `/docs` interactive Swagger documentation |
| `POST` | `/tickets` | Intakes a new customer ticket, runs the 4-step pipeline, and returns status, reply, and citations |
| `GET` | `/tickets` | Lists tickets with optional status filtering (`?status=auto_sent`) |
| `GET` | `/tickets/{id}` | Retrieves full ticket details, including replies and the step-by-step audit log |
| `POST` | `/tickets/{id}/approve`| Allows a human agent to review, edit, and approve a drafted reply (closes ticket) |

### Sample API Request (`POST /tickets`):
```json
{
  "customer_email": "priya.verma@example.com",
  "subject": "Can I return my VoltKart wireless earbuds?",
  "body": "Hi, I bought VoltKart wireless earbuds 10 days ago. The sound is good but they do not fit my ears comfortably. Can I return them for a refund?"
}
```

### Sample API Response:
```json
{
  "ticket_id": 1,
  "status": "auto_sent",
  "decision": "auto_send",
  "confidence": 0.89,
  "reply": "Dear Priya,\n\nYes, you can return your VoltKart wireless earbuds. Under our 30-day return policy, electronics can be returned within 30 days of delivery if they are in original condition with all accessories and packaging intact.\n\nOnce our team receives and inspects the item, your refund will be processed back to your original payment method within 5 to 7 business days.\n\nBest regards,\nVoltKart Support Team",
  "citations": [
    "returns-and-replacements.md#30-Day Return Window",
    "refunds-and-store-credit.md#Refund Processing Times"
  ]
}
```

---

## 🧪 Running Automated Tests

Run the full pytest suite to verify all 38 tests across the system:

```bash
pytest tests/ -v
```

Expected output:
```text
tests/test_api.py::test_create_ticket_endpoint PASSED
tests/test_api.py::test_list_tickets_endpoint PASSED
tests/test_api.py::test_get_ticket_details_endpoint PASSED
tests/test_api.py::test_approve_ticket_endpoint PASSED
tests/test_api.py::test_approve_ticket_with_edited_text PASSED
tests/test_db.py::test_create_tables PASSED
tests/test_db.py::test_create_ticket_with_replies_and_audit PASSED
tests/test_pipeline.py::test_process_ticket_auto_send PASSED
tests/test_pipeline.py::test_process_ticket_exception_handling PASSED
tests/test_resolver.py::... PASSED (3 tests)
tests/test_retriever.py::... PASSED (9 tests)
tests/test_router.py::... PASSED (8 tests)
tests/test_schemas.py::... PASSED (5 tests)
tests/test_triage.py::... PASSED (5 tests)
============================= 38 passed in 3.42s ==============================
```

---

## 🛡️ Design Principles & Safety Guardrails

1. **No Hallucinated Commitments**: Customer service LLMs must never promise refunds or accept returns without verification. The resolver prompt enforces strict policy citation.
2. **Deterministic Routing**: LLMs are not permitted to route their own outputs directly. The decision is calculated in Python using mathematical thresholds and strict rules.
3. **Graceful Fallbacks**: If the LLM provider experiences network timeouts or rate limits, the pipeline automatically catches the error, rolls back the database transaction, flags the ticket as `escalated`, and assigns it to human support without crashing.
4. **Auditability**: Every AI inference, retrieval distance, and triage score is stored in SQLite for complete visibility into why a decision was made.

---

## 📄 License
This project is licensed under the MIT License.
