import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from db import save_reminder, fetch_recent
from parse import check_important
from extraction import extract_reminder

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Temporary channel id to restrict scope to test channel
TRACKED_CHANNEL = 1549134537458450542

@client.event
async def on_ready():
    synced = await tree.sync()
    print(f"Synced {len(synced)} commands")
    print(f"Logged in as {client.user}")

@tree.command(name="recent", description="Show recent stored messages")
async def recent(interaction: discord.Interaction):
    recent_messages = fetch_recent(TRACKED_CHANNEL)

    if not recent_messages:
        await interaction.response.send_message("No recent messages")
        return

    response = []

    for message in reversed(recent_messages):
        response.append(f"{message['author_name']}: {message['content']}")

    await interaction.response.send_message("\n".join(response))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id != TRACKED_CHANNEL:
        return

    # print(
    #     message.author,
    #     message.channel,
    #     message.content
    # )
    if (check_important(message.content)):
        reminder = extract_reminder(message.content, message.created_at.isoformat())
        print(reminder)
        save_reminder(reminder, message)
        await message.channel.send(f"You said {message.content}: reminder saved")
    else:
        await message.channel.send(f"You said {message.content}: no reminder found")

    # save_message(message)

client.run(TOKEN)