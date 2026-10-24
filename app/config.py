from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All project settings in one place. Values come from the .env file."""

    model_config = SettingsConfigDict(env_file=".env")

    gemini_api_key: str
    llm_model: str = "gemini-2.5-flash"
    embed_model: str = "gemini-embedding-001"

    # Confidence thresholds used by the router
    auto_threshold: float = 0.85    # at or above this: auto-send
    draft_threshold: float = 0.55   # at or above this: human approval, below: escalate


# One shared settings object used by the whole project
settings = Settings()