import os
from dotenv import load_dotenv

from openai import OpenAI
from pydantic import BaseModel, Field
from datetime import date
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
    - "start_date": date on which the recurring reminder becomes active, or null if no explicit start date is provided
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

    If the user specifies when the recurrence should begin, populate start_date.
    Examples:
    - "starting next Monday, remind me every week..." → resolve next Monday relative to the message timestamp and use it as start_date
    - "every Friday starting October 2" → use October 2 as start_date

    If the user specifies when the recurrence should stop, populate end_date.
    Examples:
    - "every Wednesday until December 1" → use December 1 as end_date
    - "every day through Friday" → use Friday as end_date

    If a month or date is provided without a year, use the next occurrence that is not in the past relative to the provided message timestamp.

    Do not invent missing recurrence components, dates, or times unless they can be explicitly determined from the message or one of the rules above.
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

class RecurringReminder(BaseModel):
    title: str
    reminder_type: Literal["task", "event", "reminder"]
    frequency: Literal["daily", "weekly", "monthly", "yearly"]
    interval_value: int = Field(default=1, ge=1)
    weekdays: list[Weekday] | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    month: int | None = Field(default=None, ge=1, le=12)
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    start_date: date | None = None
    end_date: date | None = None

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

def extract_reminder(message, timestamp):
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

def extract_recurring(message, timestamp):
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
        text_format=RecurringReminder
    )

    return response.output_parsed