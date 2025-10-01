# src/config.py
import os
from pathlib import Path

def get_user_documents_folder() -> Path:
    """
    Finds the correct "Documents" folder on any OS.

    On Windows, this queries the system registry to find the true location,
    even if the user has moved it to another drive (e.g., D:\).
    On macOS and Linux, it defaults to the standard '~/Documents'.
    """
    # Check if the OS is Windows
    if os.name == 'nt':
        try:
            # Import necessary modules for Windows API calls
            import ctypes
            from ctypes import wintypes

            # Define constants and function signatures from the Windows API
            CSIDL_PERSONAL = 5       # My Documents folder identifier
            SHGFP_TYPE_CURRENT = 0   # Get the folder's current path

            # Create a buffer to hold the path string
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            
            # Call the Windows Shell API function to get the folder path
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)

            # If the call succeeded, the buffer will contain the path
            if buf.value:
                return Path(buf.value)
        except (ImportError, OSError):
            # Fallback if ctypes fails or is in an unsupported environment
            # This will use the default user home directory
            pass

    # For non-Windows OS (macOS, Linux) or as a fallback on Windows,
    # use the standard home directory approach.
    return Path.home() / "Documents"


# --- PATH DEFINITIONS ---

# Get the correct, user-configured "Documents" folder path
_documents_path = get_user_documents_folder()

# This is now a robust, cross-platform way to get to the user's Documents folder
# and create the main directory for our game's user-facing data.
BASE_GAME_DATA_PATH = _documents_path / "My Games" / "DepthsOfDespair"

# Path to the global settings file
SETTINGS_FILE_PATH = BASE_GAME_DATA_PATH / "settings.json"

# Base path for all save slots
BASE_SAVES_PATH = BASE_GAME_DATA_PATH / "saves"