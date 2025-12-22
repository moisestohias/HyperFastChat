# Streaming Implementation History

This document outlines the various strategies and implementations we have experimented with to achieve real-time streaming for bot responses in the FastAPI + HTMX application.

## Goal
Implement a "typing effect" for bot responses where tokens appear in real-time. The content must support:
- Markdown rendering (Bold, Italic, Headings, Lists)
- LaTeX equations (MathCyl)
- Syntax Highlighting (Highlight.js)
- Multi-line text

## Approach 1: HTMX SSE Extension
We initially attempted to use the standard `hx-ext="sse"` to handle the stream.

### Implementation
- **Backend**: Endpoint `/chat/{id}/bot-stream` yielding standard SSE events.
- **Frontend**: Used `sse-connect` and `sse-swap="beforeend"` on a container.

### Challenges encountered
1. **Data Format**: HTMX provides the best experience when swapping HTML fragments. However, creating valid HTML fragments for *partial* markdown tokens is impossible (e.g., you can't send an unclosed `<b>` tag easily without breaking the DOM parser).
2. **Swap Logic**: `beforeend` appending of raw text works, but breaks Markdown rendering, which requires the *context* of the whole string to parse correctly (e.g., to know if a `*` is a bullet point or italic marker).

## Approach 2: Native EventSource with Full Accumulation (Server-Side)
To solve the parsing context issue, we switched to sending the **full accumulated text** with every token, rather than just the new chunk.

### Implementation
- **Backend**: Generator maintains `accumulated` string. Each event sends the *entire* message so far.
- **Protocol**: `event: token`, `data: <JSON-encoded-string>`. used JSON to safely transport newlines and special characters.

### Rendering Strategy
- **Frontend**: A custom script using `new EventSource()`:
    1.  Listens for `token` event.
    2.  Updates `innerText` with the new full content.
    3.  Immediately calls `marked.parse()` and `renderMathInElement()` to re-render the preview.

### Issues
- **Flickering**: Re-rendering the entire DOM tree 10-20 times a second caused visual jitters, especially with complex LaTeX or Code blocks.
- **Broken HTML during generation**: This was the critical failure properly identified. If the bot generates a code block:
    ```markdown
    Here is a code block:
    ```python
    def main():
    ```
    At this exact moment, the markdown parser sees an **unclosed** code block. It often treats the *rest of the available document* (including the cursor) as code, or fails to render the HTML structure correctly, causing the chat bubble to look broken until the final closing ``` arrives.

## Approach 3: "Safe" Text Streaming (Deferred Rendering)
To fix the "broken HTML" issue during generation, we moved to a two-phase rendering approach.

### Implementation
1.  **Phase 1 (Streaming)**:
    - Receive token.
    - **Do NOT** parse Markdown.
    - Simply escape HTML characters (`<`, `>`) and replace newlines `\n` with `<br>`.
    - Inject this "safe" HTML into the bubble.
    - *Result*: User sees the raw tokens appear with correct line breaks, but no bold/headings/colors yet.
2.  **Phase 2 (Completion)**:
    - Receive `done` event.
    - Take the raw text and run the full `renderMessage()` pipeline (Marked + KaTeX + Highlight.js).
    - *Result*: The message "snaps" into its final formatted state.

### Current Status
This is the active implementation. While stable (no broken HTML), it lacks the "wow" factor of seeing bold text or code highlighting appear in real-time. It renders as plain text until the stream finishes.

## Important Configurations
- **Marked.js**: Enabled `breaks: true` option. Standard Markdown requires double-newlines for a paragraph break. Users often type single newlines expecting a break. This configuration aligns the rendering with user expectations for chat interfaces.
