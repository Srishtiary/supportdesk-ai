from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.config import settings

# Create the Gemini client once and reuse it everywhere
client = genai.Client(api_key=settings.gemini_api_key)


def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the raw text it replies with."""
    response = client.models.generate_content(
        model=settings.llm_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return response.text or ""


def generate_json(prompt: str, schema: type[BaseModel], max_retries: int = 1) -> BaseModel:
    """Ask Gemini for JSON and check it against a Pydantic schema. Retry if invalid."""
    last_error = None

    for attempt in range(max_retries + 1):
        raw_text = ask_gemini(prompt)
        try:
            return schema.model_validate_json(raw_text)
        except ValidationError as error:
            last_error = error
            print(f"Attempt {attempt + 1} failed: invalid JSON from the LLM")

    raise ValueError(f"LLM returned invalid JSON after retries: {last_error}")


def embed(texts: list[str]) -> list[list[float]]:
    """Convert a list of texts into a list of vectors (lists of numbers)."""
    response = client.models.embed_content(
        model=settings.embed_model,
        contents=texts,
    )

    vectors = []
    for item in response.embeddings:
        vectors.append(item.values)

    return vectors