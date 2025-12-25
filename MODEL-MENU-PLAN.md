# Implementation Plan: LLM Selection Dropdown

This document outlines the plan to implement a model selection dropdown menu in the top-right corner of the chat interface. This feature will allow users to switch which LLM they are communicating with on a per-conversation basis.

## 1. UI/UX Design

### Location
- **Top Right Header**: A sticky or fixed-position header will be added to the main chat area in `templates/chat.html`.
- **Z-Index**: Ensure it stays above the chat messages but below any full-screen overlays (if any).

### Components
- **Dropdown Button**: 
    - Text: Currently selected model name (e.g., "Gemini 1.5 Pro").
    - Icon: A small chevron-down icon.
    - Styling: Semi-transparent background (`bg-zinc-800/50`), backdrop blur, border, and rounded corners (matching the sidebar toggle button).
- **Dropdown Menu**:
    - Appears when the button is clicked.
    - Animation: Fade-in and slide-down (using Tailwind/Hyperscript).
    - Items: List of available models with their friendly names.
    - Selection Indicator: Highlight the current model.

## 2. Integration Steps

### Step 1: Backend Setup (`main.py`)
- Define a dictionary of supported models:
  ```python
  SUPPORTED_MODELS = {
      "gemini-1.5-pro": "Gemini 1.5 Pro",
      "gemini-1.5-flash": "Gemini 1.5 Flash",
      "gpt-4o": "GPT-4o",
      "claude-3-5-sonnet": "Claude 3.5 Sonnet"
  }
  ```
- Update `chats` initialization to include a `model` field.
- Add a route `PATCH /chat/{conv_id}/model` to handle model changes:
  - Updates `chats[conv_id]["model"]`.
  - Returns the updated button HTML or a success status for HTMX to handle.

### Step 2: Template Modifications
- **`templates/chat.html`**:
    - Add a `<header>` element with `position: absolute` or `sticky`, and `top-0`, `right-0`.
    - Include the dropdown logic.
- **`templates/model_dropdown.html` (New)**:
    - Create a partial for the dropdown button and menu to keep `chat.html` clean.
    - Use `hx-patch` on menu items to trigger model updates.

### Step 3: Frontend Interactivity (Hyperscript)
- Use Hyperscript to manage the dropdown's open/closed state:
  ```hyperscript
  on click toggle .hidden on #model-menu
  on click from window if not my.contains(it) add .hidden to #model-menu
  ```
- **New Chat Context**: 
    - When at `/` or a "new" chat state, selecting a model in the dropdown will update a hidden `<input name="model">` within the `#chatForm`.
    - This ensures that the *very first* `POST` to `/chat/new/send-message` includes the user's chosen model.
    - **Persistence**: The selected model ID will also be saved to `localStorage.lastSelectedModel`. On subsequent visits to the landing page, the UI will automatically initialize the dropdown and hidden input to this value.

## 3. State Management

- **Initialization Logic**:
    - **Existing Chats**: The model is retrieved from the `chats[conv_id]["model"]` dictionary.
    - **New Chats**: The model is retrieved from `localStorage.lastSelectedModel` (falling back to "gemini-1.5-flash" if empty).
- **Backend Sync**:
    - For existing chats: `PATCH /chat/{conv_id}/model` updates the DB/memory immediately.
    - For new chats: The selection is transient (client-side only) until the first message is sent.

## 4. Model Switching & Creation Logic

1. **At `/` (New Chat)**:
   - User clicks dropdown -> selects "Claude 3.5 Sonnet".
   - Hyperscript: `set #selected-model-input.value to 'claude-3-5-sonnet'` + `set localStorage.lastSelectedModel to 'claude-3-5-sonnet'`.
   - User sends message.
   - Backend `send_message` receives `form_data.model`.
   - Backend creates `chats[actual_conv_id] = { "model": form_data.model, ... }`.

2. **Inside an Existing Chat**:
   - User clicks dropdown -> selects "GPT-4o".
   - HTMX: `PATCH /chat/{conv_id}/model` -> Backend updates state -> Returns updated dropdown UI.

## 5. Files to be Modified
- `main.py`: Add models, routes, and update data structures.
- `templates/chat.html`: Add the header container.
- `templates/model_dropdown.html`: Create the new dropdown component.
- `static/style.css`: Add minor styling for the dropdown menu (shadows, z-index).

---
*Status: Planned*
