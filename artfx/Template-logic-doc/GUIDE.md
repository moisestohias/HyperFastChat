# Chat Application Template Guide

## Overview

This document explains how the template system works in the chat application, covering the relationship between the templates and their integration with the FastAPI backend.

## Template Structure

The application uses a hierarchical template structure:

1. `base.html` - The root template that includes all necessary CSS/JS dependencies
2. `chat.html` - Extends `base.html` and provides the chat interface layout
3. `index.html` - Extends `chat.html` and handles the chat history rendering

### Template Files

- `base.html`: Contains the HTML skeleton, head section with all dependencies (HTMX, hyperscript, Tailwind CSS, Markdown renderer, LaTeX renderer, syntax highlighter)
- `chat.html`: Provides the chat interface structure with message display area and input field
- `index.html`: Implements the logic to render conversation history, handling both regular messages and streaming messages
- `chat_response.html`: Renders individual user/bot messages with styling and action buttons
- `chat_stream.html`: Handles streaming responses with Server-Sent Events (SSE) and real-time updates
- `chat_input_field.html`: Provides the message input form with file upload capabilities

## Template Integration with FastAPI

### Backend Setup

In `main.py`, the application sets up Jinja2 templates:

```python
templates = Jinja2Templates(directory="templates")
```

### Route Handling

- The `/chat/{conv_id}` endpoint initializes conversations and renders `index.html` with conversation data
- The `send_message` endpoint processes form submissions, updates conversation state, and returns rendered HTML fragments
- The `bot_stream` endpoint provides an SSE stream for real-time message updates

### Message Flow

1. User sends a message through the HTMX-powered form
2. FastAPI processes the request, updates in-memory conversation state
3. The response includes rendered HTML for the user's message and the streaming container
4. Background task simulates LLM generation, updating the shared state
5. SSE endpoint streams token updates to the client
6. Client-side JavaScript updates the UI in real-time as tokens arrive

## Streaming Functionality

The streaming implementation uses:

1. **EventSource API**: Client-side JavaScript creates an EventSource connection to the SSE endpoint
2. **Server-Sent Events**: The `bot_stream` endpoint continuously sends token updates with the accumulated content
3. **State Management**: A background task updates the conversation state in real-time while generation occurs
4. **Real-time Updates**: The UI updates as new content is received, with a pulsing cursor during streaming
5. **Final Processing**: When streaming completes, action buttons are shown and full Markdown/TeX processing occurs

## Features

- Real-time streaming responses with visual feedback
- File upload support with preview
- Markdown rendering in messages
- LaTeX mathematical expression support
- Syntax highlighting for code blocks
- Message action buttons (copy, regenerate, feedback)
- Auto-scrolling to new messages
- Responsive design with Tailwind CSS

## Key Dependencies

- HTMX for AJAX requests and DOM updates
- hyperscript for client-side scripting
- Tailwind CSS for styling
- Marked.js for Markdown rendering
- KaTeX for LaTeX rendering
- Highlight.js for code syntax highlighting
- EventSource for Server-Sent Events