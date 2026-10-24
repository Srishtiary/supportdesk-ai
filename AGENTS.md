# SupportDesk AI
A support-ticket agent for a fictional electronics store "VoltKart".
Pipeline: triage -> retrieve -> resolve -> route.

## Rules
- Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, type hints everywhere.
- Every LLM call returns JSON validated by a Pydantic model; retry once if invalid.
- Prompts live in app/prompts/*.md, never inside Python code.
- Secrets only in .env.
- Every pipeline step writes a row to the audit_log table.
- Write pytest tests for each module.
- I am a beginner: before coding any task, give a short plan and wait for my OK.
  After coding, explain each file in simple language.