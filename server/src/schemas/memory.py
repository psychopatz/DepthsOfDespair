# ==============================================================================
# src/schemas/memory.py
#
# This file defines the Pydantic models (schemas) for the Memory system.
# These models act as the strict data contracts for the API endpoints defined
# in src/api/memory_endpoint.py.
#
# They ensure that data sent between Godot and the server is correctly typed,
# validated, and documented in the Swagger UI.
# ==============================================================================

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

# ==============================================================================
# --- Core Data Object ---
# ==============================================================================

class Memory(BaseModel):
    """
    Represents a single memory retrieved from the vector database (ChromaDB).
    This is the standard output format for reading memories.
    """
    id: str = Field(
        ...,
        description="The unique UUID of the memory, generated upon creation."
    )
    text: str = Field(
        ...,
        description="The canonical, immutable text summary of the memory."
    )
    metadata: Dict[str, Any] = Field(
        ...,
        description="Structured data attached to the memory (type, timestamp, etc.)."
    )
    distance: Optional[float] = Field(
        None,
        description="The semantic distance score from the query (0.0 is exact match). Only present in similarity searches."
    )


# ==============================================================================
# --- CREATE Operation (/memory/add) ---
# ==============================================================================

class AddMemoryRequest(BaseModel):
    """Payload for saving a new memory to an NPC's database."""
    save_id: str = Field(
        ...,
        description="The ID of the current save file."
    )
    npc_id: str = Field(
        ...,
        description="The unique ID of the NPC forming the memory."
    )
    memory_text: str = Field(
        ...,
        description="The canonical summary of the event, preferably using IDs like [PLAYER] or [NPC_ID:...]."
    )
    metadata: Dict[str, Any] = Field(
        ...,
        description="Structured data to categorize the memory."
    )

    # Provides a default example in the Swagger UI for easy testing
    model_config = {
        "json_schema_extra": {
            "example": {
                "save_id": "save_slot_01",
                "npc_id": "npc_korgan_blacksmith_1a8f",
                "memory_text": "[PLAYER] complimented my finest sword.",
                "metadata": {
                    "type": "dialogue",
                    "source": "[PLAYER]",
                    "importance": 0.5,
                    "timestamp": "2025-10-27T10:00:00Z"
                }
            }
        }
    }

class AddMemoryResponse(BaseModel):
    """Response after successfully adding a memory."""
    new_memory_id: str = Field(..., description="The UUID of the newly created memory.")


# ==============================================================================
# --- READ (by Filter) Operation (/memory/search) ---
# ==============================================================================

class MemorySearchRequest(BaseModel):
    """Payload for finding memories using exact metadata matches (like SQL WHERE)."""
    save_id: str
    npc_id: str
    filter_metadata: Dict[str, Any] = Field(
        ...,
        description="Key-value pairs that MUST match exactly."
    )
    limit: int = Field(
        100, ge=1, le=1000,
        description="Max number of results to return."
    )

    # Swagger UI Example
    model_config = {
        "json_schema_extra": {
            "example": {
                "save_id": "save_slot_01",
                "npc_id": "npc_korgan_blacksmith_1a8f",
                "filter_metadata": {
                    "type": "dialogue"
                },
                "limit": 10
            }
        }
    }


# ==============================================================================
# --- READ (by Similarity) Operation (/memory/retrieve) ---
# ==============================================================================

class RetrieveMemoriesRequest(BaseModel):
    """Payload for finding memories based on semantic meaning (RAG)."""
    save_id: str
    npc_id: str
    query_text: str = Field(
        ...,
        description="The text (e.g., player input) to find conceptually similar memories for."
    )
    n_results: int = Field(
        5, ge=1, le=20,
        description="Number of most relevant memories to return."
    )
    filter_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional: Filter by metadata *before* performing the vector search."
    )

    # Swagger UI Example
    model_config = {
        "json_schema_extra": {
            "example": {
                "save_id": "save_slot_01",
                "npc_id": "npc_korgan_blacksmith_1a8f",
                "query_text": "What does Korgan think about the player's attitude?",
                "n_results": 3
            }
        }
    }


# ==============================================================================
# --- DELETE Operation (/memory/delete) ---
# ==============================================================================

class DeleteMemoryRequest(BaseModel):
    """Payload for deleting a specific memory."""
    save_id: str
    npc_id: str
    memory_id: str = Field(..., description="The specific UUID of the memory to delete.")

    # Swagger UI Example
    model_config = {
        "json_schema_extra": {
            "example": {
                "save_id": "save_slot_01",
                "npc_id": "npc_korgan_blacksmith_1a8f",
                "memory_id": "paste-real-uuid-here"
            }
        }
    }

class DeleteMemoryResponse(BaseModel):
    """Response after attempting to delete a memory."""
    status: str = "success"
    message: str