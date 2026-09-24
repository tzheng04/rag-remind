import calendar
from datetime import date, datetime

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