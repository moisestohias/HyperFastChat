# Comprehensive Context Document: Enhanced Chat Application

## Project Overview
This is a lightweight yet feature-rich chat application built with **FastAPI**, **HTMX**, and **Hyperscript**. It supports multi-file uploads, real-time Markdown rendering with LaTeX support, and a robust background-streaming architecture that persists across page reloads.

## Core Purpose
The application provides a modern, dark-themed chat interface where users can:
- Send text messages with **Markdown** formatting and **Syntax Highlighting** (via Highlight.js).
- Write and render **LaTeX equations** (using `$` for inline and `$$` for block-level expressions).
- Upload and preview **multiple files** (images, PDFs) simultaneously.
- Experience a seamless, "no-refresh" UI powered by HTMX partial updates.
- Manage persistent conversations via unique **UUID-based URLs**.
- Interact with messages through actions like **Copy** (message & code blocks), **Edit**, **Regenerate**, and **Feedback** (Thumbs Up/Down).

## Current Focus & Recent Work
Recent development has introduced a resilient streaming architecture and optimized the rendering pipeline:
1. **Background Generation & Polling**:
   - Decoupled AI generation from the SSE connection. Responses are generated in an `asyncio.create_task` worker.
   - The `/bot-stream` endpoint acts as a state-aware listener, polling the conversation history and yielding updates as they occur in the backend.
2. **Streaming Resumption**:
   - Implemented auto-detection of `streaming` status in `index.html`.
   - If a page is reloaded during generation, the `chat_stream.html` partial is loaded with existing content, and the client-side `EventSource` re-connects to resume following the background task.
3. **Rendering Pipeline Optimization**: 
   - Moved all Markdown, LaTeX, and Syntax Highlighting logic into a dedicated `static/render.js` helper.
   - Implemented a specialized `renderMessageStreaming(el)` for live updates and `renderMessage(el)` for final, feature-complete rendering.
4. **Stateful Backend**:
   - Implemented a `chats` dictionary in `main.py` that stores full message history, including file metadata and generation status.

## File Structure
```
clean/
├── main.py              # FastAPI backend, background workers, & SSE polling
├── static/
│   ├── style.css        # Global CSS (Scrollbars, Markdown, Layout, Actions)
│   └── render.js        # Core rendering logic (Marked, KaTeX, Highlight.js, Copy)
└── templates/
    ├── base.html        # Main layout & global JS state
    ├── chat.html        # Main chat page container
    ├── index.html       # Landing page (History renderer & auto-resume logic)
    ├── chat_response.html # Static message partial (User/Bot)
    ├── chat_stream.html # Dynamic streaming message partial (SSE client)
    └── chat_input_field.html # Input form & multi-file handling logic
```

## Technology Stack
- **Backend**: FastAPI (Python)
- **Templating**: Jinja2
- **UI Framework**: Tailwind CSS (Tailwind CDN)
- **Interactivity**: HTMX (AJAX updates) & Hyperscript (Client-side triggers)
- **Streaming**: Native Server-Sent Events (SSE)
- **Rendering**: Marked.js (Markdown), KaTeX (LaTeX), Highlight.js (Code Syntax)

## Important Development Rules (LLM Guidelines)
1. **Background Logic**: AI responses must be generated in background tasks (`asyncio.create_task`). Never block the `StreamingResponse` generator with long-running compute.
2. **SSE Transport**: Always use `json.dumps()` for SSE `data:` payloads to safely handle newlines and special characters.
3. **State Resumption**: When rendering the chat history, always check for messages with a `streaming` status and load the corresponding streaming partial to allow UI continuity.
4. **Hyperscript & Data Attributes**: Never pass raw multi-line template variables into Hyperscript. Store them in `data-message="{{ message }}"` (properly escaped) and access via `my.dataset.message`.
5. **Horizontal Overflow**: Ensure wide elements like `pre`, `code`, and `.katex-display` use `overflow-x: auto` and reside in relative containers for fixed UI elements (like copy buttons).

---

*Note: The server is managed by the user. Do not attempt to start or restart the server.*
