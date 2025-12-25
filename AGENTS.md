# Comprehensive Context Document: HyperFastChat

## Project Overview
This is a lightweight yet feature-rich chat application built with **FastAPI**, **HTMX**, and **Hyperscript**. It supports multi-file uploads, real-time Markdown rendering with LaTeX support, and a robust background-streaming architecture that persists across page reloads. The application features a persistent, collapsible sidebar for conversation history and management.

## Core Purpose
The application provides a modern, dark-themed chat interface where users can:
- **Chat**: Send text messages with **Markdown** formatting and **Syntax Highlighting** (via Highlight.js).
- **Math**: Write and render **LaTeX equations** (using `$` for inline and `$$` for block-level expressions).
- **Files**: Upload and preview **multiple files** (images, PDFs) simultaneously.
- **Sidebar**: Manage persistent conversations via a collapsible sidebar with real-time history updates.
- **Management**: Interact with conversations through actions like **Delete** and **Rename** (with auto-truncation to 10 words).
- **Model Selection**: Switch between multiple LLMs (llama, Qwen, ..) via a top-right dropdown, with selection persistence across messages and sessions.
- **SPA Experience**: Navigate between chats instantly without full page reloads using HTMX partial updates.
- **Message Actions**: **Copy** (message & code blocks), **Edit**, **Regenerate**, and **Feedback** (Thumbs Up/Down).

## Current Focus & Recent Work
Recent development has introduced a resilient streaming architecture and a comprehensive sidebar system:
1. **Sidebar & SPA Navigation**: 
   - Implemented a persistent, collapsible sidebar (`sidebar.html`) that maintains its state (expanded/collapsed) in `localStorage`.
   - Enabled SPA-style navigation where clicking a conversation in the sidebar loads the history via `/chat/{id}/history` into the main container without a refresh.
2. **Conversation Management**:
   - **Rename**: Added inline title editing using the HTMX `json-enc` extension. Titles are automatically truncated to the first 10 words on the backend.
   - **Delete**: Implemented conversation deletion with real-time sidebar updates via HTMX OOB (Out-of-Band) swaps.
   - **Lazy Creation**: Conversations are only officially created and assigned a UUID after the first user message is sent, updating the URL via `HX-Push-Url`.
3. **Background Generation & Polling**:
   - Decoupled AI generation from the SSE connection. Responses are generated in an `asyncio.create_task` worker.
   - The `/bot-stream` endpoint acts as a state-aware listener, polling the conversation history and yielding updates as they occur in the backend.
4. **Streaming Resumption**:
   - Implemented auto-detection of `streaming` status. If a page is reloaded during generation, the `chat_stream.html` partial is loaded, and the client-side `EventSource` re-connects automatically.
5. **Rendering Pipeline**: 
   - Moved all Markdown, LaTeX, and Syntax Highlighting logic into `static/render.js`.
   - Uses `renderMessageStreaming(el)` for live updates and `renderMessage(el)` for final rendering.
6. **Model Selection & Persistence**:
   - Implemented a model selection dropdown (`model_dropdown.html`) in the top-right header.
   - **Pre-Conversation Selection**: Users can select a model on the landing page before starting a chat; this choice is stored in `localStorage` and sent with the first message.
   - **Dynamic Switching**: Existing conversations can have their model updated via a `PATCH` request, which is reflected immediately in the UI and subsequent bot responses.

## File Structure
```
clean/
├── main.py              # FastAPI backend (Routes, background workers, SSE polling, Rename/Delete logic)
├── static/
│   ├── style.css        # Global CSS (Sidebar animations, scrollbars, Markdown, Glassmorphism)
│   └── render.js        # Rendering helper (Marked, KaTeX, Highlight.js, Copy functionality)
└── templates/
    ├── base.html        # Main layout (Global dependencies, Sidebar container, Main content block)
    ├── sidebar.html     # Sidebar container (Search, New Chat button, History list)
    ├── sidebar_item.html # Individual chat entry (Title, Context Menu, Inline Rename input)
    ├── chat.html        # Chat page container (Messages area and Input field)
    ├── chat_history_list.html # List of message partials for history loading
    ├── chat_input_field.html # Multi-file input form & Hyperscript handling
    ├── chat_response.html # Static message partial (User/Bot styling)
    ├── chat_stream.html # SSE-backed streaming partial for live bot responses
    ├── model_dropdown.html # LLM selection menu and logic
    └── index.html       # Landing page (Initial state & redirection logic)
```

## Technology Stack
- **Backend**: FastAPI (Python)
- **Templating**: Jinja2
- **UI Framework**: Tailwind CSS (via CDN)
- **Interactivity**: HTMX (AJAX, SSE, OOB swaps, `json-enc`) & Hyperscript (Client-side UI logic, toggles)
- **Streaming**: Native Server-Sent Events (SSE)
- **Rendering**: Marked.js (Markdown), KaTeX (LaTeX), Highlight.js (Code Syntax)

## Important Development Rules (LLM Guidelines)
1. **Background Logic**: AI responses must be generated in background tasks. Never block the SSE generator.
2. **SSE Transport**: Always use `json.dumps()` for SSE `data:` payloads to ensure safe transport.
3. **State Resumption**: Always check for messages with `streaming: true` when rendering history to enable UI continuity.
4. **Hyperscript & Data Attributes**: Store multi-line data in `data-message="{{ ... }}"` and access via `my.dataset.message` in Hyperscript.
5. **Horizontal Overflow**: Ensure `pre`, `code`, and `.katex-display` use `overflow-x: auto`.
6. **Rename Feature**: Use `hx-ext="json-enc"` for PATCH requests to the `/chat/{conv_id}` endpoint.
7. **Hyperscript Slashes**: Never use dot notation for Tailwind classes with slashes (e.g., `.bg-black/50`). Use `class '...'` syntax instead to avoid parser errors.

---

*Note: The server is managed by the user. Do not attempt to start or restart the server.*
