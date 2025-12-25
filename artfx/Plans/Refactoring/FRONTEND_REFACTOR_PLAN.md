# Frontend Refactoring Plan: Logic Modularization & Extensibility

## 1. Executive Summary
This plan focuses on **code-level modularity** rather than just file organization. The goal is to decouple the monolithic JavaScript and inline template logic into distinct, reusable modules. This ensures that agents can modify a specific behavior (e.g., "change how LaTeX renders") without parsing unrelated code (e.g., "UI copy buttons").

## 2. Refactoring JavaScript Logic (`static/js/`)

We will transition from a single `render.js` to a modular architecture using ES6 Modules (or namespaced objects if build tools are absent).

### 2.1 Core Modules (`static/js/core/`)
These modules handle pure logic and configuration, independent of the DOM.
*   **`markdown.js`**: Contains the `marked` library configuration (GFM, breaks). Extruding this allows agents to easily swap markdown parsers or add extensions.
*   **`latex.js`**: Wraps `katex` configuration (delimiters, error handling).
*   **`highlighter.js`**: precise configuration for `highlight.js`, decoupled from the rendering loop.

### 2.2 Feature Modules (`static/js/features/`)
These modules handle specific UI interactions.
*   **`code-blocks.js`**: Only logic related to transforming `<pre>` tags, injecting "Copy" buttons, and handling their click events.
*   **`file-upload.js`**: Extracts the currently inline `FileReader` logic from `chat_input_field.html`. It should expose a simple class like `new FilePreviewer('#input', '#preview-container')`.
*   **`clipboard.js`**: A generic utility for `navigator.clipboard` interactions with fallback handling.

### 2.3 The Orchestrator (`static/js/app.js`)
*   Imports the above modules.
*   Exposes a clean `window.App.renderMessage(el)` API.
*   Why? The calling code (HTMX) doesn't need to know *how* rendering works, just that it *should* render.

## 3. Refactoring Template Logic (Hyperscript & Inline JS)

We will reduce the cognitive load of inline scripts by creating **Defined Behaviors**.

### 3.1 Extracting Inline Scripts
*   **Problem**: `chat_input_field.html` contains a large `<script>` block for file previews.
*   **Solution**: Move this to `static/js/features/file-upload.js` and initialize it via a flexible data attribute, e.g., `<input type="file" data-behavior="file-preview">`.

### 3.2 Standardizing Hyperscript
*   **Problem**: Logic like "auto-resize textarea" is hardcoded in `_=""` attributes.
*   **Solution**: Define "Hyperscript Behaviors" in a global file or use a standardized set of utility classes.
    *   *Example*: Instead of writing the full resize logic inline, use `_="install AutoResize"`.

## 4. Implementation Priorities

1.  **Split `render.js`**: This is the highest friction point.
    *   Create `static/js/core/` and `static/js/features/`.
    *   Refactor `render.js` to import/use these files.
    *   *Agent Benefit*: An agent asked to "fix a LaTeX rendering bug" now edits a 20-line `latex.js` file instead of searching through a 160-line mixed file.

2.  **Clean `chat_input_field.html`**:
    *   Extract the file preview logic.
    *   *Agent Benefit*: The HTML becomes purely structural, making it easier for agents to redesign the UI without breaking functionality.

3.  **Unify Streaming Logic**:
    *   Currently, `renderMessage` and `renderMessageStreaming` duplicate config.
    *   Refactor to share the core configuration modules (`markdown.js`, `latex.js`).

## 5. Resulting Architecture for Agents
When an agent needs to add a feature, they follow this widely understood pattern:
1.  **Logic**: specific logic goes into `static/js/{category}/{feature}.js`.
2.  **View**: UI goes into `templates/components/{feature}.html`.
3.  **Glue**: Connect them using a simple data attribute or ID.

This separation of concerns allows "coding agents" to work safely within boundaries, drastically reducing the risk of regression errors.
