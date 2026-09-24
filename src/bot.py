import os

import discord
from discord import app_commands
from dotenv import load_dotenv

import calendar
from datetime import datetime
from db import save_reminder, fetch_recent, fetch_reminders
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
    recent_messages = fetch_recent(TRACKED_CHANNEL).data

    if not recent_messages:
        await interaction.response.send_message("No recent messages")
        return

    response = []

    for message in reversed(recent_messages):
        response.append(f"{message['author_name']}: {message['content']}")

    await interaction.response.send_message("\n".join(response))

@tree.command(name="showreminders", description="Show your reminders")
async def showReminders(interaction: discord.Interaction):
    stored_reminders = fetch_reminders(interaction.user.id).data

    if not stored_reminders:
            await interaction.response.send_message("No reminders available")
            return

    response = []
    datetimeless = []

    # probably want to move this whole thing to another file later
    for reminder in stored_reminders:
        reminder_string = ""
        if reminder["day"]:
            date_str = f"{reminder['month']}-{reminder['day']}-{reminder['year']}"
            date = datetime.strptime(date_str, "%m-%d-%Y")
            reminder_string += f"{date.strftime('%a')}. {date.month}-{date.day}-{date.year}"
            if reminder["range_end"]:
                range_end_datetime = datetime.strptime(reminder["range_end"], "%Y-%m-%d")
                reminder_string += f" to {range_end_datetime.strftime('%a')}. {range_end_datetime.month}-{range_end_datetime.day}-{range_end_datetime.year}"
            if reminder["minute"] is not None:
                time_str = f"{reminder['hour']}:{reminder['minute']}"
                time = datetime.strptime(time_str, "%H:%M")
                reminder_string += f" at {time.hour % 12 or 12}:{time.minute:02d} {'AM' if time.hour < 12 else 'PM'}"
        elif reminder["month"]:
            reminder_string += f"{calendar.month_abbr[reminder['month']]}. {reminder['year']}"
        elif reminder["year"]:
            reminder_string += f"{reminder['year']}"
        else:
            datetimeless.append(f"{reminder['title']} (ID: {reminder['id']})")
            continue
        reminder_string += f": {reminder['title']}"
        response.append(f"{reminder_string} (ID: {reminder['id']})")

    # handles reminders without datetime
    if datetimeless:
        response.append("")
        response.append("To do:")
        for reminder in datetimeless:
            response.append(reminder)
    
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