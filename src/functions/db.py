import os

from dotenv import load_dotenv
from supabase import Client, create_client
from functions.utils import calculate_next_recurring
from functions.extraction import Reminder, RecurringReminder, RecurringReminderExtraction

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

def save_reminder(reminder: Reminder, message):
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

def save_recurring(recurring_reminder_extraction: RecurringReminderExtraction, message):
    # save_message() and retain id for fk relation
    response = save_message(message)
    message_id = response.data[0]["id"]

    # Create a RecurringReminder object to pass into calculate_next_recurring()
    recurring_reminder = RecurringReminder(
        **recurring_reminder_extraction.model_dump(),
        reminder_id = None,
        message_id = message_id,
        author_id = message.author.id,
        last_reminder_date = recurring_reminder_extraction.start_date,
        next_reminder = None
    )
    recurring_reminder.next_reminder = calculate_next_recurring(recurring_reminder)

    response = generate_next_reminder(recurring_reminder)
    reminder_id = response.data[0]["id"]
    recurring_reminder.reminder_id = reminder_id

    data = recurring_reminder.model_dump(mode="json")

    return (
        supabase    
        .table("recurring_reminders")
        .insert(data)
        .execute()
    )

def generate_next_reminder(recurring_reminder: RecurringReminder):
    # Check if reminder already exists, in this case update it
    response = (
        supabase
        .table("reminders")
        .select("id")
        .eq("id", recurring_reminder.reminder_id)
        .execute()
    )

    if response.data:
        return (
            supabase
            .table("reminders")
            .update({
                "year": recurring_reminder.next_reminder.year,
                "month": recurring_reminder.next_reminder.month,
                "day": recurring_reminder.next_reminder.day,
                "hour": recurring_reminder.next_reminder.hour,
                "minute": recurring_reminder.next_reminder.minute,
            })
            .eq("id", recurring_reminder.reminder_id)
            .execute()
        )

    reminder = {
        "message_id": recurring_reminder.message_id,
        "author_id": recurring_reminder.author_id,
        "title": recurring_reminder.title,
        "year": recurring_reminder.next_reminder.year,
        "month": recurring_reminder.next_reminder.month,
        "day": recurring_reminder.next_reminder.day,
        "hour": recurring_reminder.next_reminder.hour,
        "minute": recurring_reminder.next_reminder.minute,
        "reminder_type": "recurring",
    }

    return (
        supabase
        .table("reminders")
        .insert(reminder)
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

def fetch_recurring_updates(now):
    return (
        supabase
        .table("recurring_reminders")
        .select("*")
        .eq("active", True)
        .lte("next_reminder", now.isoformat())
        .execute()
    )

def update_recurring(now):
    outdated_recurring_reminders = fetch_recurring_updates(now)

    for recurring_reminder_dict in outdated_recurring_reminders.data:
        recurring_reminder = RecurringReminder(**recurring_reminder_dict)
        next_reminder = calculate_next_recurring(recurring_reminder)

        (
            supabase
            .table("recurring_reminders")
            .update({
                "next_reminder": next_reminder.isoformat(),
                "last_reminder_date": recurring_reminder.next_reminder.date().isoformat(),
            })
            .eq("reminder_id", recurring_reminder.reminder_id)
            .execute()
        )

        recurring_reminder.next_reminder = next_reminder
        generate_next_reminder(recurring_reminder)

    print("Finished updating recurring reminders")

def delete_reminder(reminder_id, user_id):
    response = (
        supabase
        .table("reminders")
        .select("id, message_id, title, reminder_type")
        .eq("id", reminder_id)
        .eq("author_id", user_id)
        .execute()
    )

    if not response.data:
        return f"Failed to delete reminder #{reminder_id}"

    reminder = response.data[0]
    message_id = reminder["message_id"]
    reminder_type = reminder["reminder_type"]

    if (reminder_type == "recurring"):
        delete_recurring(reminder_id, user_id)

    (
        supabase
        .table("reminders")
        .delete()
        .eq("id", reminder_id)
        .execute()
    )

    (
        supabase
        .table("messages")
        .delete()
        .eq("id", message_id)
        .execute()
    )

    if (reminder_type == "recurring"):
        return f"Successfully deleted recurring reminder associated with #{reminder_id}: {reminder['title']}"
    else:
        return f"Successfully deleted reminder #{reminder_id}: {reminder['title']}"

def delete_recurring(reminder_id):
    (
        supabase
        .table("recurring_reminders")
        .delete()
        .eq("id", reminder_id)
        .execute()
    )

    return f"Successfully deleted recurring reminder associated with #{reminder_id}"

