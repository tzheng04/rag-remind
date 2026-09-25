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

DATE_REGEX = r"\b\d{1,2}/\d{1,2}\b"

def check_important(str):
    str = str.lower()

    return any(token in str for token in KEYWORDS) or bool(re.search(DATE_REGEX, str))