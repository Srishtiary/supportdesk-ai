"""Resolution module for answering customer tickets using KB retrieval."""

from pathlib import Path
from typing import Any

from app.llm import generate_json
from app.retriever import search
from app.schemas import ResolverResult

# Path to the resolver prompt markdown template
PROMPT_FILE = Path(__file__).parent / "prompts" / "resolver.md"


def resolve_ticket(
    subject: str,
    body: str,
    k: int = 4,
) -> tuple[ResolverResult, float, list[dict[str, Any]]]:
    """Retrieve relevant KB chunks, call Gemini to draft an answer, and return the result."""
    # 1. Search the Knowledge Base using subject and body
    search_query = f"{subject} {body}".strip()
    chunks = search(search_query, k=k)

    # 2. Get the top similarity score
    top_retrieval_score = float(chunks[0]["score"]) if chunks else 0.0

    # 3. Format retrieved excerpts into context text
    context_parts: list[str] = []
    for chunk in chunks:
        chunk_id = chunk.get("id", "")
        text = chunk.get("text", "")
        context_parts.append(f"[{chunk_id}]\n{text}")

    context_text = (
        "\n\n---\n\n".join(context_parts)
        if context_parts
        else "No relevant articles found."
    )

    # 4. Fill in prompt placeholders using .replace()
    prompt_template = PROMPT_FILE.read_text(encoding="utf-8")
    filled_prompt = (
        prompt_template.replace("{{SUBJECT}}", subject)
        .replace("{{BODY}}", body)
        .replace("{{CONTEXT}}", context_text)
    )

    # 5. Generate and validate the structured response
    result = generate_json(filled_prompt, ResolverResult)

    return result, top_retrieval_score, chunks
