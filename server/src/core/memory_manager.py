# ==============================================================================
# memory_manager.py
#
# This module contains the MemoryManager class, which is the core business logic
# for handling all interactions with the NPC memory database (ChromaDB).
#
# It follows the "Gatekeeper" principle: NO other part of the application
# should ever talk directly to ChromaDB. All operations must go through this
# manager. This ensures a clean separation of concerns and makes it easy to
# swap out the vector database in the future if needed.
# ==============================================================================

# --- Imports ---
import uuid
import json
import chromadb
from pathlib import Path
from typing import Dict, List, Optional, Any

# Dependencies from other parts of our application.
from src.core.llm_service import LLMService
from src.schemas.memory import Memory


# --- The Manager Class ---
class MemoryManager:
    """
    Manages the creation, retrieval, and deletion of NPC memories using ChromaDB.
    This class is the sole interface to the vector database.
    """

    def __init__(self, llm_service: LLMService, base_data_path: Path):
        """
        Initializes the MemoryManager.

        Args:
            llm_service: An instance of LLMService (Dependency Injection). This
                         manager uses the service to create embeddings but does not
                         manage its lifecycle.
            base_data_path: A Path object for the root of the game's data directory,
                            e.g., 'Documents/My Games/DepthsOfDespair/'.
        """
        self.llm_service = llm_service
        self.base_data_path = base_data_path
        # This cache is a critical performance optimization. It stores active
        # ChromaDB collection objects to avoid the overhead of reconnecting
        # to the same database files on disk for every single request.
        self._collection_cache: Dict[str, chromadb.Collection] = {}

    def _get_or_create_collection(self, save_id: str, npc_id: str) -> chromadb.Collection:
        """
        A private helper to get or create a ChromaDB collection for a specific NPC.
        This centralizes the logic for path management and caching.
        """
        # Create a unique key for the cache from the save and NPC IDs.
        collection_key = f"{save_id}_{npc_id}"
        if collection_key in self._collection_cache:
            return self._collection_cache[collection_key]

        # Construct the unique path for this NPC's memory database.
        # Using pathlib is OS-agnostic (handles '/' and '\' correctly).
        npc_memory_path = self.base_data_path / "saves" / save_id / "npcs" / npc_id / "memory_db"
        # This is a robust way to create the directory if it doesn't exist.
        npc_memory_path.mkdir(parents=True, exist_ok=True)
        
        # A PersistentClient saves the database to the specified file path.
        client = chromadb.PersistentClient(path=str(npc_memory_path))
        # Get the collection named "memories", or create it if it's the first time.
        collection = client.get_or_create_collection(name="memories")
        
        # Store the newly created collection object in the cache for future use.
        self._collection_cache[collection_key] = collection
        print(f"INFO: Loaded or created memory collection for NPC '{npc_id}' in save '{save_id}'.")
        return collection

    async def add_memory(self, save_id: str, npc_id: str, memory_text: str, metadata: dict) -> str:
        """
        Creates an embedding for memory text and stores it in the database.
        """
        collection = self._get_or_create_collection(save_id, npc_id)
        memory_id = str(uuid.uuid4())
        
        metadata['memory_id'] = memory_id
        
        # WORKAROUND: ChromaDB's metadata values must be primitive types. This
        # loop sanitizes the metadata by converting any lists or dicts into
        # JSON strings, making them storable.
        sanitized_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                sanitized_metadata[key] = json.dumps(value)
            else:
                sanitized_metadata[key] = value

        # Generate the vector embedding for the memory text.
        embedding_response = await self.llm_service.generate_embeddings(memory_text)
        embedding = embedding_response['embeddings'][0]

        # Add the complete memory (embedding, text, metadata, ID) to the collection.
        collection.add(embeddings=[embedding], documents=[memory_text], metadatas=[sanitized_metadata], ids=[memory_id])
        return memory_id

    async def retrieve_relevant_memories(self, save_id: str, npc_id: str, query_text: str, n_results: int, filter_metadata: Optional[dict] = None) -> List[Memory]:
        """
        Finds the N most relevant memories using semantic (vector) search.
        """
        collection = self._get_or_create_collection(save_id, npc_id)
        embedding_response = await self.llm_service.generate_embeddings(query_text)
        query_embedding = embedding_response['embeddings'][0]

        # This is the core vector search operation.
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results, where=filter_metadata, include=["metadatas", "documents", "distances"])

        retrieved_memories: List[Memory] = []
        if not results: return retrieved_memories

        # ROBUSTNESS: The following checks prevent crashes if ChromaDB returns
        # empty or malformed results, and they satisfy strict type-checkers.
        ids_list = results.get('ids')
        documents_list = results.get('documents')
        metadatas_list = results.get('metadatas')
        distances_list = results.get('distances')

        # The query result is a list of lists (one for each query). We only send one.
        if ids_list and documents_list and metadatas_list and distances_list:
            ids, documents, metadatas, distances = ids_list[0], documents_list[0], metadatas_list[0], distances_list[0]
            
            for i, doc_id in enumerate(ids):
                if i < len(documents) and i < len(metadatas) and i < len(distances):
                    # Convert Chroma's Mapping to a standard dict for Pydantic.
                    mem = Memory(id=doc_id, text=documents[i], metadata=dict(metadatas[i]), distance=distances[i])
                    retrieved_memories.append(mem)
        
        return retrieved_memories

    def delete_memory(self, save_id: str, npc_id: str, memory_id: str) -> bool:
        """Deletes a specific memory from the database by its unique ID."""
        try:
            collection = self._get_or_create_collection(save_id, npc_id)
            collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            # Gracefully handle potential errors during deletion.
            print(f"ERROR: Could not delete memory {memory_id}. Reason: {e}")
            return False

    def search_memories(self, save_id: str, npc_id: str, filter_metadata: dict, limit: int = 100) -> List[Memory]:
        """
        Searches memories using exact metadata filters (like an SQL 'WHERE' clause).
        """
        collection = self._get_or_create_collection(save_id, npc_id)
        # '.get()' is for direct filtering, not vector search.
        results = collection.get(where=filter_metadata, limit=limit, include=["metadatas", "documents"])

        found_memories: List[Memory] = []
        if not results: return found_memories

        # ROBUSTNESS: Same pattern as retrieve_relevant_memories for type safety.
        ids, documents, metadatas = results.get('ids'), results.get('documents'), results.get('metadatas')

        if ids and documents and metadatas:
            for i, doc_id in enumerate(ids):
                if i < len(documents) and i < len(metadatas):
                    # Be explicit that .get() does not return a distance.
                    mem = Memory(id=doc_id, text=documents[i], metadata=dict(metadatas[i]), distance=None)
                    found_memories.append(mem)
        
        return found_memories

    def get_all_memories(self, save_id: str, npc_id: str, limit: int = 1000) -> List[Memory]:
        """
        Retrieves all memories for a given NPC. Primarily for debugging.
        """
        collection = self._get_or_create_collection(save_id, npc_id)
        results = collection.get(limit=limit, include=["metadatas", "documents"])

        all_memories: List[Memory] = []
        if not results: return all_memories
        
        # ROBUSTNESS: Same pattern as search_memories for type safety.
        ids, documents, metadatas = results.get('ids'), results.get('documents'), results.get('metadatas')
        
        if ids and documents and metadatas:
            for i, doc_id in enumerate(ids):
                if i < len(documents) and i < len(metadatas):
                    # Be explicit that .get() does not return a distance.
                    mem = Memory(id=doc_id, text=documents[i], metadata=dict(metadatas[i]), distance=None)
                    all_memories.append(mem)
        
        return all_memories