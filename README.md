# AI Bot

A Discord bot with AI capabilities for conversation, memory, and customization.

## Features

- AI-powered conversation using Mistral AI
- Custom facts and jokes storage per user
- Conversation history and context
- Slash commands for managing bot behavior
- Customizable system prompt

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sennvacan/discord-mistral-chatbot
   cd discord-mistral-chatbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration**:
   - Copy `config.sample.json` to `config.json`
   - Edit `config.json` with your actual credentials:
     - Mistral API key (get from [Mistral AI](https://mistral.ai/))
     - Discord bot token (create a bot at [Discord Developer Portal](https://discord.com/developers/applications))
     - Your server/guild ID
     - Your user ID (for allowed users)

4. **Run the bot**:
   ```bash
   python main.py
   ```

## Configuration

The bot uses a JSON configuration file (`config.json`). Here's what each section does:

- `credentials`: API keys and tokens
- `bot`: Bot behavior and Discord-specific settings
- `database`: Database file locations and limits
- `ai`: AI model settings and limits
- `memory`: Memory and customization limits
- `logging`: Logging settings

## Usage

Once running, the bot will respond to:
- Mentions of the bot
- Messages containing "BOT"S NAME THAT YOU SET" (case insensitive)
- Slash commands for managing facts, jokes, and system prompt

## Slash Commands

- `/system_prompt` - View or edit the bot's system prompt
- `/add_fact` - Add facts about a user
- `/remove_fact` - Remove facts about a user
- `/show_fact` - Show all facts about a user
- `/add_joke` - Add jokes/roasts for a user
- `/remove_joke` - Remove jokes/roasts for a user
- `/show_joke` - Show all jokes/roasts for a user

## Customization

You can customize:
- The system prompt in `system_prompt.json`
- Memory limits in `config.json`
- AI model and behavior in `config.json`




