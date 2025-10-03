from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from src.schemas.enums import DataStoreType

# --- CREATE ---
class AddEntryRequest(BaseModel):
    store_type: DataStoreType
    save_id: str = Field(..., examples=["save_slot_01"])
    npc_id: Optional[str] = Field(None, examples=["korgan_ironhand_a3f8"])
    text: str = Field(..., examples=["The player complimented my smithing work."])
    metadata: Dict[str, Any] = Field(..., examples=[{"type": "dialogue", "game_tick": 40321}])

class AddEntryResponse(BaseModel):
    new_entry_id: str

# --- READ (by Similarity) ---
class RetrieveEntriesRequest(BaseModel):
    store_type: DataStoreType = Field(..., examples=["memory_db"])
    save_id: str = Field(..., examples=["save_slot_01"])
    npc_id: Optional[str] = Field(None, examples=["korgan_ironhand_a3f8"])
    query_text: str = Field(..., examples=["Tell me about your family."])
    n_results: int = Field(5, ge=1, le=20)
    filter_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata to filter on *before* the similarity search.", examples=[{"type": "dialogue"}])
    time_from_tick: Optional[int] = Field(None, description="Optional game tick to filter entries created after this time.")
    time_to_tick: Optional[int] = Field(None, description="Optional game tick to filter entries created before this time.",examples=[40321])

# --- READ (by Filter) ---
class SearchEntriesRequest(BaseModel):
    store_type: DataStoreType  = Field(..., examples=["memory_db"])
    save_id: str = Field(..., examples=["save_slot_01"])
    npc_id: Optional[str] = Field(None, examples=["korgan_ironhand_a3f8"])
    filter_metadata: Optional[Dict[str, Any]] = Field(None, description="Key-value pairs to filter by.", examples=[{"type": "dialogue"}])
    limit: int = Field(100, ge=1, le=1000)
    time_from_tick: Optional[int] = Field(None, description="Optional game tick to filter entries created after this time.", examples=[40320])
    time_to_tick: Optional[int] = Field(None, description="Optional game tick to filter entries created before this time.", examples=[50000])

# --- DELETE / UPDATE ---
class DeleteEntryRequest(BaseModel):
    store_type: DataStoreType  = Field(..., examples=["memory_db"])
    save_id: str = Field(..., examples=["save_slot_01"])
    npc_id: Optional[str] = Field(None, examples=["korgan_ironhand_a3f8"])
    entry_id: str = Field(..., examples=["a1b2c3d4-e5f6-7890-1234-567890abcdef"])

class DeleteEntryResponse(BaseModel):
    status: str = Field("success")
    message: str

class UpdateEntryRequest(BaseModel):
    store_type: DataStoreType  = Field(..., examples=["memory_db"])
    save_id: str = Field(..., examples=["save_slot_01"])
    npc_id: Optional[str] = Field(None, examples=["korgan_ironhand_a3f8"])
    entry_id: str = Field(..., description="The ID of the existing entry to be replaced.", examples=["a1b2c3d4-e5f6-7890-1234-567890abcdef"])
    new_text: str = Field(..., description="The new natural language text for the entry.", examples=["The Sunstone is actually a petrified dragon's heart."])
    new_metadata: Dict[str, Any] = Field(..., description="The complete new set of metadata for the entry.", examples=[{"entry_name": "Sunstone", "type": "Artifact", "true_nature": "Dragon Heart"}])

class UpdateEntryResponse(BaseModel):
    new_entry_id: str = Field(..., description="The ID of the newly created entry that replaced the old one.")