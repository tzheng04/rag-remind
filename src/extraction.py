import os
from dotenv import load_dotenv

from openai import OpenAI
from pydantic import BaseModel
from typing import Optional

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
    For example:
    - If the message timestamp is February 12, 2026 and the user says "in March", use March 2026.
    - If the message timestamp is February 12, 2026 and the user says "in January", use January 2027.

    If a time is provided with no date, use today's date relative to the provided message timestamp.

    Unless explicitly stated otherwise, the phrases "by midnight" and "before midnight" refers to 11:59 PM on that day.

    Do not invent missing date or time components unless explicitly determined by the message or one of the rules above.
"""

class Reminder(BaseModel):
    title: str
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    hour: Optional[int]
    minute: Optional[int]
    reminder_type: str

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