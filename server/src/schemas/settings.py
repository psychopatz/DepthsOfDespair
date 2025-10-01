# src/schemas/settings.py
from pydantic import BaseModel, Field

class GameSettings(BaseModel):
    """Global settings for the LLM server."""
    ollama_host: str = Field(
        default="http://127.0.0.1:11434",
        description="The host address for the Ollama server."
    )
    chat_model: str = Field(
        default="gemma3:4b", # <-- UPDATED DEFAULT
        description="The default model name to use for generating dialogue."
    )
    embedding_model: str = Field(
        default="nomic-embed-text:latest", # <-- UPDATED DEFAULT
        description="The model to use for creating embeddings for memories."
    )