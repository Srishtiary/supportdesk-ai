"""Triage module for classifying incoming VoltKart customer tickets."""

from pathlib import Path

from app.llm import generate_json
from app.schemas import TriageResult

# Path to the triage markdown prompt file
PROMPT_FILE = Path(__file__).parent / "prompts" / "triage.md"


def triage_ticket(subject: str, body: str) -> TriageResult:
    """Analyze a customer ticket and return structured classification."""
    # 1. Read the prompt markdown template
    prompt_template = PROMPT_FILE.read_text(encoding="utf-8")

    # 2. Fill in the placeholders using .replace()
    filled_prompt = (
        prompt_template.replace("{{SUBJECT}}", subject)
        .replace("{{BODY}}", body)
    )

    # 3. Call Gemini and validate against TriageResult schema
    result = generate_json(filled_prompt, TriageResult)

    return result
