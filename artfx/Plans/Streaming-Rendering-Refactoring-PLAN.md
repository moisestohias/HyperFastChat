# Refactoring Plan: Client-Side Bot Response Rendering

## Objective
Refactor the bot response streaming workflow to decouple rendering logic from the backend. The server will provide raw data (tokens and completion metadata), and the client will be responsible for rendering the final UI components (Action Buttons, final layout). This reduces server load and bandwidth usage while centralizing UI logic in the frontend.

## Current State Analysis
- **Streaming**: The `/bot-stream` endpoint currently sends raw text tokens (Good).
- **Completion**: The `/bot-stream` endpoint constructs and sends a block of HTML strings (Action Buttons) in the `done` event (Bad - Server Side UI Rendering).
- **Rendering**: Markdown rendering is correctly handled on the client via `render.js`.
- **Interactivity**: Buttons (Copy, Edit) use Hyperscript injected via HTML strings from the server.

## Detailed Refactoring Steps

### 1. Update Backend (`main.py`)
**Goal**: Completely remove HTML string concatenation from the streaming generator.

- **Target Function**: `generate_bot_response_stream` (Lines ~268-321)
- **Specific Changes**:
  1.  **Remove**: Delete the `escaped_message` logic and the `done_html` f-string block (Lines 304-318).
  2.  **Construct Payload**: Create a structured dictionary for the final event.
      ```python
      # Proposed Payload Structure
      final_payload = {
          "status": "done",
          "conversation_id": conv_id,
          "msg_index": bot_msg_index,  # Critical for targeting correct DOM elements
          "content": final_content,     # Raw content for populating edit fields/copy buffers
          "timestamp": datetime.now().isoformat() # Optional but good for future use
      }
      ```
  3.  **Yield JSON**:
      ```python
      yield f"event: done\ndata: {json.dumps(final_payload)}\n\n"
      ```
  4.  **Dependencies**: No new imports needed (`json` is already imported).

### 2. Implement Client-Side Component Renderer (`static/render.js`)
**Goal**: Create a centralized, reusable function to generate the action toolbar.

- **Target File**: `static/render.js`
- **New Function**: `window.renderBotActions(containerEl, convId, msgIndex, content)`
- **Implementation Details**:
  1.  **Sanitization**: Use a helper or regex to escape the `content` string before embedding it in `data-message` attributes to prevent XSS or attribute breaking.
      ```javascript
      const safeContent = content.replace(/"/g, '&quot;').replace(/'/g, "&#39;");
      ```
  2.  **Template Literal**: Use JS Template Literals to recreate the HTML structure currently found in `main.py`.
      - **Copy Button**: Needs `data-message="${safeContent}"` and `_="on click copyMessage(me, ...)"`.
      - **Edit Button**: Needs correct IDs: `#message-bubble-${msgIndex}`, `#edit-container-${msgIndex}`, `#edit-textarea-${msgIndex}`.
      - **Regenerate Button**: Standard static button.
  3.  **Hyperscript Activation**:
      - **Critical Step**: After setting `containerEl.innerHTML`, we **MUST** re-process the new DOM nodes so Hyperscript attaches the event listeners.
      - Code: `if (window._hyperscript) window._hyperscript.processNode(containerEl);`

### 3. Update Client Streaming Logic (`templates/chat_stream.html`)
**Goal**: Switch from expecting HTML to expecting JSON in the 'done' event.

- **Target File**: `templates/chat_stream.html`
- **Event Listener**: `eventSource.addEventListener('done', ...)`
- **Logic Change**:
  1.  **Parse JSON**:
      ```javascript
      const data = JSON.parse(evt.data); // Expecting JSON now
      ```
  2.  **Call Renderer**:
      ```javascript
      window.renderBotActions(actionsEl, data.conversation_id, data.msg_index, data.content);
      ```
  3.  **Fallback**: Add a small check. If `evt.data` starts with `<`, assume it's legacy HTML (for safety during transition, though we are doing a hard switch) or just error out cleanly.
  4.  **Populate Edit Field**: Ensure `document.getElementById('edit-textarea-' + data.msg_index).value = data.content;` is executed using the fresh content from the JSON to ensure exact sync.

### 4. Verification & Testing Plan
- **Pre-Flight Check**: Ensure server is running.
- **Test Case 1: Standard Stream**:
  - Send a message.
  - Watch the stream.
  - **Verify**: At the end, do the "Copy", "Edit", "Regenerate" buttons appear?
  - **Verify**: Click "Edit". Does it toggle the text area? Does the text area contain the full bot response?
  - **Verify**: Click "Copy". Does it copy to clipboard?
- **Test Case 2: Reload & Resume**:
  - Refresh the page while streaming (or after).
  - Ensure the history uses the standard `chat_response.html` (which is server-rendered), but *new* streams use the new logic. Note: `chat_response.html` generates its own buttons server-side. This refactor *only* affects the live streaming component `chat_stream.html`. This is acceptable for now.

## Safety & Rollback
- **Risk**: If `renderBotActions` fails or Hyperscript doesn't attach, buttons won't work.
- **Mitigation**: The `renderBotActions` function will be wrapped in a try-catch block in the event listener.
- **Rollback**: If major issues occur, revert `main.py` to send HTML string and `chat_stream.html` to expect HTML.

## Architectural Note
This change moves us closer to a full "API + Client-Side Rendering" architecture, making it easier to eventually port the frontend to a framework like React or Vue if desired in the future, as the backend becomes purely an API.
