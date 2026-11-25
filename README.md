# Project Overview
Discord bot for convenient reminders. Uses OpenAI API to extract tasks, events, and important reminders from natural user conversation.  
Structured data is stored in Supabase/PostgreSQL and support retrieval through app commands.  

## Reducing token usages
When a message is sent in the channel, Reminder Bot reads it and uses regex to look for notable features like specific keywords, dates, and times.  
See ![parse.py](./src/functions/parse.py) to see the keywords and more.  

## Current state
![Extract reminders from natural language using LLM](./examples/save_reminder.png)  
![Fetch and display upcoming reminders in the app](./examples/showreminders.png)  

## Context window
Generates context from the conversation around the original message!  
![Context window](./examples/context_window.png)  

## Schema
A PostgreSQL database is used to store user messages and reminders.  
- 'messages': stores source messages of reminders, including content and metadata
- 'recurring_reminders: stores reminders with intervals and other metadata. Note that a recurring_reminder generates a regular reminder.
- 'reminders': stores one time reminders and metadata

recurring_reminders references messages and reminders; reminders references messages (see below)
![Reference diagram](./examples/references.png)  

## Roadmap
- Implement natural language querying for personal reminders
- Use RAG on conversation history
- Add privacy settings
- Improve how reminders are displayed
- Containerization and deployment