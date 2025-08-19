# Safi AI Bot Configuration Guide

This document explains the configuration system for the Safi AI Discord bot.

## Overview

The bot uses a centralized configuration system based on a JSON file (`config.json`) that contains all sensitive credentials and configurable variables. This approach provides several benefits:

1. **Security**: Sensitive credentials are separated from the code
2. **Maintainability**: Configuration values can be changed without modifying code
3. **Organization**: All settings are in one place with clear structure

## Configuration File Structure

The `config.json` file is organized into logical sections:

```json
{
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
    "default_typing_indicator": true,
    "response_style": "concise"
  },

  "memory": {
    "max_facts_per_user": 4,
    "max_jokes_per_user": 2,
    "memory_context_window": 7
  },

  "logging": {
    "enable_api_logging": true,
    "log_prompt_sizes": true,
    "log_response_times": true
  }
}
```

## Configuration Sections

### 1. Credentials

This section contains sensitive information that should never be committed to version control:

- `mistral_api_key`: Your Mistral AI API key
- `discord_bot_token`: Your Discord bot token

### 2. Bot Configuration

General bot settings:

- `allowed_user_ids`: List of user IDs allowed to use admin commands
- `guild_id`: The Discord server ID where the bot operates
- `command_prefix`: The prefix for bot commands
- `system_prompt_file`: File containing the system prompt for the AI
- `default_model`: The default AI model to use

### 3. Database Configuration

Settings for database files and retention:

- `chat_memory_db`: Path to the SQLite database file
- `custom_memory_json`: Path to the JSON file for custom memory
- `message_retention_limit`: Maximum number of messages to retain per channel
- `max_conversation_history`: Maximum number of messages to include in conversation history

### 4. AI Settings

Configuration for AI behavior:

- `max_prompt_size`: Maximum size of the prompt sent to the AI
- `max_response_length`: Maximum length of AI responses
- `default_typing_indicator`: Whether to show typing indicators
- `response_style`: Style of AI responses ("concise", "detailed", etc.)

### 5. Memory Settings

Configuration for user memory:

- `max_facts_per_user`: Maximum number of facts to store per user
- `max_jokes_per_user`: Maximum number of jokes to store per user
- `memory_context_window`: Number of recent messages to include in memory context

### 6. Logging Settings

Configuration for logging:

- `enable_api_logging`: Whether to log API calls
- `log_prompt_sizes`: Whether to log prompt sizes
- `log_response_times`: Whether to log response times

## How to Modify Configuration

1. Copy `config.sample.json` to `config.json`
2. Open the `config.json` file in a text editor
3. Modify the values as needed, replacing all placeholder values with your actual credentials
4. Save the file
5. Restart the bot for changes to take effect

## Security Best Practices

1. Never commit the `config.json` file to version control
2. Add `config.json` to your `.gitignore` file
3. Use environment variables for production deployments
4. Keep API keys and tokens secure

## Constants Module

The bot uses a `constants.py` module that loads the configuration and exposes all values as Python constants. This module is imported by other modules to access configuration values.

## Troubleshooting

If you encounter issues with the configuration:

1. Verify the JSON syntax is valid
2. Check that all required fields are present
3. Ensure file permissions allow the bot to read the file
4. Check the bot logs for error messages