# How the Streaming Architecture Works

## Overview
This application uses a **decoupled streaming architecture** where AI generation happens in a background task, while the UI uses Server-Sent Events (SSE) to poll and display updates.

## Flow

### 1. User Sends Message (`send_message` in `main.py`)
- User message is saved to `chats[conv_id]["messages"]`
- A placeholder assistant message is added with `status: "streaming"` and empty content
- Background task `run_chatbot_logic(conv_id)` is started via `asyncio.create_task()`
- Returns HTML for user message + `chat_stream.html` partial to HTMX

### 2. Background Generation (`run_chatbot_logic`)
- Iterates through simulated tokens, updating `assistant_msg["content"]` in real-time
- Sets `status: "complete"` when finished
- Runs independently of any HTTP request

### 3. SSE Endpoint (`/chat/{conv_id}/bot-stream`)
- The `generate_bot_response_stream` function polls the shared `chats` state
- While `status == "streaming"`, it yields `event: token` with accumulated content
- On completion, yields `event: done` with action buttons HTML

### 4. Client-Side Streaming (`chat_stream.html`)
- Creates an `EventSource` connection to `/bot-stream`
- On `token` events: updates displayed text and re-renders Markdown
- On `done` events: performs final render and shows action buttons
- Auto-resumes if page was reloaded during streaming (handled in `index.html`)

### 5. Page Reload Recovery (`index.html`)
- When rendering history, checks if the last assistant message has `status: "streaming"`
- If so, includes `chat_stream.html` with the accumulated content to resume the SSE connection

## Key Design Points
- **Decoupled**: Generation doesn't block the SSE response
- **Resilient**: Page reloads don't lose progress (background task continues)
- **Shared State**: Both backend task and SSE poller read from `chats[conv_id]["messages"]`
