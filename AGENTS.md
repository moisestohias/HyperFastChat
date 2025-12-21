# Comprehensive Context Document: Enhanced Chat Application

## Project Overview
This is a lightweight yet feature-rich chat application built with **FastAPI**, **HTMX**, and **Hyperscript**. It supports multi-file uploads, real-time Markdown rendering, and LaTeX mathematical equations. The application uses a modular template structure and externalized logic to ensure maintainability, performance, and robustness.

## Core Purpose
The application provides a modern, dark-themed chat interface where users can:
- Send text messages with **Markdown** formatting and **Syntax Highlighting** (via Highlight.js).
- Write and render **LaTeX equations** (using `$` for inline and `$$` for block-level expressions).
- Upload and preview **multiple files** (images, PDFs) simultaneously.
- Experience a seamless, "no-refresh" UI powered by HTMX partial updates.
- Manage persistent conversations via unique **UUID-based URLs**.
- Interact with messages through actions like **Copy** (message & code blocks), **Edit**, **Regenerate**, and **Feedback** (Thumbs Up/Down).

## Current Focus & Recent Work
Recent development has stabilized the rendering pipeline and added stateful conversation management:
1. **Rendering Pipeline Optimization**: 
   - Moved all Markdown, LaTeX, and Syntax Highlighting logic from Hyperscript into a dedicated `static/render.js` helper.
   - Implemented an `on load` trigger in `chat_response.html` that calls `renderMessage(me)` for robust asynchronicity.
   - Integrated `highlight.js` with the **Atom One Dark** theme.
2. **Stateful Backend**:
   - Implemented a `chats` dictionary in `main.py` to store conversation history and model attributes.
   - Shifted to UUID-based routing (`/chat/{uuid}`) to support multiple persistent sessions.
3. **Advanced Interactivity**:
   - Added **fixed copy buttons** for code blocks that remain visible during horizontal scrolling.
   - Implemented a secure message-copying system using `data-*` attributes to prevent Hyperscript syntax errors with multi-line strings.
   - Added emoji actions (✏️, 📋, ♻️, 👍, 👎) beneath each message.

## File Structure
```
clean/
├── main.py              # FastAPI backend, UUID routing, & conversation state
├── static/
│   ├── style.css        # Global CSS (Scrollbars, Markdown, Layout, Actions)
│   └── render.js        # Core rendering logic (Marked, KaTeX, Highlight.js, Copy)
└── templates/
    ├── base.html        # Main layout, CDN imports, & global JS state
    ├── chat.html        # Main chat page container
    ├── index.html       # Landing page (initializes history & welcome)
    ├── chat_response.html # Individual message partial (with action buttons)
    └── chat_input_field.html # Input form, multi-file logic, & conversation-aware posting
```

## Technology Stack
- **Backend**: FastAPI (Python)
- **Templating**: Jinja2
- **UI Framework**: Tailwind CSS (Tailwind CDN)
- **Interactivity**: HTMX (AJAX updates) & Hyperscript (Client-side triggers)
- **Rendering**: Marked.js (Markdown), KaTeX (LaTeX), Highlight.js (Code Syntax)

## Important Development Rules (LLM Guidelines)
1. **Hyperscript & Multi-line Strings**: Never pass raw multi-line template variables directly into Hyperscript literals. **Always** store them in `data-message="{{ message }}"` and retrieve them via `my.dataset.message`.
2. **Externalize Complex Logic**: Do not write complex loops or conditionals in `_=""` tags. Call global functions defined in `static/render.js`.
3. **Viewport Integrity**: Never allow `body` or `html` to scroll. Use `overflow: hidden` and `height: 100vh`. All scrolling should be internal.
4. **Horizontal Overflow**: Wrap wide tags (`pre`, `code`, `.katex-display`) in `overflow-x: auto` and ensure parents have `position: relative` for fixed buttons.
5. **Self-Rendering Partials**: When creating or modifying message partials, ensure they call `renderMessage(me)` on load to support HTMX swaps.

---

*Note: The server is managed by the user. Do not attempt to start or restart the server.*
