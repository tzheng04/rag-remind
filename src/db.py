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
    response = save_message(message)
    message_id = response.data[0]["id"]
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