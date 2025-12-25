# HTML Templates Refactoring Plan: Component-Driven Architecture

## 1. Executive Summary
This plan focuses exclusively on the structure and modularity of `.html` template files. The goal is to transition from a "page-centric" mental model to a "component-centric" one. This enhances extend-ability by allowing agents to compose new pages from existing, well-tested building blocks and ensures that HTMX interactions have dedicated, predictable targets.

## 2. Structural Philosophy: Atomic Design for Jinja
We will categorize templates based on their complexity and purpose.

```text
templates/
├── layouts/          # The "Shells" of the application
├── views/            # Full page entry points (HTML responses)
├── components/       # Reusable UI Blocks (Includes)
└── fragments/        # HTMX Partials (Server-returned bits)
```

## 3. Detailed Directory Breakdown

### 3.1 `layouts/`
Contains the overarching HTML structure (`<html>`, `<head>`, `<body>`).
*   **`base.html`**: The single source of truth for CSS/JS imports and meta tags.
*   **`app_shell.html`**: Extends `base.html` to provide the standard application layout (e.g., Sidebar + Main Content Area).

### 3.2 `views/`
These are the files returned by the main GET routes. They mostly "glue" components together.
*   **`home.html`** (was `index.html`): The landing state.
*   **`chat.html`**: The active conversation view.

### 3.3 `components/`
Reusable UI chunks included via `{% include %}`. These should generally **not** contain their own `<script>` tags (logic should be external, as per the Frontend Logic plan).
*   **`sidebar/`**:
    *   `drawer.html`: The container logic for the sidebar.
    *   `nav_item.html` (was `sidebar_item.html`): A single row in the history list.
*   **`chat/`**:
    *   `input_area.html`: The form and textarea.
    *   `welcome_splash.html`: The "No Setup Required" empty state message.
*   **`ui/`**:
    *   `icon.html`: (Optional) SVG definitions or macros to avoid cluttering other files.
    *   `modal.html`: A generic dialog structure.

### 3.4 `fragments/`
These are **critical** for HTMX. They are small, standalone chunks of HTML returned by semantic endpoints (e.g., "append message", "update title").
*   **`message_bubble.html`** (was `chat_response.html`): A single user or bot message.
*   **`stream_chunk.html`** (was `chat_stream.html`): The active cursor/stream container.
*   **`file_preview.html`**: The HTML block for a selected file (extracted from the input form).

## 4. Refactoring Actions

### Action 1: Decoupling the "Input Form"
Currently, `chat_input_field.html` handles form layout, file inputs, AND Hyperscript logic.
*   **Refactor**: Split `chat_input_field.html` into:
    *   `components/chat/input_area.html` (The visuals)
    *   `components/chat/file_preview_item.html` (The template used by JS to render previews)

### Action 2: Standardizing HTMX Targets
*   **Problem**: Agents often guess what ID to target (e.g., `#response-div` vs `#chat-container`).
*   **Solution**: Enforce a naming convention in `layouts/app_shell.html`.
    *   `#main-viewport`: The dynamic content area.
    *   `#sidebar-region`: The persistent rail.
    *   `#modal-layer`: For overlays.

### Action 3: Message Unification
*   **Problem**: `chat_response.html` and `chat_stream.html` share similar styling but duplicate code.
*   **Solution**: Create a `components/chat/message_base.html` that both fragments can include or extend to ensure visual consistency (margins, padding, avatars) is maintained in one place.

## 5. Benefits for Agents
*   **"Edit the Message Style"**: An agent can go directly to `components/chat/message_base.html` and know the change will propagate to both static history and live streams.
*   **"Add a Modal"**: The agent sees `fragments/modal.html` and knows exactly how to structure the HTML response for a dialog.
*   **Clear Boundaries**: Separating `views` from `fragments` clarifies which files are full pages vs. partial updates, preventing "HTML inside HTML" rendering errors.
