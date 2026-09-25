import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from functions.db import save_reminder, fetch_recent, fetch_reminders, delete_reminder
from functions.parse import check_important
from functions.utils import process_reminders
from functions.extraction import extract_reminder

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
    recent_messages = fetch_recent(TRACKED_CHANNEL).data

    if not recent_messages:
        await interaction.response.send_message("No recent messages")
        return

    response = []

    for message in reversed(recent_messages):
        response.append(f"{message['author_name']}: {message['content']}")

    await interaction.response.send_message("\n".join(response))

@tree.command(name="showreminders", description="Show your reminders")
async def show_reminders(interaction: discord.Interaction):
    stored_reminders = fetch_reminders(interaction.user.id).data

    if not stored_reminders:
            await interaction.response.send_message("No reminders available")
            return

    response = process_reminders(stored_reminders)

    message = ""
    for group, lines in response.items():
        if lines:
            message += f"{group}: \n"
            message += "\n".join(lines)
            message += "\n\n"
    
    await interaction.response.send_message(message)

@tree.command(name="delete", description="Delete a reminder")
async def delete(interaction: discord.Interaction, reminder_id: int):
    user_id = interaction.user.id

    response = delete_reminder(reminder_id, user_id)

    await interaction.response.send_message(response)

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
        await message.channel.send(f"Saved reminder: {reminder}")
    # else:
        # await message.channel.send(f"You said {message.content}: no reminder found")

    # save_message(message)

client.run(TOKEN)