import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from functions.extraction import RecurringReminder

# Defaults to America East timezone
TZ = ZoneInfo("America/New_York")

def process_reminders(reminders: list[dict]) -> dict:
    """
    Iterate through a list of reminders and convert them to strings. Use fetch_reminders() to get appropriate results.

    Args:
        reminders: List of reminders as dicts, ordered by time through fetch_reminders().

    Returns:
        Dict with keys "Past reminders", "Current reminders", and "To do", each containing lists of strings.
    """
    # Initialize our three groups of reminders
    expired = []
    regular = []
    datetimeless = []

    now = datetime.now()
    date_today = date.today()

    # Iterate through reminders and conditionally generate the resultant string
    for reminder in reminders:
        reminder_string = ""
        past = False
        today = False

        # Check if the reminder has a specific date defined.
        if reminder["day"]:
            # Create a date object for comparison
            date_str = f"{reminder['month']}-{reminder['day']}-{reminder['year']}"
            reminder_date = datetime.strptime(date_str, "%m-%d-%Y").date()

            # Check if the reminder is expired.
            # For date ranges check the range_end instead.
            if not reminder["range_end"] and reminder_date < date_today:
                past = True
            elif reminder_date == date_today:
                today = True

            # Add the weekday and date
            reminder_string += f"{reminder_date.strftime('%a')}. {reminder_date.month}-{reminder_date.day}-{reminder_date.year}"

            # If a date range was provided, check if the reminder is expired.
            if reminder["range_end"]:
                range_end_date = datetime.strptime(reminder["range_end"], "%Y-%m-%d").date()
                if range_end_date < date_today:
                    past = True
                # Add the range_end to the string
                reminder_string += f" to {range_end_date.strftime('%a')}. {range_end_date.month}-{range_end_date.day}-{range_end_date.year}"

            # If a time was provided, add the time to the string.
            if reminder["minute"] is not None:
                time_str = f"{reminder['hour']}:{reminder['minute']}"
                time = datetime.strptime(time_str, "%H:%M").time()
                # Check if the reminder is expired.
                if today and time < now.time():
                    past = True
                # Add the time and AM or PM
                reminder_string += f" at {time.hour % 12 or 12}:{time.minute:02d} {'AM' if time.hour < 12 else 'PM'}"

        # If no day was provided, check if the month was provided.
        elif reminder["month"]:
            # Check if the reminder is expired.
            if reminder['year'] < now.year and reminder['month'] < now.month:
                past = True
            # Add the month and year.
            reminder_string += f"{calendar.month_abbr[reminder['month']]}. {reminder['year']}"

        # If no month was provided, check if the year was provided.
        elif reminder["year"]:
            # Check if the reminder is expired.
            if reminder['year'] < now.year:
                past = True
            # Add the year.
            reminder_string += f"{reminder['year']}"

        # If no time references were provided, the reminder is datetimeless.
        else:
            # Add the title and ID to the list and move on to the next reminder.
            datetimeless.append(f"{reminder['title']} (ID: {reminder['id']})")
            continue

        # Add the Recurring indicator to any recurring reminders. Note that datetimeless reminders cannot be recurring by definition.
        if reminder["reminder_type"] == "recurring":
            reminder_string += f" (Recurring)"

        # Add the reminder title to all non-datetimeless reminders
        reminder_string += f": {reminder['title']}"

        # Sort into expired or regular reminders
        if past:
            expired.append(f"{reminder_string} (ID: {reminder['id']})")
        else:
            regular.append(f"{reminder_string} (ID: {reminder['id']})")

    response = {
         "Past reminders": expired,
         "Current reminders": regular,
         "To do": datetimeless
    }

    return response

def calculate_next_recurring(recurring_reminder: RecurringReminder) -> datetime:
    """
    Calculate the next valid recurrence for a reminder. Defaults to 8AM if no time is provided.

    Args:
        recurring_reminder: RecurringReminder object. Requires last_reminder_date to be valid.

    Returns:
        datetime object representing the next valid occurence
    """
    now = datetime.now(TZ)
    today = now.date()

    # Defaults to 8AM if no time was provided by the user when creating the reminder
    hour = recurring_reminder.hour if recurring_reminder.hour is not None else 8
    minute = recurring_reminder.minute if recurring_reminder.minute is not None else 0

    if recurring_reminder.frequency == "daily":
        candidate = recurring_reminder.last_reminder_date + timedelta(days=recurring_reminder.interval_value)

        # Ensures we generate a valid date in the future
        while (candidate < today):
            candidate += timedelta(days=recurring_reminder.interval_value)
        
        candidate_datetime = datetime(
            candidate.year,
            candidate.month,
            candidate.day,
            hour,
            minute,
            tzinfo=TZ
        )
        
        return candidate_datetime
            

    elif recurring_reminder.frequency == "weekly":
        # Monday of the last_reminder_date week
        start = recurring_reminder.last_reminder_date - timedelta(days=recurring_reminder.last_reminder_date.weekday())

        # Try days up to a year until we find a day that matches the recurrence
        for days in range(0, 366):
            candidate = start + timedelta(days=days)

            if candidate.weekday() not in recurring_reminder.weekdays:
                continue

            if candidate < today:
                continue

            # Monday of the candidate week
            candidate_start = candidate - timedelta(days=candidate.weekday())

            # Check that weeks_elapsed matches the interval (i.e. every week, every two weeks, etc)
            weeks_elapsed = (candidate_start - start).days // 7
            if weeks_elapsed % recurring_reminder.interval_value != 0:
                continue

            candidate_datetime = datetime(
                candidate.year,
                candidate.month,
                candidate.day,
                hour,
                minute,
                tzinfo=TZ
            )
            if candidate_datetime <= now:
                continue

            return candidate_datetime

    elif recurring_reminder.frequency == "monthly":
        start = recurring_reminder.last_reminder_date
        candidate = start + timedelta(months=recurring_reminder.interval_value)

        # Ensures we generate a valid date in the future
        while (candidate < today):
            candidate += timedelta(months=recurring_reminder.interval_value)

        candidate_datetime = datetime(
            candidate.year,
            candidate.month,
            recurring_reminder.day_of_month,
            hour,
            minute,
            tzinfo=TZ
        )

        return candidate_datetime

    elif recurring_reminder.frequency == "yearly":
        # Prepare default values
        month = recurring_reminder.month if recurring_reminder.month is not None else recurring_reminder.last_reminder_date.month
        day = recurring_reminder.day_of_month if recurring_reminder.day_of_month is not None else recurring_reminder.last_reminder_date.day

        start = recurring_reminder.last_reminder_date
        candidate = start + timedelta(years=recurring_reminder.interval_value)

        # Ensures we generate a valid date in the future
        while (candidate < today):
            candidate += timedelta(years=recurring_reminder.interval_value)

        candidate_datetime = datetime(
            candidate.year,
            month,
            day,
            hour,
            minute,
            tzinfo=TZ
        )

        return candidate_datetime