# Comprehensive Context Document: Enhanced Chat Application

## Project Overview
This is a lightweight yet feature-rich chat application built with **FastAPI**, **HTMX**, and **Hyperscript**. It supports multi-file uploads, real-time Markdown rendering, and LaTeX mathematical equations. The application uses a modular template structure and externalized styling to ensure maintainability and performance.

## Core Purpose
The application provides a modern, dark-themed chat interface where users can:
- Send text messages with **Markdown** formatting (code blocks, lists, bold/italics).
- Write and render **LaTeX equations** (using `$` for inline and `$$` for block-level expressions).
- Upload and preview **multiple files** (images, PDFs) simultaneously.
- experience a seamless, "no-refresh" UI powered by HTMX partial updates.

## Current Focus & Recent Work
Recent development has focused on enhancing the richness of message content and UI stability:
1. **Markdown & LaTeX Integration**: Implemented self-contained rendering logic in chat partials using `marked.js` and `KaTeX`.
2. **Scrollbar & Layout Optimization**: Resolved "double scrollbar" issues by locking the viewport (`100vh`) and implementing specialized horizontal overflow handling for wide equations and code blocks.
3. **Architectural Refactoring**: 
   - Moved from a monolithic `index.html` to a modular system of partials (`base.html`, `chat.html`, `chat_response.html`, `chat_input_field.html`).
   - Externalized styles into `static/style.css` and configured FastAPI static file mounting.
   - Refactored message rendering to use individual Hyperscript `on load` triggers for robust asynchronous rendering.

## File Structure
```
clean/
├── main.py              # FastAPI app, static mounting, & message handlers
├── static/
│   └── style.css        # Global styles (Scrollbars, Markdown, LaTeX blocks)
└── templates/
    ├── base.html        # Main layout, CDN imports (KaTeX, Marked, HTMX)
    ├── chat.html        # Main chat page container
    ├── index.html       # Landing page (inherits chat)
    ├── chat_response.html # Individual message partial (handles own rendering)
    └── chat_input_field.html # Input form, multi-file logic, & preview
```

## Technology Stack
- **Backend**: FastAPI (Python)
- **Templating**: Jinja2
- **UI Framework**: Tailwind CSS (Tailwind CDN)
- **Interactivity**: HTMX (AJAX updates) & Hyperscript (Client-side logic)
- **Rendering**: Marked.js (Markdown) & KaTeX (LaTeX)

## Important Development Rules (LLM Guidelines)
1. **Viewport Integrity**: Never allow `body` or `html` to scroll. Use `overflow: hidden` and `height: 100vh`. All scrolling should be internal.
2. **Horizontal Overflow**: Always wrap wide tags (`pre`, `code`, `.katex-display`) in `overflow-x: auto` to prevent them from breaking the message bubble width.
3. **Modular CSS**: Add new global styles to `static/style.css` rather than using inline `<style>` blocks in templates.
4. **Self-Rendering Partials**: When creating or modifying message partials, ensure they trigger their own rendering logic (Markdown/LaTeX) `on load` to support HTMX swaps.

---

*Note: The server is managed by the user. Do not attempt to start or restart the server.*
