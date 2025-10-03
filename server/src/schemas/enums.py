from enum import Enum

class DataStoreType(str, Enum):
    """
    Defines all possible vector database stores in the game world.
    This Enum is used to dynamically select the correct database path and context.
    
    The value of each member corresponds to the folder name on disk.
    """
    # World-level data stores (per-save)
    WORLD_LORE = "lore_db"
    WORLD_LEXICON = "lexicon_db"

    # NPC-level data stores (per-save, per-npc)
    NPC_FACTS = "fact_db"
    NPC_MEMORIES = "memory_db"
    NPC_QUEST_TRIGGERS = "quest_triggers_db"