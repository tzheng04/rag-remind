CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    year INT,
    month INT,
    day INT,
    hour INT,
    minute INT,
    reminder_type TEXT NOT NULL,
);