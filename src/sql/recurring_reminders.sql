CREATE TABLE recurring_reminders (
    id SERIAL PRIMARY KEY,
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

    start_date DATE,
    end_date DATE,

    next_reminder TIMESTAMPTZ,
    active BOOLEAN NOT NULL DEFAULT TRUE
);