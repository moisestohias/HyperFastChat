# How `templates/index.html` Works

This template extends `chat.html` and handles **rendering the chat history** with a special case for interrupted streaming sessions.

## Template Logic Breakdown

```jinja
{% for msg in history %}
```

Iterates through all messages in the conversation history.

## The Key Logic: Auto-Resume for Interrupted Streaming

```jinja
{% if loop.last and msg.role == 'assistant' and msg.get('status') == 'streaming' %}
```

This condition checks **three things**:
1. `loop.last` - Is this the **last message** in the history?
2. `msg.role == 'assistant'` - Is it a **bot message**?
3. `msg.get('status') == 'streaming'` - Was the bot **interrupted** during generation?

**Why this matters**: If the user reloaded the page while the bot was still streaming, the background task (`run_chatbot_logic`) continues running on the server. The message in `chats[conv_id]` has accumulated content but `status` is still `"streaming"`.

## Two Paths

| Condition | Action |
|-----------|--------|
| **Streaming resume case** | Includes `chat_stream.html` with current `msg.content`. This starts a new `EventSource` to continue receiving updates from the background task. |
| **Normal case** | Includes `chat_response.html` for completed messages (user or bot). |

## Example Scenarios

1. **Fresh page load, conversation complete**: Last message has `status: "complete"` → renders as normal `chat_response.html`

2. **Page reload during streaming**: Last message has `status: "streaming"` and partial content → renders `chat_stream.html` which reconnects to `/bot-stream` and continues receiving tokens

3. **First message (no streaming yet)**: No "last message" matching criteria → normal loop continues

This design ensures **session continuity** even if the user refreshes or loses connection during streaming.
