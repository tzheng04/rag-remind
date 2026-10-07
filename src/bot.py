import os
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv

from functions.db import save_reminder, save_recurring, fetch_recent, fetch_reminders, delete_reminder, send_reminders, update_recurring
from functions.parse import check_important, check_recurring
from functions.utils import process_reminders
from functions.extraction import extract_reminder, extract_recurring

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

TZ = ZoneInfo("America/New_York")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Temporary channel id to restrict scope to test channel
TRACKED_CHANNEL = 1549134537458450542

@tasks.loop(seconds=30)
async def update_recurring_loop():
    channel = client.get_channel(TRACKED_CHANNEL)

    now = datetime.now(TZ)

    reminders = send_reminders(now)
    if reminders:
        for reminder in reminders:
            await channel.send(reminder)
            
    update_recurring(now)
    
@client.event
async def on_ready():
    synced = await tree.sync()
    print(f"Synced {len(synced)} commands")
    if not update_recurring_loop.is_running():
        update_recurring_loop.start()
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

    if (check_recurring(message.content)):
        reminder = extract_recurring(message.content, message.created_at.isoformat())
        print(reminder)
        save_recurring(reminder, message)
        await message.channel.send(f"Saved recurring reminder: {reminder}")
    elif (check_important(message.content)):
        reminder = extract_reminder(message.content, message.created_at.isoformat())
        print(reminder)
        save_reminder(reminder, message)
        await message.channel.send(f"Saved reminder: {reminder}")

client.run(TOKEN)