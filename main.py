"""
Safi AI Bot - Main Application File

This file contains the main bot implementation, command handlers,
and message processing logic for the Safi AI Discord bot.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import nextcord
from mistralai import Mistral
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from constants import (
    ALLOWED_USER_IDS,
    BOT_PREFIX,
    DEFAULT_MODEL,
    GUILD_ID,
    MAX_CONVERSATION_HISTORY,
    MAX_FACTS_PER_USER,
    MAX_JOKES_PER_USER,
    MAX_PROMPT_SIZE,
    MAX_RESPONSE_LENGTH,
    PROMPT_FILE
)
from custom_memory import load_custom_memory, save_custom_memory
from database import add_message, close_db, get_last_messages, init_db

# --- Initialize Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# --- Bot Setup ---
intents = nextcord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents,
    help_command=None
)

# --- Initialize Services ---
# Note: For the public version, we need to handle missing credentials gracefully
try:
    from constants import MISTRAL_API_KEY, DISCORD_BOT_TOKEN
    mistral = Mistral(MISTRAL_API_KEY)
except ImportError:
    # If credentials aren't available in constants (public version)
    logging.warning("Credentials not available in constants.py. Using placeholder values.")
    mistral = None
    DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

# --- Owner allowed --

# --- System Prompt Management ---
def load_system_prompt() -> str:
    """
    Load the system prompt from the configured prompt file.

    Returns:
        str: The system prompt text, or a default prompt if the file doesn't exist
    """
    try:
        if os.path.exists(PROMPT_FILE):
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("prompt", "")
        return "Your name is Kattar peshawri Marwat Pashtun. You're from Peshawar, Pakistan. You're a Pathan. Don't use emojis much. Be mysterious and talk in Urdu and Pashto."
    except Exception as e:
        logging.error(f"Error loading system prompt: {str(e)}")
        return "Your name is Kattar peshawri Marwat Pashtun. You're from Peshawar, Pakistan. You're a Pathan. Don't use emojis much. Be mysterious and talk in Urdu and Pashto."

def save_system_prompt(prompt: str) -> None:
    """
    Save the system prompt to the configured prompt file.

    Args:
        prompt (str): The system prompt text to save
    """
    try:
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            json.dump({"prompt": prompt}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving system prompt: {str(e)}")
        raise

# Load the initial system prompt
system_prompt = load_system_prompt()

# --- Slash Command to View/Edit System Prompt ---
@client.slash_command(
    name="system_prompt",
    description="View or edit the bot's system prompt (owner + allowed users)"
)
async def system_prompt_cmd(
    interaction: Interaction,
    new_prompt: str = SlashOption(
        description="Provide new system prompt to update (leave empty to just view)",
        required=False
    )
) -> None:
    """
    Slash command to view or edit the bot's system prompt.

    Args:
        interaction: Discord interaction object
        new_prompt: Optional new prompt text. If not provided, shows current prompt.
    """
    # Defer response to give us more time for processing
    await interaction.response.defer(ephemeral=True)

    # Check permissions
    if not owner_or_allowed(interaction):
        await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
        return

    # Update system prompt if new prompt provided
    global system_prompt
    if new_prompt:
        try:
            save_system_prompt(new_prompt)
            system_prompt = new_prompt
            logging.info(f"System prompt updated by user {interaction.user}")
            await interaction.followup.send("✅ System prompt updated successfully.", ephemeral=True)
        except Exception as e:
            logging.error(f"Error updating system prompt: {str(e)}")
            await interaction.followup.send(f"❌ Error updating system prompt: {str(e)}", ephemeral=True)
    else:
        # Show current system prompt
        try:
            # Limit the displayed prompt to avoid Discord message size limits
            display_prompt = system_prompt if len(system_prompt) <= 1800 else system_prompt[:1797] + "..."
            await interaction.followup.send(
                f"📄 Current system prompt:\n```\n{display_prompt}\n```",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Error retrieving system prompt: {str(e)}")
            await interaction.followup.send(f"❌ Error retrieving system prompt: {str(e)}", ephemeral=True)

# --- Slash Commands for Facts/Jokes ---
def owner_or_allowed(interaction: Interaction) -> bool:
    """
    Check if the user is the server owner or in the allowed users list.

    Args:
        interaction: Discord interaction object

    Returns:
        bool: True if user is owner or allowed, False otherwise
    """
    # Handle case when guild is None (DMs) or interaction.user is None
    if interaction.guild is None or interaction.user is None:
        return False

    # Handle case when guild.owner is None
    if interaction.guild.owner is None:
        return False

    # Check if user is server owner or in allowed users list
    try:
        user_id = interaction.user.id
        owner_id = interaction.guild.owner.id
        return user_id == owner_id or user_id in ALLOWED_USER_IDS
    except (AttributeError, TypeError):
        return False

async def modify_list(
    interaction: Interaction,
    member: nextcord.Member,
    text: str,
    category: str,
    action: str = "add"
) -> None:
    """
    Modify a list of items (facts or jokes) for a user in the custom memory.

    Args:
        interaction: Discord interaction object
        member: The member to modify items for
        text: Comma-separated items to add or remove
        category: The category to modify ('facts' or 'jokes')
        action: Action to perform ('add' or 'remove')

    Raises:
        ValueError: If an invalid action is provided
    """
    # Check permissions
    if not owner_or_allowed(interaction):
        await interaction.response.send_message("❌ Only server owner can use this.", ephemeral=True)
        return

    # Load and prepare data
    data = await load_custom_memory()
    uid = str(member.id)
    data.setdefault(category, {})
    data[category].setdefault(uid, [])

    # Process input items
    items = [x.strip() for x in text.split(",") if x.strip()]
    modified = []

    # Perform the requested action
    if action == "add":
        for x in items:
            if x not in data[category][uid]:
                data[category][uid].append(x)
                modified.append(x)

        if modified:
            logging.info(f"{action.upper()} {len(modified)} {category} for {member.display_name}")
            await interaction.response.send_message(
                f"✅ Added {category} for {member.display_name}: {', '.join(modified)}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ All {category} already exist.",
                ephemeral=True
            )

    elif action == "remove":
        for x in items:
            if x in data[category][uid]:
                data[category][uid].remove(x)
                modified.append(x)

        if modified:
            logging.info(f"{action.upper()} {len(modified)} {category} for {member.display_name}")
            await interaction.response.send_message(
                f"✅ Removed {category} for {member.display_name}: {', '.join(modified)}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ None of the specified {category} were found.",
                ephemeral=True
            )
    else:
        raise ValueError(f"Invalid action: {action}. Must be 'add' or 'remove'")

    # Save the updated data
    await save_custom_memory(data)

@client.slash_command(name="add_fact", description="Add fact(s) for a user")
async def add_fact(interaction: Interaction, member: nextcord.Member = SlashOption(description="Member"), fact: str = SlashOption(description="Comma-separated facts")):
    await modify_list(interaction, member, fact, "facts", action="add")

@client.slash_command(name="remove_fact", description="Remove fact(s) for a user (use fact numbers from show_fact or type the fact text)")
async def remove_fact(interaction: Interaction,
                     member: nextcord.Member = SlashOption(description="Member"),
                     fact: str = SlashOption(description="Comma-separated fact numbers or text to remove")):
    # Check if the input contains numbers (like "1,2,3") or text
    data = await load_custom_memory()
    uid = str(member.id)
    facts_list = data.get("facts", {}).get(uid, [])

    if not facts_list:
        await interaction.response.send_message(
            f"ℹ️ No facts found for {member.display_name}.",
            ephemeral=True
        )
        return

    # Check if input contains only numbers
    items = [x.strip() for x in fact.split(",") if x.strip()]
    is_numeric = all(item.isdigit() for item in items)

    if is_numeric:
        # Convert numbers to actual fact texts
        fact_texts = []
        for num_str in items:
            num = int(num_str) - 1  # Convert to 0-based index
            if 0 <= num < len(facts_list):
                fact_texts.append(facts_list[num])

        if fact_texts:
            # Join with commas for the modify_list function
            await modify_list(interaction, member, ", ".join(fact_texts), "facts", action="remove")
        else:
            await interaction.response.send_message(
                f"⚠️ No valid fact numbers found for {member.display_name}.",
                ephemeral=True
            )
    else:
        # Original behavior - treat as text
        await modify_list(interaction, member, fact, "facts", action="remove")

@client.slash_command(name="add_joke", description="Add joke(s) for a user")
async def add_joke(interaction: Interaction, member: nextcord.Member = SlashOption(description="Member"), joke: str = SlashOption(description="Comma-separated jokes")):
    await modify_list(interaction, member, joke, "jokes", action="add")

@client.slash_command(name="remove_joke", description="Remove joke(s) for a user (use joke numbers from show_joke or type the joke text)")
async def remove_joke(interaction: Interaction,
                     member: nextcord.Member = SlashOption(description="Member"),
                     joke: str = SlashOption(description="Comma-separated joke numbers or text to remove")):
    # Check if the input contains numbers (like "1,2,3") or text
    data = await load_custom_memory()
    uid = str(member.id)
    jokes_list = data.get("jokes", {}).get(uid, [])

    if not jokes_list:
        await interaction.response.send_message(
            f"ℹ️ No jokes found for {member.display_name}.",
            ephemeral=True
        )
        return

    # Check if input contains only numbers
    items = [x.strip() for x in joke.split(",") if x.strip()]
    is_numeric = all(item.isdigit() for item in items)

    if is_numeric:
        # Convert numbers to actual joke texts
        joke_texts = []
        for num_str in items:
            num = int(num_str) - 1  # Convert to 0-based index
            if 0 <= num < len(jokes_list):
                joke_texts.append(jokes_list[num])

        if joke_texts:
            # Join with commas for the modify_list function
            await modify_list(interaction, member, ", ".join(joke_texts), "jokes", action="remove")
        else:
            await interaction.response.send_message(
                f"⚠️ No valid joke numbers found for {member.display_name}.",
                ephemeral=True
            )
    else:
        # Original behavior - treat as text
        await modify_list(interaction, member, joke, "jokes", action="remove")

@client.slash_command(name="show_fact", description="Show facts for a user")
async def show_fact(
    interaction: Interaction,
    member: nextcord.Member = SlashOption(description="Member")
) -> None:
    """
    Display all facts stored for a specific user.

    Args:
        interaction: Discord interaction object
        member: The member to show facts for
    """
    # Check permissions
    if not owner_or_allowed(interaction):
        await interaction.response.send_message("❌ Only server owner can use this.", ephemeral=True)
        return

    # Load facts for the specified user
    data = await load_custom_memory()
    uid = str(member.id)
    facts = data.get("facts", {}).get(uid, [])

    if facts:
        # Create a numbered list of facts
        numbered_facts = "\n".join(f"{i+1}. {fact}" for i, fact in enumerate(facts))
        logging.info(f"Showing {len(facts)} facts for {member.display_name}")

        # Limit the number of facts shown to avoid message size limits
        display_facts = numbered_facts
        if len(display_facts) > 1800:
            display_facts = display_facts[:1797] + "\n..."

        await interaction.response.send_message(
            f"📝 Facts for {member.display_name}:\n{display_facts}\n\n"
            f"To remove a fact, use `/remove_fact {member.display_name} <number>`",
            ephemeral=True
        )
    else:
        logging.info(f"No facts found for {member.display_name}")
        await interaction.response.send_message(
            f"ℹ️ No facts found for {member.display_name}.",
            ephemeral=True
        )

@client.slash_command(name="show_joke", description="Show jokes for a user")
async def show_joke(
    interaction: Interaction,
    member: nextcord.Member = SlashOption(description="Member")
) -> None:
    """
    Display all jokes stored for a specific user.

    Args:
        interaction: Discord interaction object
        member: The member to show jokes for
    """
    # Check permissions
    if not owner_or_allowed(interaction):
        await interaction.response.send_message("❌ Only server owner can use this.", ephemeral=True)
        return

    # Load jokes for the specified user
    data = await load_custom_memory()
    uid = str(member.id)
    jokes = data.get("jokes", {}).get(uid, [])

    if jokes:
        # Create a numbered list of jokes
        numbered_jokes = "\n".join(f"{i+1}. {joke}" for i, joke in enumerate(jokes))
        logging.info(f"Showing {len(jokes)} jokes for {member.display_name}")

        # Limit the number of jokes shown to avoid message size limits
        display_jokes = numbered_jokes
        if len(display_jokes) > 1800:
            display_jokes = display_jokes[:1797] + "\n..."

        await interaction.response.send_message(
            f"😄 Jokes for {member.display_name}:\n{display_jokes}\n\n"
            f"To remove a joke, use `/remove_joke {member.display_name} <number>`",
            ephemeral=True
        )
    else:
        logging.info(f"No jokes found for {member.display_name}")
        await interaction.response.send_message(
            f"ℹ️ No jokes found for {member.display_name}.",
            ephemeral=True
        )

# --- Message Event Handler ---
@client.event
async def on_message(message: nextcord.Message) -> None:
    """
    Handle incoming messages and generate AI responses when appropriate.

    Args:
        message: The Discord message object
    """
    if message.author.bot or not message.guild:
        return

    # Store message in DB with message ID and reference ID
    message_id = str(message.id)
    reference_id = str(message.reference.message_id) if message.reference and hasattr(message.reference, 'message_id') else None
    await add_message(str(message.channel.id), str(message.author.id), message.content, message_id, reference_id)

    # Trigger only if bot mentioned or keyword
    if not client.user or not client.user.mentioned_in(message) and "marwat" not in message.content.lower():
        return

    # Replace mentions for readability
    if not client.user:
        return

    bot_id = client.user.id
    content = message.content
    for user in message.mentions:
        if user.id != bot_id:
            content = content.replace(f"<@{user.id}>", user.display_name)
            content = content.replace(f"<@!{user.id}>", user.display_name)
    content = content.replace(f"<@{bot_id}>", "").strip()

    # Handle replies
    replied_text = ""
    replied_author = ""
    if message.reference and isinstance(message.reference.resolved, nextcord.Message):
        replied = message.reference.resolved
        replied_author = replied.author.display_name if replied.author else "Unknown"
        replied_text = replied.content if replied.content else "[No text]"

    # Load conversation history from database
    last_messages = await get_last_messages(str(message.channel.id), limit=MAX_CONVERSATION_HISTORY)
    memory_text = ""

    # Process messages and their replies
    for row in last_messages:
        uid, msg, msg_id, ref_id = row[:4]  # Unpack with safety for older DB records

        # Get user display name
        member = message.guild.get_member(int(uid)) if message.guild else None
        name = member.display_name if member else f"User{uid[-4:]}"

        # Add the message
        memory_text += f"{name}: {msg}\n"

        # If this message is a reply to another message
        if ref_id:
            # In a real implementation, we would look up the referenced message
            # For now, we'll just note that it's a reply
            memory_text += f"  (This was a reply to another message: {ref_id})\n"

    # Always load custom memory for context
    custom = await load_custom_memory()
    relevant_uids = {str(message.author.id)}

    # Include mentioned users
    if message.mentions:
        relevant_uids.update(str(user.id) for user in message.mentions)

    # Include replied-to user if this is a reply
    if message.reference and isinstance(message.reference.resolved, nextcord.Message):
        relevant_uids.add(str(message.reference.resolved.author.id))

    # Include facts and jokes per user according to configuration
    facts_list = []
    for uid, lst in custom.get("facts", {}).items():
        if uid in relevant_uids and lst:
            member = message.guild.get_member(int(uid)) if message.guild else None
            name = member.display_name if member else f"User{uid[-4:]}"
            # Include up to configured number of facts
            facts_list.append(f"{name}: {', '.join(lst[:MAX_FACTS_PER_USER])}")

    jokes_list = []
    for uid, lst in custom.get("jokes", {}).items():
        if uid in relevant_uids and lst:
            member = message.guild.get_member(int(uid)) if message.guild else None
            name = member.display_name if member else f"User{uid[-4:]}"
            # Include up to configured number of jokes
            jokes_list.append(f"{name}: {lst[0]}" + (f"; {lst[1]}" if len(lst) > 1 and len(lst) <= MAX_JOKES_PER_USER else ""))

    custom_info = ""
    if facts_list:
        custom_info += "\nFacts about users:\n" + "\n".join(facts_list)
    if jokes_list:
        custom_info += "\nCustom jokes/roasts:\n" + "\n".join(jokes_list)

    # Build simplified prompt for AI
    prompt_for_ai = f"""
STRICTLY FOLLOW THIS: {system_prompt[:500]}...

{custom_info}

Recent conversation:
{memory_text}

{message.author.display_name}: {message.content[:200]}"""

    # Include replied-to message if it exists and is relevant
    if replied_text and len(prompt_for_ai) < 1500:  # Only include if prompt isn't too long
        prompt_for_ai += f"\n\nReplied to: {replied_author}: {replied_text[:100]}"

    prompt_for_ai += "\n\nRespond concisely and naturally."

    # Send prompt to AI
    await message.channel.trigger_typing()

    try:
        import time
        start_time = time.time()
        print(f"[API CALL START] Sending request to Mistral AI...")

        # Check if we have a valid Mistral client
        if mistral is None:
            await message.reply("⚠️ Bot is running in demo mode. Please set up your config.json with actual API keys to enable full functionality.")
            return

        # Further optimize the prompt if it's too large
        if len(prompt_for_ai) > MAX_PROMPT_SIZE:
            print("[PROMPT OPTIMIZATION] Prompt too large, truncating...")
            # Keep only the most essential parts
            optimized_prompt = f"""
            STRICTLY FOLLOW THIS: {system_prompt[:200]}...

            Recent conversation:
            {message.author.display_name}: {message.content[:300]}

            Respond concisely as Kattar peshawri Marwat Pashtun.
            """
            prompt_to_use = optimized_prompt
        else:
            prompt_to_use = prompt_for_ai

        # Use the configured model
        response = mistral.chat.complete(
            model=DEFAULT_MODEL,
            messages=[{"role": "system", "content": prompt_to_use}]
        )

        end_time = time.time()
        api_latency = end_time - start_time
        print(f"[API CALL END] Received response in {api_latency:.2f} seconds")
        print(f"[PROMPT SIZE] {len(prompt_to_use)} characters")

        # Handle response safely
        try:
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    answer = str(choice.message.content)
                    # Basic string operations with safety checks
                    if isinstance(answer, str):
                        answer = answer.replace("Mistral AI", "Kattar peshawri Marwat Pashtun")
                        # Limit response length according to configuration
                        if len(answer) > MAX_RESPONSE_LENGTH:
                            answer = answer[:MAX_RESPONSE_LENGTH-3] + "..."
                    else:
                        answer = "Sorry, I had trouble processing that request."
                else:
                    answer = "Sorry, I had trouble processing that request."
            else:
                answer = "Sorry, I had trouble processing that request."
        except Exception as e:
            print(f"[RESPONSE ERROR] {str(e)}")
            answer = "Sorry, I had trouble processing that request."

    except Exception as e:
        answer = f"❌ Error: {str(e)}"
        print(f"[API ERROR] {str(e)}")

    await message.reply(answer[:2000])

@client.event
async def on_ready():
    """
    Event handler for when the bot is ready and connected to Discord.
    Initializes the database and syncs application commands.
    """
    await init_db()
    await client.sync_application_commands(guild_id=GUILD_ID)
    logging.info(f"Bot is ready! Logged in as {client.user}")

# Remove the on_disconnect event to prevent premature database closure
# The database will be closed when the program exits

# --- Run Bot ---
if __name__ == "__main__":
    try:
        logging.info("Starting Safi AI Bot...")

        # Check if we're using placeholder token
        if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE" or "REPLACE_" in str(DISCORD_BOT_TOKEN):
            logging.error("CRITICAL: Using placeholder token! Create config.json with your actual Discord bot token.")
            print("\n" + "="*60)
            print("IMPORTANT: You need to create a config.json file with")
            print("your actual Discord bot token and Mistral API key.")
            print("See config.sample.json for the required format.")
            print("="*60 + "\n")
        else:
            # Debug: Show the token being used (with redaction for security)
            token_preview = f"{str(DISCORD_BOT_TOKEN)[:10]}..." if DISCORD_BOT_TOKEN else "EMPTY"
            logging.warning(f"Attempting to authenticate with token: {token_preview}")

        client.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        logging.error(f"Failed to start bot: {str(e)}")
        raise