# server/main.py
from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager

from src import config
from src.core.settings_manager import SettingsManager

from src.api import settings_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("--- Server Starting ---")
    settings_manager = SettingsManager(config.SETTINGS_FILE_PATH)
    app.state.settings_manager = settings_manager
    current_settings = settings_manager.get_settings()
    

    print(f"Data Path: {config.BASE_GAME_DATA_PATH}")
    print(f"Ollama Host: {current_settings.ollama_host}")
    print("----------------------")
    yield
    # --- Shutdown ---
    print("--- Server Shutting Down ---")

app = FastAPI(title="Depths of Despair - LLM NPC Server", lifespan=lifespan)



# --- API Routers ---
app.include_router(settings_endpoint.router)


# --- Root Endpoints ---
