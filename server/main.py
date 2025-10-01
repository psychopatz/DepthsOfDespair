# server/main.py
from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager

from src import config
from src.core.settings_manager import SettingsManager
from src.core.llm_service import LLMService
from src.core.memory_manager import MemoryManager  # <-- 1. IMPORT MemoryManager
from src.api import settings_endpoint, ollama_endpoint, memory_endpoint

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("--- Server Starting ---")
    
    # Settings Manager (already exists)
    settings_manager = SettingsManager(config.SETTINGS_FILE_PATH)
    app.state.settings_manager = settings_manager
    current_settings = settings_manager.get_settings()
    
    # LLM Service (already exists)
    llm_service = LLMService(
        ollama_host=current_settings.ollama_host,
        chat_model=current_settings.chat_model,
        embedding_model=current_settings.embedding_model
    )
    app.state.llm_service = llm_service

    # --- 2. CREATE the MemoryManager instance ---
    memory_manager = MemoryManager(
        llm_service=llm_service,
        base_data_path=config.BASE_GAME_DATA_PATH
    )
    app.state.memory_manager = memory_manager # <-- 3. STORE it in the app's state

    print(f"Data Path: {config.BASE_GAME_DATA_PATH}")
    print(f"Ollama Host: {current_settings.ollama_host}")
    print("Memory Manager Initialized.") # <-- 4. Add a confirmation message
    print("----------------------")
    yield
    # --- Shutdown ---
    print("--- Server Shutting Down ---")

app = FastAPI(title="Depths of Despair - LLM NPC Server", lifespan=lifespan)

# --- API Routers ---
app.include_router(settings_endpoint.router)
app.include_router(ollama_endpoint.router)
app.include_router(memory_endpoint.router) 
