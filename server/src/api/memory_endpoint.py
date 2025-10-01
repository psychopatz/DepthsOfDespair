# ==============================================================================
# memory_endpoint.py
#
# This module defines the API endpoints for all memory-related operations.
# It acts as the public interface for the Godot client to interact with an
# NPC's memory, abstracting away the underlying database logic.
#
# All core implementation is handled by the `MemoryManager` in the `src.core`
# package. This file is the "API Layer" or "Controller Layer".
# ==============================================================================

# --- Imports ---
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from typing import List

# Core business logic for handling memory operations.
from src.core.memory_manager import MemoryManager
# Pydantic models that define the strict data contracts for our API.
from src.schemas.memory import (
    Memory, AddMemoryRequest, AddMemoryResponse,
    MemorySearchRequest, RetrieveMemoriesRequest,
    DeleteMemoryRequest, DeleteMemoryResponse
)

# --- Router Setup ---
# We create a router to group all memory-related endpoints.
# - 'prefix="/memory"': All routes in this file will start with '/memory'
#   (e.g., http://localhost:8000/memory/add).
# - 'tags=["Memory Management"]': Groups all these endpoints under a "Memory Management"
#   section in the auto-generated API docs (at /docs).
router = APIRouter(prefix="/memory", tags=["Memory Management"])


# --- Dependency Injection ---
def get_memory_manager(request: Request) -> MemoryManager:
    """
    This is a dependency injection function. FastAPI runs this for any endpoint
    that includes `memory_manager: MemoryManager = Depends(get_memory_manager)`.
    
    It fetches the single, shared `MemoryManager` instance that was created
    when the server started (in `main.py`) and stored in `app.state`. This is the
    standard way to manage shared resources and state in FastAPI.
    """
    return request.app.state.memory_manager


# ==============================================================================
# --- CRUD Endpoints ---
# ==============================================================================

# --- CREATE ---
@router.post("/add", response_model=AddMemoryResponse)
async def add_npc_memory(
    request_body: AddMemoryRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Saves a new memory to an NPC's database.
    
    This endpoint is used to create a new memory entry. We use the HTTP POST
    method as it's the standard for creating new resources on the server.
    """
    try:
        # The endpoint's logic is simple: it validates the input (via Pydantic)
        # and passes the data to the memory_manager, which does the heavy lifting.
        new_id = await memory_manager.add_memory(
            save_id=request_body.save_id,
            npc_id=request_body.npc_id,
            memory_text=request_body.memory_text,
            metadata=request_body.metadata
        )
        return AddMemoryResponse(new_memory_id=new_id)
    except Exception as e:
        # Catch any unexpected errors from the core logic and return a generic
        # but informative 500 Internal Server Error.
        raise HTTPException(status_code=500, detail=str(e))


# --- READ (by Filter) ---
@router.post("/search", response_model=List[Memory])
def search_npc_memories(
    request_body: MemorySearchRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Searches memories using exact metadata filters (no vector search).
    
    Even though this is a "read" operation, we use POST because the filtering
    criteria can be a complex JSON object, which is not suitable for a GET
    request's URL parameters. This is a common and accepted API design pattern.
    """
    return memory_manager.search_memories(
        save_id=request_body.save_id,
        npc_id=request_body.npc_id,
        filter_metadata=request_body.filter_metadata,
        limit=request_body.limit
    )


# --- READ (by Similarity) ---
@router.post("/retrieve", response_model=List[Memory])
async def retrieve_npc_memories(
    request_body: RetrieveMemoriesRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Retrieves the most semantically relevant memories based on a query text.
    This is the core of the RAG (Retrieval-Augmented Generation) pattern.
    """
    return await memory_manager.retrieve_relevant_memories(
        save_id=request_body.save_id,
        npc_id=request_body.npc_id,
        query_text=request_body.query_text,
        n_results=request_body.n_results,
        filter_metadata=request_body.filter_metadata
    )


# --- DELETE ---
@router.post("/delete", response_model=DeleteMemoryResponse)
def delete_npc_memory(
    request_body: DeleteMemoryRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Deletes a specific memory from an NPC's database by its unique ID.
    
    While a DELETE HTTP method exists, using POST is simpler for APIs that
    consistently expect JSON bodies for all operations.
    """
    success = memory_manager.delete_memory(
        save_id=request_body.save_id,
        npc_id=request_body.npc_id,
        memory_id=request_body.memory_id
    )
    # Provide a specific, user-friendly error if the memory to be deleted
    # was not found, instead of a generic server error.
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory with ID '{request_body.memory_id}' not found.")
    
    return DeleteMemoryResponse(message=f"Memory '{request_body.memory_id}' deleted successfully.")


# --- READ (All) ---
@router.get("/list_all", response_model=List[Memory])
def list_all_npc_memories(
    # We use GET here because the parameters are simple identifiers and fit
    # perfectly in a URL's query string (e.g., /memory/list_all?save_id=...&npc_id=...).
    save_id: str = Query(..., description="The ID of the save file."),
    npc_id: str = Query(..., description="The unique ID of the NPC."),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Lists all memories for a specific NPC, up to a reasonable limit.
    This is primarily intended as a debugging and inspection tool.
    """
    return memory_manager.get_all_memories(
        save_id=save_id,
        npc_id=npc_id
    )