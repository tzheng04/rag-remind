import os
from dotenv import load_dotenv

from openai import OpenAI
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Annotated, Literal

SYSTEM_PROMPT = """
    You extract reminders from Discord messages. 

    Field definitions:
    - "title": short description of what should be remembered
    - "reminder_type": 
        - "task" for something that the user needs to do or complete
        - "event" for an upcoming activity, meeting, or plan
        - "reminder" for information the user wants to remember but is not a task or an event

    Use the provided message timestamp as the reference point for relative dates such as "today", "tomorrow", "next week", and similar expressions.

    Unless explicitly stated otherwise, interpret all times to America/New_York timezone.
    
    If a month or date is provided without the year, use the next occurrence that is not in the past relative to the provided message timestamp.
    Examples:
    - If the message timestamp is February 12, 2026 and the user says "in March", use March 2026.
    - If the message timestamp is February 12, 2026 and the user says "in January", use January 2027.
    
    Interpret “next week” as the next Monday through Sunday after the week containing the message timestamp.
    Use "range_start" and "range_end" only when the message refers to a span of dates.
    Examples:
    - "next week" → use range_start and range_end
    - "this weekend" → use range_start and range_end
    - "October 3 through October 7" → use range_start and range_end
    - "in October" → use year and month; leave range_start and range_end null
    - "next year" → use year; leave range_start and range_end null
    - "Friday" → use year, month, and day; leave range_start and range_end null
    Do not populate both the date component fields and the range fields for the same temporal expression unless necessary to preserve information.

    If a time is provided with no date, use today's date relative to the provided message timestamp.

    Unless explicitly stated otherwise, the phrases "by midnight" and "before midnight" refers to 11:59 PM on that day.

    Do not invent missing date or time components unless explicitly determined by the message or one of the rules above.
"""

RECURRING_SYSTEM_PROMPT = """
    You extract recurring reminders from Discord messages.

    Field definitions:
    - "title": short description of what should be remembered
    - "reminder_type": 
        - "task" for something that the user needs to do or complete
        - "event" for an upcoming activity, meeting, or plan
        - "reminder" for information the user wants to remember but is not a task or an event
    - "frequency":
        - "daily" for reminders that repeat every N days
        - "weekly" for reminders that repeat every N weeks
        - "monthly" for reminders that repeat every N months
        - "yearly" for reminders that repeat every N years
    - "interval_value": number of frequency units between occurrences. Default to 1 when recurrence is specified but no interval is given.
    - "weekdays": list of weekdays associated with a weekly recurrence, using Monday = 0 through Sunday = 6, or null if not applicable
    - "day_of_month": day of the month from 1 through 31 for monthly or yearly recurrence, or null if not applicable
    - "start_date": the earliest date on or after the message timestamp that matches the recurrence pattern
    - "end_date": date after which the recurring reminder should stop, or null if no end date is provided

    Use the provided message timestamp as the reference point for relative dates such as "today", "tomorrow", "next week", and similar expressions.

    Unless explicitly stated otherwise, interpret all times in the America/New_York timezone.

    Interpret recurrence expressions according to the following rules:

    - "every day" → frequency = "daily", interval_value = 1
    - "every 3 days" → frequency = "daily", interval_value = 3
    - "every Wednesday" → frequency = "weekly", interval_value = 1, weekdays = [2]
    - "every 2 weeks on Wednesday" → frequency = "weekly", interval_value = 2, weekdays = [2]
    - "every month on the 15th" → frequency = "monthly", interval_value = 1, day_of_month = 15
    - "every 3 months on the 1st" → frequency = "monthly", interval_value = 3, day_of_month = 1
    - "every year on October 5" → frequency = "yearly", interval_value = 1, month = 10, day_of_month = 5
    - "every weekday" → frequency = "weekly", interval_value = 1, weekdays = [0, 1, 2, 3, 4]
    - "every weekend" → frequency = "weekly", interval_value = 1, weekdays = [5, 6]

    If the user specifies a time, extract the hour and minute.
    Example:
    - "every Wednesday at 7 PM" → frequency = "weekly", interval_value = 1, weekdays = [2], hour = 19, minute = 0

    Always populate the start_date as the first day reminder becomes active and from which the recurrence schedule is anchored.
    Examples:
    - "remind me every Thursday at 4pm..." → use the nearest occurence of Thursday, 4PM that is not in the past relative to the message timestamp and use it as start_date
    - "starting next Monday, remind me every week..." → resolve next Monday relative to the message timestamp and use it as start_date
    - "every Friday starting October 2" → use October 2 as start_date
    Consider that it is acceptable for the start_date to match the date of the message timestamp.

    If the user specifies when the recurrence should stop, populate end_date.
    Examples:
    - "every Wednesday until December 1" → use December 1 as end_date
    - "every day through Friday" → use Friday as end_date

    If a month or date is provided without a year, use the next occurrence that is not in the past relative to the provided message timestamp.

    Do not invent missing recurrence components, dates, or times unless they can be explicitly determined from the message or one of the rules above.
"""

CONTEXT_SYSTEM_PROMPT = """
    You generate concise context for a Discord reminder using the surrounding conversation, reminder title, source message, and the source message's timestamp.

    Identify only conversation details that would be useful when the reminder is delivered.

    Field definitions:
    - "useful": boolean indicating whether or not useful context could be generated
    - "content": short string describing the context of the reminder, or None

    Useful context examples:
    - What activity, task, or event the reminder refers to
    - Location
    - People involved
    - Agreed upon plans
    - Changes to the time, date, or location
    - Constraints
    - Other necessary details

    Use the provided message timestamp as the reference point for relative dates such as "today", "tomorrow", "next week", and similar expressions.
    Note that the provided timestamp is of the source message.
    
    Unless explicitly stated otherwise, interpret all times in the America/New_York timezone.

    Do not invent information or include unrelated conversation.

    Do not repeat information already contained in the reminder.

    Do not assume that messages provided are strictly relevant to the reminder.

    If the context conflicts with the reminder, explain the changes or uncertainties.

    If there is no useful additional context, indicate this by returning useful as False and context as None.

    Keep the context concise.
"""

class Reminder(BaseModel):
    title: str
    year: int | None = None
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    range_start: date | None = None
    range_end: date | None = None
    reminder_type: Literal["task", "event", "reminder"]

Weekday = Annotated[int, Field(ge=0, le=6)]

class RecurringReminderExtraction(BaseModel):
    title: str
    reminder_type: Literal["task", "event", "reminder"]
    frequency: Literal["daily", "weekly", "monthly", "yearly"]
    interval_value: int = Field(default=1, ge=1)
    weekdays: list[Weekday] | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    month: int | None = Field(default=None, ge=1, le=12)
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    start_date: date
    end_date: date | None = None

class RecurringReminder(RecurringReminderExtraction):
    reminder_id: int | None = None
    message_id: int | None = None
    author_id: int | None = None
    next_reminder: datetime | None = None
    last_reminder_date: date | None = None
    active: bool = True

class Context(BaseModel):
    useful: bool
    content: str | None

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

def extract_reminder(message: str, timestamp: str) -> Reminder:
    """
    Extract a Reminder object from a message and a timestamp.

    Args:
        message: Discord message content
        timestamp: datetime the message was sent, as a string

    Returns:
        Reminder object
    """
    response = client.responses.parse(
        model="gpt-5.6-luna",
        input = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
                    Timestamp: {timestamp}
                    Message: {message}
                """
            }
        ],
        text_format=Reminder
    )

    return response.output_parsed

def extract_recurring(message: str, timestamp: str) -> RecurringReminderExtraction:
    """
    Extract a RecurringReminderExtraction object from a message and a timestamp.

    Args:
        message: Discord message content
        timestamp: datetime the message was sent, as a string

    Returns:
        RecurringReminderExtraction object
    """
    response = client.responses.parse(
        model="gpt-5.6-luna",
        input = [
            {
                "role": "system",
                "content": RECURRING_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
                    Timestamp: {timestamp}
                    Message: {message}
                """
            }
        ],
        text_format=RecurringReminderExtraction
    )

    return response.output_parsed

def extract_context(title: str, source: str, conversation: str, timestamp: str) -> Context:
    """
    Extract the Context of a reminder.

    Args:
        title: Reminder title
        source: Original message that generated the reminder
        conversation: Discord message history from fetch_context()
        timestamp: datetime the source message was sent, as a string

    Returns:
        Context object
    """
    response = client.responses.parse(
        model="gpt-5.6-luna",
        input = [
            {
                "role": "system",
                "content": CONTEXT_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
                    Timestamp: {timestamp}
                    Reminder title: {title}
                    Source message: {source}
                    Conversation: {conversation}
                """
            }
        ],
        text_format=Context
    )

    return response.output_parsed