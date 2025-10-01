# server/main.py
from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager

from src import config
from src.core.settings_manager import SettingsManager
from src.core.llm_service import LLMService  # <-- IMPORT LLMService
from src.api import settings_endpoint, ollama_endpoint # <-- IMPORT new router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("--- Server Starting ---")
    settings_manager = SettingsManager(config.SETTINGS_FILE_PATH)
    app.state.settings_manager = settings_manager
    current_settings = settings_manager.get_settings()
    
    # Create the LLMService instance and store it in the app's state
    app.state.llm_service = LLMService(
        ollama_host=current_settings.ollama_host,
        chat_model=current_settings.chat_model,
        embedding_model=current_settings.embedding_model
    )

    print(f"Data Path: {config.BASE_GAME_DATA_PATH}")
    print(f"Ollama Host: {current_settings.ollama_host}")
    print("----------------------")
    yield
    # --- Shutdown ---
    print("--- Server Shutting Down ---")

app = FastAPI(title="Depths of Despair - LLM NPC Server", lifespan=lifespan)

# --- API Routers ---
app.include_router(settings_endpoint.router)
app.include_router(ollama_endpoint.router) # <-- INCLUDE new router