# src/api/settings_endpoint.py
from fastapi import APIRouter, Depends, Request
from src.schemas.settings import GameSettings
from src.core.settings_manager import SettingsManager
from src.core.llm_service import LLMService  # <-- ADD THIS IMPORT
import logging

log = logging.getLogger(__name__)
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
    """
    return settings_manager.get_settings()

@router.put("/settings", response_model=GameSettings, tags=["Settings"])
async def update_game_settings(
    new_settings: GameSettings,
    request: Request,  # <-- ADD request OBJECT DEPENDENCY
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """
    Update the global game settings and re-initialize services live.
    """
    # 1. Save the new settings to the settings.json file
    settings_manager.update_settings(new_settings)
    
    # 2. Re-initialize the LLM service with the new settings LIVE
    log.info("Settings updated. Re-initializing LLMService with new configuration...")
    
    # Create a new instance of the LLMService with the updated settings
    new_llm_service = LLMService(
        ollama_host=new_settings.ollama_host,
        chat_model=new_settings.chat_model,
        embedding_model=new_settings.embedding_model
    )
    
    # Replace the old service instance in the app's state with the new one
    request.app.state.llm_service = new_llm_service
    
    log.info(f"LLMService successfully re-initialized. New chat model: '{new_settings.chat_model}'.")
    
    # 3. Return the updated settings to the client
    return new_settings