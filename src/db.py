import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_message(message):
    data = {
        "message_id": message.id,
        "channel_id": message.channel.id,
        "author_id": message.author.id,
        "author_name": message.author.name,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }

    return (
        supabase
        .table("messages")
        .insert(data)
        .execute()
    )

def save_reminder(reminder, message):
    # save_message() and retain id for fk relation
    response = save_message(message)
    message_id = response.data[0]["id"]

    # fill in year, month, and day fields for easier querying later
    if reminder.range_start:
        reminder.year = reminder.range_start.year
        reminder.month = reminder.range_start.month
        reminder.day = reminder.range_start.day    

    data = reminder.model_dump(mode="json")
    data["message_id"] = message_id
    data["author_id"] = message.author.id

    return (
        supabase
        .table("reminders")
        .insert(data)
        .execute()
    )

def fetch_recent(channel):
    return (
        supabase
        .table("messages")
        .select("author_name, content, created_at")
        .eq("channel_id", channel)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )

def fetch_reminders(user_id):
    return (
        supabase
        .table("reminders")
        .select("*")
        .eq("author_id", user_id)
        .order("year")
        .order("month")
        .order("day")
        .order("hour")
        .order("minute")
        .execute()
    )

def delete_reminder(reminder_id, user_id):
    response = (
        supabase
        .table("reminders")
        .select("id, title")
        .eq("id", reminder_id)
        .eq("author_id", user_id)
        .execute()
    )

    if not response.data:
        return f"Failed to delete reminder #{reminder_id}"

    reminder = response.data[0]

    (
        supabase
        .table("reminders")
        .delete()
        .eq("id", reminder_id)
        .execute()
    )

    return f"Successfully deleted reminder #{reminder_id}: {reminder['title']}"
    