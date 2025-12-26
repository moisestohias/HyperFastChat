# Rename Feature Implementation Plan

## 1. Objective
Implement a user-friendly way to rename conversation titles directly from the sidebar. The feature will use an inline input field, persist changes to the backend, and enforce a 10-word limit.

## 2. Backend Implementation
- **New Endpoint**: `PATCH /chat/{conv_id}`
- **Payload**: JSON object `{"title": "New Title"}` (transmitted via HTMX `json-enc` extension).
- **Format Integration**:
    - Add `https://unpkg.com/htmx.org@1.9.10/dist/ext/json-enc.js` as a global script in `base.html`.
    - Use `hx-ext="json-enc"` on the rename input or form.
- **Logic**:
    1. Validate that the conversation exists.
    2. Split the `title` string by whitespace.
    3. Truncate to the first 10 words if necessary.
    4. Update the `chats[conv_id]["title"]` entry in memory.
    5. Return the updated title as a simple string or a rendered partial to update the UI.

## 3. Frontend Implementation (UI/UX)
- **Toggle Rename Mode**: 
    - In `sidebar_item.html`, the "Rename" button in the context menu will trigger Hyperscript to hide the title button and show an input field.
- **Inline Editing**:
    - An `<input type="text">` will appear in place of the title.
    - Styled to match the sidebar aesthetic (transparent background, subtle border).
- **Submission**:
    - **Enter Key**: Triggers `hx-patch` to the backend.
    - **Blur (loss of focus)**: Either cancels the rename or triggers submission (decision: trigger submission for better UX).
    - **Escape Key**: Cancels the rename and restores the old title.
- **Feedback**:
    - The UI updates instantly upon successful response from the server using HTMX.

## 4. Implementation Steps

### Phase 1: Backend
1. Modify `main.py` to add the `@app.patch("/chat/{conv_id}")` route.
2. Implement word truncation logic (keep only first 10 words).

### Phase 2: Frontend Partial Update
1. Modify `templates/sidebar_item.html`:
    - Wrap the title text in a container that can toggle between "View" and "Edit" modes.
    - Add the hidden input field with HTMX and Hyperscript triggers.
    - Update the context menu "Rename" button to trigger the mode change.

### Phase 3: Polish
1. Ensure the input field auto-focuses when "Rename" is clicked.
2. Add a slight transition effect when switching modes.

## 5. Persistence & State
- The backend will update the in-memory `chats` store.
- HTMX will handle the DOM swap to reflect the new title immediately without a page refresh.
