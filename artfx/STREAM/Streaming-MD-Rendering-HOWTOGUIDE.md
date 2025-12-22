# Rendering & Streaming How-To Guide

This document codifies the lessons learned from implementing real-time bot streaming. Use these rules to prevent recurring rendering bugs in future projects involving FastAPI, HTMX, and Markdown.

## 1. Streaming Protocol: ALWAYS JSON-Encode SSE Data
**Context**: Server-Sent Events (SSE) are strict line-based protocols. If your data payload contains a newline (e.g., inside an HTML string or a multi-line code block), it breaks the event stream.
**The Mistake**: Sending raw HTML or multi-line text directly in the `data:` field.  
`yield f"data: <div>\nContent\n</div>\n\n"` -> **BROKEN**

**How To**:
1.  **Server**: Wrap your entire payload (string, token, or HTML) in `json.dumps()`.
    ```python
    safe_payload = json.dumps(accumulated_text_or_html)
    yield f"event: token\ndata: {safe_payload}\n\n"
    ```
2.  **Client**: Always parse before using.
    ```javascript
    eventSource.addEventListener('token', (evt) => {
        const text = JSON.parse(evt.data); // Safely restores newlines and special chars
        // ...
    });
    ```

## 2. Text Extraction: Use `textContent`, NOT `innerText`
**Context**: When switching from a "streaming" state to a "final render" state, you often read the current text from the DOM to pass it to a renderer (like Marked.js).
**The Mistake**: Using `el.innerText`. This property returns the *visually rendered* text. If CSS whitespace collapsing is active (default), `innerText` returns "Line 1 Line 2" instead of "Line 1\nLine 2". This permanently destroys formatting.

**How To**:
Always read `el.textContent` to retrieve the raw, uncollapsed source text from the DOM.
```javascript
// BAD: const raw = el.innerText;
const raw = el.textContent; // Returns raw text including \n
el.innerHTML = marked.parse(raw);
```

## 3. Markdown Configuration: Enforce Line Breaks
**Context**: Standard Markdown treats single newlines as spaces. Users in chat interfaces expect single newlines to be line breaks.
**The Mistake**: Leaving the default configuration, causing long, multi-line streaming responses to collapse into a single giant paragraph.

**How To**:
Explicitly configure your Markdown parser to respect breaks.
```javascript
marked.setOptions({
    breaks: true, // Crucial for chat UI
    gfm: true
});
```

## 4. HTML Attributes: Aggressively Escape Multi-line Data
**Context**: Storing message content in data attributes (e.g., for a "Copy" button) is risky if the content contains quotes or newlines.
**The Mistake**: Naive string interpolation.
`<button data-msg="{message}">` -> If message has a quote `"` or newline, the HTML attribute breaks.

**How To**:
1.  **Python Side**: Sanitize specifically for HTML attributes.
    ```python
    # For data attributes, we must escape quotes AND newlines
    safe_msg = html.escape(raw_msg).replace('\n', '&#10;').replace('\r', '').replace('"', '&quot;')
    ```
2.  **Frontend**: Use `getAttribute` (which decodes entities automatically) rather than reading raw HTML.

## 5. Streaming Strategy: Native EventSource > HTMX Extensions
**Context**: HTMX's `sse` extension is great for simple HTML swaps, but struggles with fine-grained control needed for:
- Token-by-token concatenation.
- Live client-side processing (Markdown rendering).
- Handling "Done" events with different logic than "Token" events.

**How To**:
For complex streaming (like Chatbots), use native `EventSource`.
1.  Create a target container in your template.
2.  Use a robust inline script (or module) to manage the `EventSource` lifecycle.
3.  Manually handle `onmessage` (token append) and `close` (cleanup).
