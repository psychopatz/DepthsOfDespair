# src/core/settings_manager.py
import json
from pathlib import Path
from src.schemas.settings import GameSettings # <-- UPDATED IMPORT
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self, settings_path: Path):
        self.settings_path = settings_path
        self.settings = self._load_or_create()

    def _load_or_create(self) -> GameSettings:
        """Loads settings from the file, or creates it with defaults if it doesn't exist."""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r') as f:
                    data = json.load(f)
                    log.info(f"Successfully loaded settings from {self.settings_path}")
                    return GameSettings(**data)
            else:
                log.warning(f"Settings file not found at {self.settings_path}. Creating with default values.")
                default_settings = GameSettings()
                self.save(default_settings)
                return default_settings
        except (json.JSONDecodeError, TypeError) as e:
            log.error(f"Error reading settings file: {e}. Using default settings.")
            return GameSettings()

    def save(self, settings: GameSettings):
        """Saves the current settings to the file."""
        try:
            # Ensure the parent directory exists
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_path, 'w') as f:
                # Use .model_dump_json for Pydantic v2, or .json() for v1
                f.write(settings.model_dump_json(indent=4))
            log.info(f"Settings saved to {self.settings_path}")
        except IOError as e:
            log.error(f"Could not write to settings file: {e}")

    def get_settings(self) -> GameSettings:
        """Returns the currently loaded settings."""
        return self.settings

    def update_settings(self, new_settings: GameSettings) -> GameSettings:
        """Updates the settings and saves them to the file."""
        self.settings = new_settings
        self.save(self.settings)
        return self.settings