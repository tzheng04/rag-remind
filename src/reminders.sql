CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id),
    title TEXT NOT NULL,
    year INT,
    month INT,
    day INT,
    hour INT,
    minute INT,
    range_start DATE,
    range_end DATE,
    reminder_type TEXT NOT NULL
);