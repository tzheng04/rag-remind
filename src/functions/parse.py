import re

KEYWORDS = {
    "remind", "remember", "rem", "soon",
    "tomorrow", "tom", "tmrw", "tm", "next",
    "today", "td", "tonight", "tn", 
    "morning", "morn", "afternoon", "noon", "evening", "midnight", "night",
    "week", "weekend",
    "monday", "mon", 
    "tuesday", "tue", "tues", 
    "wednesday", "wed", "thursday", 
    "thurs", "thu", 
    "friday", "fri", 
    "saturday", "sat", 
    "sunday", "sun",
    "meeting", "meet", "mtg", "scheduled",
    "appointment", "appt",
    "deadline", "due", "by", "on",
    "finish", "send", "submit", "finalize", "complete",
    "am", "pm",
    "month",
    "january", "jan",
    "february", "feb",
    "march", "mar",
    "april", "apr",
    "may",
    "june", "jun",
    "july", "jul",
    "august", "aug",
    "september", "sept",
    "october", "oct",
    "november", "nov",
    "december", "dec",
}

RECURRING_KEYWORDS = {
    "every", "each",
    "through",
    "daily", "weekly", "monthly", "yearly",
    "mondays", "tuesdays", "wednesdays", "thursdays", "fridays", "saturdays", "sundays"
}

# Regex pattern matching dates like 1/1, 2/14, 12/25, etc
DATE_REGEX = r"\b\d{1,2}/\d{1,2}\b"

def check_important(str: str) -> bool:
    """
    Searches string for KEYWORDS or dates

    Args:
        str: Discord message content

    Returns:
        True if KEYWORDS or date is found. Otherwise, False.
    """
    words = re.findall(r"\b\w+\b", str.lower())

    return any(token in words for token in KEYWORDS) or bool(re.search(DATE_REGEX, str))

def check_recurring(str: str) -> bool:
    """
    Searches string for RECURRING_KEYWORDS

    Args:
        str: Discord message content

    Returns:
        True if RECURRING_KEYWORDS is found. Otherwise, False.
    """
    words = re.findall(r"\b\w+\b", str.lower())
    
    return any(token in words for token in RECURRING_KEYWORDS)