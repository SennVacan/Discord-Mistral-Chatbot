from nextcord import Interaction, SlashOption
import nextcord
from nextcord.ext import commands
from mistralai import Mistral
import os
import json

# --- Bot Setup ---
intents = nextcord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = commands.Bot(
    command_prefix=commands.when_mentioned,
    intents=intents,
    help_command=None
)

async def on_ready():
    # This will sync slash commands to the guilds you specify
    # Faster for testing: use a specific guild ID
    guild_id = 1403534221838123179  # replace with your dev server ID
    await client.sync_application_commands(guild_id=guild_id)
    print(f"Bot is ready! Logged in as {client.user}")
# --- Services ---
mistral = Mistral("MISTRAL API KEY")

# --- Prompt Storage ---
PROMPT_FILE = "system_prompt.json"

def load_system_prompt():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("prompt", "")
    # Default prompt
    return "Your name is Kattar peshawri Marwat Pashtun. You're from Peshawar, Pakistan. You're a Pathan. don't use emojies mutch. be mysterious and talk in urdu and pustho"

def save_system_prompt(prompt: str):
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump({"prompt": prompt}, f, ensure_ascii=False, indent=2)

system_prompt = load_system_prompt()

# --- Commands to Edit Prompt ---
@client.slash_command(name="set_prompt", description="Update the system prompt")
async def set_prompt(interaction: Interaction, new_prompt: str = SlashOption(description="New prompt text")):
    global system_prompt
    system_prompt = new_prompt
    save_system_prompt(new_prompt)
    await interaction.response.send_message("✅ System prompt updated!")
@client.slash_command(name="view_prompt")
async def view_prompt(ctx):
    """View the current system prompt."""
    await ctx.send(f"Current system prompt:\n```\n{system_prompt}\n```")

# --- Message Event ---
@client.event
async def on_message(message: nextcord.Message):
    if message.author.bot or not client.user.mentioned_in(message):
        return

    query = message.content.replace(f"<@{client.user.id}>", "").strip()
    if not query:
        return

    await message.channel.trigger_typing()

    try:
        response = mistral.chat.complete(
            model="mistral-medium-2508",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        answer = response.choices[0].message.content.strip()
        answer = answer.replace("Mistral AI", "Kattar peshawri Marwat Pashtun")
        answer = answer.replace("OpenAI", "Kattar peshawri Marwat Pashtun")

    except Exception as e:
        answer = f"❌ Error: {e}"

    await message.channel.send(answer[:2000])

# --- Run Bot ---
client.run("YOUR DISCORD BOT TOKEN")


