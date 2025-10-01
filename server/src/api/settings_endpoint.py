# src/api/settings_endpoint.py
from fastapi import APIRouter, Depends, Request
from src.schemas.settings import GameSettings
from src.core.settings_manager import SettingsManager
import logging # <-- ADDED IMPORT

log = logging.getLogger(__name__) # <-- ADDED LOGGER
router = APIRouter()

# Dependency function to get the settings manager instance
def get_settings_manager(request: Request) -> SettingsManager:
    return request.app.state.settings_manager

@router.get("/settings", response_model=GameSettings, tags=["Settings"])
async def get_current_settings(
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """
    Retrieve the current global game settings.

    This endpoint returns the configuration currently used by the server,
    such as the Ollama API endpoint and model names.
    """
    return settings_manager.get_settings()

@router.put("/settings", response_model=GameSettings, tags=["Settings"])
async def update_game_settings(
    new_settings: GameSettings,
    request: Request, # <-- ADDED request OBJECT
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """
    Update the global game settings and re-initialize services live.

    This endpoint overwrites the settings file and immediately creates a new
    LLMService instance with the updated model names. Changes to chat_model
    and embedding_model take effect instantly for all subsequent requests.

    **Note:** Changing `ollama_host` may still require a server restart
    to be fully effective.
    """
    # 1. Save the new settings to the settings.json file
    settings_manager.update_settings(new_settings)
    
    # 2. Re-initialize the LLM service with the new settings LIVE
    log.info("Settings updated. Re-initializing LLMService with new configuration...")
    

    log.info(f"LLMService successfully re-initialized with chat model '{new_settings.chat_model}'.")
    
    # 3. Return the updated settings to the client
    return new_settings