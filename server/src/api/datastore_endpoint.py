# ==============================================================================
# datastore_endpoint.py
#
# This module defines the generic CRUD API endpoints for all vector data stores.
# It acts as the public interface for the Godot client (or any other client)
# to interact with the game's RAG databases. It orchestrates calls to the
# DataManager and LLMService to fulfill requests.
# ==============================================================================

from fastapi import APIRouter, Depends, Request, HTTPException, Query, Body
from fastapi.openapi.models import Example
from typing import List, Optional
from src.core.data_manager import DataManager
from src.core.llm_service import LLMService
from src.schemas.enums import DataStoreType
from src.schemas.memory import Memory
from src.schemas.datastore import (
    AddEntryRequest, AddEntryResponse, RetrieveEntriesRequest,
    SearchEntriesRequest, DeleteEntryRequest, DeleteEntryResponse,
    UpdateEntryRequest, UpdateEntryResponse
)

# --- Reusable Examples for Swagger/OpenAPI Docs ---
# This dictionary provides pre-filled examples for the /add endpoint in the
# interactive API documentation, making it much easier to test.
# Note: The 'store_type' uses the string value of the enum, which is what the
# actual JSON request will contain.
add_entry_examples = {
    "Add NPC Memory": Example(
        summary="Add a dynamic memory for an NPC",
        description="Creates a memory entry in a specific NPC's `memory_db`. Note that `npc_id` is required.",
        value={
            "store_type": "memory_db",
            "save_id": "save_slot_01",
            "npc_id": "korgan_ironhand_a3f8",
            "text": "The player asked about my family, and I told them about my mother who worked in the Sunstone Mine.",
            "metadata": {
                "type": "dialogue",
                "source": "{@player:player_main}",
                "importance": 0.7,
                "game_tick": 40321
            }
        }
    ),
    "Add World Lore": Example(
        summary="Add a static lore entry for the world",
        description="Creates a lore entry in the save file's `lore_db`. Note that `npc_id` must be `null` or omitted.",
        value={
            "store_type": "lore_db",
            "save_id": "save_slot_01",
            "text": "The Sunstone Mine was the primary source of iron for the kingdom before its collapse fifty years ago during the Great Quake.",
            "metadata": {
                "scope": "location_history",
                "location_id": "sunstone_mine_ruins_b4c1"
            }
        }
    )
}

# --- Router & Dependencies ---
router = APIRouter(prefix="/datastore", tags=["Data Store Management"])
def get_data_manager(request: Request) -> DataManager: return request.app.state.data_manager
def get_llm_service(request: Request) -> LLMService: return request.app.state.llm_service

# --- CRUD Endpoints ---

@router.post("/add", response_model=AddEntryResponse)
async def add_datastore_entry(
    req: AddEntryRequest = Body(..., openapi_examples=add_entry_examples),
    data_manager: DataManager = Depends(get_data_manager),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    ### Adds a new entry to any specified vector data store.
    
    This is the primary endpoint for populating all RAG databases. Its behavior is
    determined by the `store_type` provided in the request body.

    **Valid `store_type` values are:**
    - `'lore_db'`
    - `'lexicon_db'`
    - `'fact_db'`
    - `'memory_db'`
    - `'quest_triggers_db'`

    ---
    
    ### RAG Best Practices & Custom Metadata:
    - **`text` is for SEMANTICS:** Use natural language prose. This is what the AI "understands."
    - **`metadata` is for FILTERING:** Use structured key-value pairs. You can **add any custom fields** you need for your game's logic (e.g., `"quest_stage": 2`, `"is_secret": true`). For time-based queries, always include a **`game_tick`** integer.
    """
    try:
        embedding_response = await llm_service.generate_embeddings(req.text)
        embedding = embedding_response['embeddings'][0]
        new_id = data_manager.add_entry(
            store_type=req.store_type, save_id=req.save_id, npc_id=req.npc_id,
            text=req.text, embedding=embedding, metadata=req.metadata
        )
        return AddEntryResponse(new_entry_id=new_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrieve", response_model=List[Memory])
async def retrieve_datastore_entries(req: RetrieveEntriesRequest, data_manager: DataManager = Depends(get_data_manager), llm_service: LLMService = Depends(get_llm_service)):
    """
    ### Retrieves entries using semantic search, with optional filters.

    This is the core RAG endpoint. It finds entries based on conceptual meaning.

    - **Pure Semantic Search:** To search the entire data store (e.g., all of `'lore_db'`), simply omit the `filter_metadata` and time filter fields from your request.
    - **Hybrid Search:** To improve performance and precision, provide `filter_metadata` (including any of your custom fields) and/or a time range. The database filters first, then performs the vector search on the smaller result set.
    """
    try:
        embedding_response = await llm_service.generate_embeddings(req.query_text)
        embedding = embedding_response['embeddings'][0]
        return data_manager.retrieve_entries(
            store_type=req.store_type, save_id=req.save_id, npc_id=req.npc_id,
            query_embedding=embedding, n_results=req.n_results, 
            filter_metadata=req.filter_metadata,
            time_from_tick=req.time_from_tick,
            time_to_tick=req.time_to_tick
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=List[Memory])
def search_datastore_entries(req: SearchEntriesRequest, data_manager: DataManager = Depends(get_data_manager)):
    """
    ### Searches entries using exact metadata and/or game tick range filters.
    
    This is for direct, fast lookups, like a traditional database query. It does **not** perform a semantic search.

    - The `filter_metadata` field can contain **any custom keys** you've saved.
    - To get the most recent entries up to the limit, omit all filter fields.
    """
    return data_manager.search_entries(
        store_type=req.store_type, save_id=req.save_id, npc_id=req.npc_id,
        filter_metadata=req.filter_metadata, limit=req.limit,
        time_from_tick=req.time_from_tick, time_to_tick=req.time_to_tick
    )

@router.post("/update", response_model=UpdateEntryResponse)
async def update_datastore_entry(req: UpdateEntryRequest, data_manager: DataManager = Depends(get_data_manager), llm_service: LLMService = Depends(get_llm_service)):
    """
    ### Updates an existing entry in a data store.

    This performs a 'delete-then-add' operation. This is the correct way to
    update a document in a vector database, as it ensures the new text is
    correctly embedded and indexed. The original `entry_id` will be destroyed,
    and a new one will be returned.

    If the provided `entry_id` does not exist, this endpoint will return a
    **404 Not Found** error.
    """
    try:
        embedding_response = await llm_service.generate_embeddings(req.new_text)
        embedding = embedding_response['embeddings'][0]
        new_id = data_manager.update_entry(
            store_type=req.store_type, save_id=req.save_id, npc_id=req.npc_id,
            entry_id=req.entry_id,
            new_text=req.new_text,
            new_embedding=embedding,
            new_metadata=req.new_metadata
        )

        if new_id is None:
            raise HTTPException(
                status_code=404,
                detail=f"Entry with ID '{req.entry_id}' not found in the specified store."
            )

        return UpdateEntryResponse(new_entry_id=new_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete", response_model=DeleteEntryResponse)
def delete_datastore_entry(req: DeleteEntryRequest, data_manager: DataManager = Depends(get_data_manager)):
    """
    ### Deletes a specific entry from a data store by its unique ID.
    
    If the provided `entry_id` does not exist in the specified store, this
    endpoint will return a 404 Not Found error.
    """
    success = data_manager.delete_entry(
        store_type=req.store_type, save_id=req.save_id, npc_id=req.npc_id, entry_id=req.entry_id
    )
    if not success:
        raise HTTPException(status_code=404, detail=f"Entry with ID '{req.entry_id}' not found in the specified store.")
    return DeleteEntryResponse(status="success", message=f"Entry '{req.entry_id}' deleted successfully.")

@router.get("/list_all", response_model=List[Memory])
def list_all_entries(
    store_type: DataStoreType = Query(..., description="The data store to query. Valid values: 'lore_db', 'lexicon_db', 'fact_db', 'memory_db', 'quest_triggers_db'.",example="memory_db"),
    save_id: str = Query(..., description="The ID of the save file.",example="save_slot_01"),
    npc_id: Optional[str] = Query(None, description="The NPC's unique ID (required for NPC-specific stores).",example="korgan_ironhand_a3f8"),
    limit: int = Query(1000, ge=1, le=5000, description="The maximum number of entries to return."),
    data_manager: DataManager = Depends(get_data_manager)
):
    """
    ### Lists all entries in a specific data store.
    
    This is primarily a debugging tool to get a complete overview of the contents
    of a specific database (e.g., view all of an NPC's memories). Parameters are
    passed via the URL query string.
    """
    return data_manager.get_all_entries(
        store_type=store_type, save_id=save_id, npc_id=npc_id, limit=limit
    )