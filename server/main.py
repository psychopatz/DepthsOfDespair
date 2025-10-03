# ==============================================================================
# main.py
#
# This is the main entry point for the FastAPI server application.
# It sets up all necessary services and includes the API routers during startup.
# ==============================================================================

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

# --- Core Application Imports ---
from src import config
from src.core.settings_manager import SettingsManager
from src.core.llm_service import LLMService
# MODIFIED: Import the new generic DataManager instead of the old MemoryManager
from src.core.data_manager import DataManager

# --- API Router Imports ---
# MODIFIED: Import the new datastore_endpoint instead of the old memory_endpoint
from src.api import settings_endpoint, ollama_endpoint, datastore_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the server's startup and shutdown events.
    This is the modern replacement for @app.on_event("startup") in FastAPI.
    All long-lived objects (like service managers) are created here.
    """
    # --- Startup ---
    print("--- Server Starting ---")
    
    # 1. Initialize the Settings Manager to handle settings.json
    settings_manager = SettingsManager(config.SETTINGS_FILE_PATH)
    app.state.settings_manager = settings_manager
    current_settings = settings_manager.get_settings()
    
    # 2. Initialize the LLM Service to handle all communication with Ollama
    llm_service = LLMService(
        ollama_host=current_settings.ollama_host,
        chat_model=current_settings.chat_model,
        embedding_model=current_settings.embedding_model
    )
    # Store the instance in the app's state so endpoints can access it
    app.state.llm_service = llm_service

    # 3. MODIFIED: Initialize the new generic DataManager
    # Note: The DataManager itself doesn't need the llm_service. Embeddings are
    # created at the endpoint layer before being passed to the manager.
    data_manager = DataManager(
        base_data_path=config.BASE_GAME_DATA_PATH
    )
    # Store the instance in the app's state
    app.state.data_manager = data_manager

    # --- Startup Logging ---
    print(f"Data Path: {config.BASE_GAME_DATA_PATH}")
    print(f"Ollama Host: {current_settings.ollama_host}")
    print("Data Manager Initialized.")
    print("----------------------")
    
    yield # The server runs while the lifespan is yielded
    
    # --- Shutdown ---
    print("--- Server Shutting Down ---")


# Create the main FastAPI application instance
app = FastAPI(title="Depths of Despair - LLM NPC Server", lifespan=lifespan)

# --- Include API Routers ---
# This makes the endpoints defined in other files available to the application.
app.include_router(settings_endpoint.router)
app.include_router(ollama_endpoint.router)
# MODIFIED: Include the new datastore_endpoint router
app.include_router(datastore_endpoint.router)