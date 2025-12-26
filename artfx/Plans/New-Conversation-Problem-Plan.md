# Bug: New Conversation Message Forking

## Problem Description
When a user starts a new conversation (URL: `/` or `/chat/new`), sending the first message correctly creates a new conversation ID (e.g., `UUID-1`) and updates the browser URL (via `HX-Push-Url`). However, subsequent messages sent from the same page are not appended to `UUID-1`. Instead, each new message triggers the creation of a *new* separate conversation (e.g., `UUID-2`, `UUID-3`), appearing as if they were successfully added to the chat visually, but persisting as separate isolated chats in the backend. This behavior persists until the page is reloaded.

## Root Cause Analysis
1.  **Initial State**: The "New Chat" page renders the input form with `hx-post="/chat/new/send-message"` (see `templates/chat_input_field.html`).
2.  **First Message**:
    - The user submits the form.
    - The backend (`main.py`, `/send-message`) detects `conv_id="new"`.
    - It generates a new `actual_conv_id` (e.g., `UUID-1`).
    - It saves the message to `UUID-1`.
    - It returns the HTML for the message and a `HX-Push-Url: /chat/UUID-1` header.
3.  **The Failure**:
    - The `HX-Push-Url` header successfully updates the browser's address bar.
    - **However**, the DOM element `<form id="chatForm" ...>` **creates no update** to its `hx-post` attribute. It remains `hx-post="/chat/new/send-message"`.
    - HTMX does not automatically update attributes of the triggering element based on the `HX-Push-Url`.
4.  **Subsequent Messages**:
    - When the user sends the next message, the form submits to `/chat/new/send-message` again.
    - The backend sees `new` again, creates `UUID-2`, and effectively forks the conversation.
    - Visually, the response is appended to `#new-messages`, so it looks correct, but the state is desynchronized.

## Fix Implementation Plan
To fix this, we must ensure that the form's `hx-post` attribute is updated to point to the created conversation ID immediately after the first message is processed.

**Solution: Out-of-Band (OOB) Swap for the Input Form**

In `main.py` -> `send_message`:
1.  Identify when a new conversation is created (`if is_new:`).
2.  Render the `chat_input_field.html` template using the new `actual_conv_id` and the current provider/model configuration.
3.  Wrap this rendered HTML in a div targeting the form container (or the form itself) with `hx-swap-oob`.
    - Target: `#chat-form-container` (defined in `templates/chat.html`).
    - Attribute: `hx-swap-oob="innerHTML"`.
4.  Append this OOB block to the response content.

This ensures that as soon as the first message returns, the input form is silently replaced with one that targets `/chat/UUID-1/send-message`.

### Code Changes (Proposed)
**File: `main.py`**
In the `send_message` function, inside the `if is_new:` block:

```python
    if is_new:
        # Push new URL
        headers["HX-Push-Url"] = f"/chat/{actual_conv_id}"
        
        # Sidebar update (existing code)
        sidebar_item_html = templates.get_template("sidebar_item.html").render({
            "request": request,
            "conv_id": actual_conv_id,
            "title": chats[actual_conv_id]["title"],
            "active": True
        })
        response_content += f'<div id="sidebar-list" hx-swap-oob="afterbegin">{sidebar_item_html}</div>'

        # --- FIX START ---
        # Update the Input Form OOB to point to the new ID
        input_field_html = templates.get_template("chat_input_field.html").render({
            "request": request,
            "conversation_id": actual_conv_id,
            "current_provider": chats[actual_conv_id]["provider"],
            "current_model": chats[actual_conv_id]["model"]
        })
        response_content += f'<div id="chat-form-container" hx-swap-oob="innerHTML">{input_field_html}</div>'
        # --- FIX END ---
```
