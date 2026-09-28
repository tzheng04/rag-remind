import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta

TZ = ZoneInfo("America/New_York")

def process_reminders(reminders):
    expired = []
    regular = []
    datetimeless = []

    now = datetime.now()
    date_today = date.today()

    for reminder in reminders:
        reminder_string = ""
        past = False
        today = False
        if reminder["day"]:
            date_str = f"{reminder['month']}-{reminder['day']}-{reminder['year']}"
            reminder_date = datetime.strptime(date_str, "%m-%d-%Y").date()
            # For date ranges check the range_end instead
            if not reminder["range_end"] and reminder_date < date_today:
                past = True
            elif reminder_date == date_today:
                today = True
            reminder_string += f"{reminder_date.strftime('%a')}. {reminder_date.month}-{reminder_date.day}-{reminder_date.year}"
            if reminder["range_end"]:
                range_end_date = datetime.strptime(reminder["range_end"], "%Y-%m-%d").date()
                if range_end_date < date_today:
                    past = True
                reminder_string += f" to {range_end_date.strftime('%a')}. {range_end_date.month}-{range_end_date.day}-{range_end_date.year}"
            if reminder["minute"] is not None:
                time_str = f"{reminder['hour']}:{reminder['minute']}"
                time = datetime.strptime(time_str, "%H:%M")
                if today and time < now.time():
                    past = True
                reminder_string += f" at {time.hour % 12 or 12}:{time.minute:02d} {'AM' if time.hour < 12 else 'PM'}"
        elif reminder["month"]:
            if reminder['year'] < now.year and reminder['month'] < now.month:
                past = True
            reminder_string += f"{calendar.month_abbr[reminder['month']]}. {reminder['year']}"
        elif reminder["year"]:
            if reminder['year'] < now.year:
                            past = True
            reminder_string += f"{reminder['year']}"
        else:
            datetimeless.append(f"{reminder['title']} (ID: {reminder['id']})")
            continue
        reminder_string += f": {reminder['title']}"
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

def calculate_next_recurring(recurring_reminder):
    now = datetime.now(TZ)
    today = now.date()

    # Defaults to 8AM if no time was provided by the user when creating the reminder
    hour = recurring_reminder.hour if recurring_reminder.hour is not None else 8
    minute = recurring_reminder.minute if recurring_reminder.minute is not None else 0

    if recurring_reminder.frequency == "daily":
        candidate = recurring_reminder.start_date + timedelta(days=recurring_reminder.interval_value)

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
        # Monday of the start_date week
        start = recurring_reminder.start_date - timedelta(days=recurring_reminder.start_date.weekday())

        # Try days up to a year until we find a day that matches the recurrence
        for days in range(0, 366):
            candidate = today + timedelta(days=days)

            if candidate.weekday() not in recurring_reminder.weekdays:
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
        start = recurring_reminder.start_date
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
        month = recurring_reminder.month if recurring_reminder.month is not None else recurring_reminder.start_date.month
        day = recurring_reminder.day_of_month if recurring_reminder.day_of_month is not None else recurring_reminder.start_date.day

        start = recurring_reminder.start_date
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