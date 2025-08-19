"""
Custom Memory Module for Safi AI Bot

This module handles loading and saving custom user-specific memory data
like facts and jokes in a JSON file.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from constants import MEMORY_FILE

async def load_custom_memory() -> Dict[str, Any]:
    """
    Load custom memory data from the JSON file.

    Returns:
        Dict: The loaded custom memory data, or an empty structure if the file doesn't exist
    """
    try:
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"facts": {}, "jokes": {}}
    except Exception as e:
        logging.error(f"Error loading custom memory: {str(e)}")
        return {"facts": {}, "jokes": {}}

async def save_custom_memory(data: Dict[str, Any]) -> None:
    """
    Save custom memory data to the JSON file.

    Args:
        data: The custom memory data to save
    """
    try:
        # Ensure the directory exists
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving custom memory: {str(e)}")
        raise