"""
Constants Module for Safi AI Bot

This module contains shared constants and configuration values
used across the bot application.
"""

import json
import logging
from typing import Any, Dict

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json file.

    Note: For the public version, this will load the sample config.
    You need to create your own config.json with your actual credentials.
    """
    try:
        # First try to load the real config
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # If config.json doesn't exist, return a safe default config
        # This allows the code to run without exposing real credentials
        logging.warning("config.json not found, using safe defaults. Create config.json with your actual credentials.")
        return {
            "credentials": {
                "mistral_api_key": "YOUR_MISTRAL_API_KEY_HERE",
                "discord_bot_token": "YOUR_DISCORD_BOT_TOKEN_HERE"
            },
            "bot": {
                "allowed_user_ids": [123456789012345678],
                "guild_id": 123456789012345678,
                "command_prefix": "@",
                "system_prompt_file": "system_prompt.json",
                "default_model": "mistral-medium-2508"
            },
            "database": {
                "chat_memory_db": "chat_memory.db",
                "custom_memory_json": "custom_memory.json",
                "message_retention_limit": 100,
                "max_conversation_history": 7
            },
            "ai": {
                "max_prompt_size": 2000,
                "max_response_length": 1000,
                "default_typing_indicator": True,
                "response_style": "concise"
            },
            "memory": {
                "max_facts_per_user": 4,
                "max_jokes_per_user": 2,
                "memory_context_window": 7
            },
            "logging": {
                "enable_api_logging": True,
                "log_prompt_sizes": True,
                "log_response_times": True
            }
        }
    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")
        raise

# Load configuration
CONFIG = load_config()

# Bot Configuration
BOT_PREFIX = CONFIG["bot"]["command_prefix"]
GUILD_ID = CONFIG["bot"]["guild_id"]
ALLOWED_USER_IDS = CONFIG["bot"]["allowed_user_ids"]

# Database Configuration
from pathlib import Path

DB_FILE = Path(CONFIG["database"]["chat_memory_db"])
MEMORY_FILE = Path(CONFIG["database"]["custom_memory_json"])
MESSAGE_RETENTION_LIMIT = CONFIG["database"]["message_retention_limit"]
MAX_CONVERSATION_HISTORY = CONFIG["database"]["max_conversation_history"]

# AI Configuration
DEFAULT_MODEL = CONFIG["bot"]["default_model"]
MAX_PROMPT_SIZE = CONFIG["ai"]["max_prompt_size"]
MAX_RESPONSE_LENGTH = CONFIG["ai"]["max_response_length"]

# Memory Configuration
MAX_FACTS_PER_USER = CONFIG["memory"]["max_facts_per_user"]
MAX_JOKES_PER_USER = CONFIG["memory"]["max_jokes_per_user"]

# System Files
PROMPT_FILE = CONFIG["bot"]["system_prompt_file"]

# Note: Credentials are NOT exposed in this public version
# You need to set up your own config.json with your actual credentials
# MISTRAL_API_KEY = CONFIG["credentials"]["mistral_api_key"]  # Commented out for public version
# DISCORD_BOT_TOKEN = CONFIG["credentials"]["discord_bot_token"]  # Commented out for public version