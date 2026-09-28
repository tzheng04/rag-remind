CREATE TABLE recurring_reminders (
    id SERIAL PRIMARY KEY,
    reminder_id INTEGER REFERENCES reminders(id)
    message_id INTEGER REFERENCES messages(id),
    author_id BIGINT NOT NULL,

    title TEXT NOT NULL,
    reminder_type TEXT NOT NULL,

    frequency TEXT NOT NULL,
    interval_value INTEGER NOT NULL DEFAULT 1,

    weekdays INTEGER[],
    day_of_month INTEGER,
    month INTEGER,

    hour INTEGER,
    minute INTEGER,

    start_date DATE NOT NULL,
    end_date DATE,

    next_reminder TIMESTAMPTZ,
    last_anchor_date DATE

    active BOOLEAN NOT NULL DEFAULT TRUE
);