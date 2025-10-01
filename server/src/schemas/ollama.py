from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union


class GenerateRequest(BaseModel):
    prompt: str
    stream: bool = Field(default=False)
    options: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = Field(default=False)
    options: Optional[Dict[str, Any]] = None

class EmbedRequest(BaseModel):
    input: Union[str, List[str]]
    options: Optional[Dict[str, Any]] = None


class ModelRequest(BaseModel):
    """A generic request that needs a model name for management tasks."""
    model: str

class PullRequest(BaseModel):
    """Request to pull a model. `stream` is supported."""
    model: str
    stream: bool = Field(default=False)