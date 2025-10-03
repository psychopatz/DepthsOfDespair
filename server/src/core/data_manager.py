import uuid
import json
import chromadb
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.schemas.enums import DataStoreType
from src.schemas.memory import Memory

class DataManager:
    def __init__(self, base_data_path: Path):
        self.base_data_path = base_data_path
        self._collection_cache: Dict[str, chromadb.Collection] = {}

    def _get_db_path(self, store_type: DataStoreType, save_id: str, npc_id: Optional[str] = None) -> Path:
        save_path = self.base_data_path / "saves" / save_id
        if store_type.name.startswith("WORLD_"):
            return save_path / "world_db" / store_type.value
        elif store_type.name.startswith("NPC_"):
            if not npc_id:
                raise ValueError(f"npc_id is required for DataStoreType '{store_type.name}'")
            return save_path / "npcs" / npc_id / store_type.value
        raise ValueError(f"Unknown DataStoreType: {store_type}")

    def _get_or_create_collection(self, store_type: DataStoreType, save_id: str, npc_id: Optional[str] = None) -> chromadb.Collection:
        db_path = self._get_db_path(store_type, save_id, npc_id)
        cache_key = str(db_path)
        if cache_key in self._collection_cache:
            return self._collection_cache[cache_key]
        db_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_or_create_collection(name="entries")
        self._collection_cache[cache_key] = collection
        print(f"INFO: Loaded or created collection for '{store_type.name}' at '{db_path}'.")
        return collection

    def _build_where_clause(self, filter_metadata: Optional[dict], time_from_tick: Optional[int], time_to_tick: Optional[int]) -> Optional[dict]:
        filters = []
        if filter_metadata:
            for key, value in filter_metadata.items():
                filters.append({key: {"$eq": value}})
        if time_from_tick is not None:
            filters.append({"game_tick": {"$gte": time_from_tick}})
        if time_to_tick is not None:
            filters.append({"game_tick": {"$lte": time_to_tick}})
        if not filters: return None
        if len(filters) == 1: return filters[0]
        return {"$and": filters}
        
    def add_entry(self, store_type: DataStoreType, save_id: str, text: str, embedding: List[float], metadata: dict, npc_id: Optional[str] = None) -> str:
        collection = self._get_or_create_collection(store_type, save_id, npc_id)
        entry_id = str(uuid.uuid4())
        metadata['entry_id'] = entry_id
        sanitized_metadata = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in metadata.items()}
        collection.add(embeddings=[embedding], documents=[text], metadatas=[sanitized_metadata], ids=[entry_id])
        return entry_id

    def delete_entry(self, store_type: DataStoreType, save_id: str, entry_id: str, npc_id: Optional[str] = None) -> bool:
        """
        Deletes an entry and returns True only if the entry actually existed and was deleted.
        """
        try:
            collection = self._get_or_create_collection(store_type, save_id, npc_id)
            
            existing_entry = collection.get(ids=[entry_id])
            if not existing_entry or not existing_entry['ids']:
                return False
                
            collection.delete(ids=[entry_id])
            return True
        except Exception as e:
            print(f"ERROR during delete_entry: {e}")
            return False

    def update_entry(self, store_type: DataStoreType, save_id: str, entry_id: str, new_text: str, new_embedding: List[float], new_metadata: dict, npc_id: Optional[str] = None) -> Optional[str]:
        """
        Updates an entry by performing a delete-then-add operation.

        Returns:
            - The new entry's ID (str) if the original entry was found and replaced.
            - None if the original entry_id did not exist.
        """
        was_deleted = self.delete_entry(store_type, save_id, entry_id, npc_id)

        if not was_deleted:
            return None

        return self.add_entry(
            store_type=store_type, save_id=save_id, text=new_text,
            embedding=new_embedding, metadata=new_metadata, npc_id=npc_id
        )

    def retrieve_entries(self, store_type: DataStoreType, save_id: str, query_embedding: List[float], n_results: int, filter_metadata: Optional[dict] = None, npc_id: Optional[str] = None, time_from_tick: Optional[int] = None, time_to_tick: Optional[int] = None) -> List[Memory]:
        collection = self._get_or_create_collection(store_type, save_id, npc_id)
        where_clause = self._build_where_clause(filter_metadata, time_from_tick, time_to_tick)
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results, where=where_clause, include=["metadatas", "documents", "distances"])
        
        retrieved_entries: List[Memory] = []
        if not results: return retrieved_entries
        ids_list, docs_list, metas_list, dists_list = results.get('ids'), results.get('documents'), results.get('metadatas'), results.get('distances')
        if ids_list and docs_list and metas_list and dists_list:
            ids, docs, metas, dists = ids_list[0], docs_list[0], metas_list[0], dists_list[0]
            for i, doc_id in enumerate(ids):
                if i < len(docs) and i < len(metas) and i < len(dists):
                    retrieved_entries.append(Memory(id=doc_id, text=docs[i], metadata=dict(metas[i]), distance=dists[i]))
        return retrieved_entries

    def search_entries(self, store_type: DataStoreType, save_id: str, filter_metadata: Optional[dict], limit: int, npc_id: Optional[str] = None, time_from_tick: Optional[int] = None, time_to_tick: Optional[int] = None) -> List[Memory]:
        collection = self._get_or_create_collection(store_type, save_id, npc_id)
        where_clause = self._build_where_clause(filter_metadata, time_from_tick, time_to_tick)
        results = collection.get(where=where_clause, limit=limit, include=["metadatas", "documents"])
        
        found_entries: List[Memory] = []
        if not results: return found_entries
        ids, docs, metas = results.get('ids'), results.get('documents'), results.get('metadatas')
        if ids and docs and metas:
            for i, doc_id in enumerate(ids):
                if i < len(docs) and i < len(metas):
                    found_entries.append(Memory(id=doc_id, text=docs[i], metadata=dict(metas[i]), distance=None))
        return found_entries

    def get_all_entries(self, store_type: DataStoreType, save_id: str, limit: int, npc_id: Optional[str] = None) -> List[Memory]:
        collection = self._get_or_create_collection(store_type, save_id, npc_id)
        results = collection.get(limit=limit, include=["metadatas", "documents"])
        all_entries: List[Memory] = []
        if not results: return all_entries
        ids, docs, metas = results.get('ids'), results.get('documents'), results.get('metadatas')
        if ids and docs and metas:
            for i, doc_id in enumerate(ids):
                if i < len(docs) and i < len(metas):
                    all_entries.append(Memory(id=doc_id, text=docs[i], metadata=dict(metas[i]), distance=None))
        return all_entries