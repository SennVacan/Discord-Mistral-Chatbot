import nextcord
from nextcord.ext import commands
from mistralai import Mistral

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

# --- Services ---
mistral = Mistral("YOUR MISTRAL KEY")

# Placeholder for study_service, replace with your actual service
class StudyService:
    def get_links(self, query: str):
        # Return a list of URLs or empty list
        return []

study_service = StudyService()

# --- Event ---
@client.event
async def on_message(message: nextcord.Message):
    """Reply when bot is mentioned. Includes replied message content and study links."""
    if message.author.bot or not client.user.mentioned_in(message):
        return

    query = message.content.replace(f"<@{client.user.id}>", "").strip()
    prompt_parts = []

    if message.reference:
        ref_msg = message.reference.resolved
        if isinstance(ref_msg, nextcord.Message) and ref_msg.content:
            prompt_parts.append(ref_msg.content)

    if query:
        prompt_parts.append(query)

    if not prompt_parts:
        return

    full_query = "\n\n".join(prompt_parts)
    await message.channel.trigger_typing()

    try:
        response = mistral.chat.complete(
            model="mistral-medium-2508",
            messages=[
                {
                    "role": "system",
                    "content": ( #add how you want your bot to behave, example:
                        # "Don't over talk too much."
                        # "Use sigma emojis (but less)."
                        # "Be really mysterious."
                    )  
                },
                {"role": "user", "content": full_query}
            ]
        )
        answer = response.choices[0].message.content.strip()

        # Ensure branding never leaks
        answer = answer.replace("Mistral AI", "discord chat bot") #what you want it to refer to itself


    except Exception as e:
        answer = f"Sorry, I couldn't process that. (Error: {e})"

    # Append study links
    links = study_service.get_links(full_query)
    if links:
        answer += "\n\nRelevant Resources:\n" + "\n".join(links)

    await message.reply(answer[:2000])

# --- Run Bot ---
client.run("YOUR BOT TOKEN")


