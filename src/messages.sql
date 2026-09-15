CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    message_id BIGINT UNIQUE NOT NULL,
    channel_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    author_name TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);