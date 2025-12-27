# Folders-Plan.md

Purpose
- Define a complete implementation plan to add "Folders" (chat containers) to the project.
- Cover data model, backend API, UI/partials changes, Hyperscript interactions, SSE/HTMX flows, edge cases, migration and testing, and an ordered implementation checklist with rough effort estimates.

Summary
- Add a `Folder` entity and extend existing chat entries with `folder_id: str | None`.
- Provide CRUD endpoints for folders, and an endpoint to move a conversation into/out of a folder.
- Update sidebar partials so folders appear as top-level groups and chats can be moved between folders via a "Move to…" context menu on each chat entry.
- Use HTMX for partial updates and OOB swaps; use Hyperscript for local UI interactions such as toggling the move menu and inline folder creation.
- Default deletion behavior: reassign contained chats to `None` (Recent). Optionally support deleting contained chats with an explicit flag/confirm.

1) Data model
- New Pydantic model: `Folder`
  - Fields:
    - `id: str` — UUID
    - `name: str`
    - `created_at: datetime`
    - `order: int | None` — optional user-specified ordering (optional)
- Extend chat entry model (existing `ChatEntry` or similar) to include:
  - `folder_id: str | None` — `None` indicates the conversation is unorganized and should appear in "Recent"
- Storage
  - In-memory dicts for dev:
    - `CONVERSATIONS: dict[str, ChatEntry]`
    - `FOLDERS: dict[str, Folder]`
  - Persist the same schema to your persistent store (JSON file, DB table, etc.). Ensure existing conversations get `folder_id = None` if missing.

2) Backend API
- Routes to add (REST-style / HTMX-friendly responses):
  - `GET /folders`
    - Returns list of folders (used to render dropdowns and sidebar)
  - `POST /folders` (body: { "name": str })
    - Create a folder. Validate non-empty name, unique name (optional). Return the created folder.
    - Response should support HTMX partial consumption (e.g., return the sidebar fragment for OOB swap).
  - `PATCH /folders/{folder_id}` (body: { "name": str })
    - Rename folder. Return updated folder/partials.
  - `DELETE /folders/{folder_id}` ?query param: `reassign=true|false` or `delete_chats=true`
    - Default `reassign=true`: set `folder_id` = `None` for contained chats.
    - If `delete_chats=true`, delete contained chats (dangerous; confirm in UI).
    - Return updated sidebar partials (OOB) and status.
  - `PATCH /chat/{conv_id}/folder` (body: { "folder_id": str | null })
    - Move a chat to a folder or to `null` (Recent).
    - On success, return:
      - HTMX OOB swap for the updated sidebar fragments (Recent and target folder lists)
      - A small JSON fragment or partial confirming success (so the context menu can close).
- Response conventions
  - Follow project rules for SSE: use `json.dumps()` for any SSE payloads.
  - For HTMX responses, return partial templates (HTML) for the updated lists so the frontend can swap them OOB.
  - Include `HX-Push-Url` if necessary when navigating into a folder view.

3) Templates / partials updates
- Files to update:
  - `templates/sidebar.html`
    - Add a "Folders" area above or below "Recent".
    - Render list of folders (each folder can expand/collapse to show its chats).
    - Add an action to create a new folder (inline + hyperscript).
  - `templates/sidebar_item.html`
    - Update chat item to include move context menu trigger (three-dot menu).
    - Include an OOB-able fragment id for the chat entry so it can be removed/inserted without full reload.
  - `templates/chat_history_list.html`
    - When viewing a folder-specific URL (`/folder/{id}` or `/chat?folder={id}`), render only chats with `folder_id` matching.
  - New partial: `templates/folder_list_partial.html` (optional but recommended)
    - Renders the entire folders block (list of folders each with its chat entries).
    - Return this fragment for OOB swaps on folder create/rename/delete/move.
  - New partial: `templates/move_menu_partial.html` (optional)
    - Renders the move dropdown (list of folders + "Recent" option + "Create new folder…").
- Rendering considerations
  - Make all updated sidebar fragments have stable element IDs so HTMX OOB swaps replace only the intended areas.
  - When moving a chat email/entry, do an OOB swap that:
    - Removes the chat element from its old parent list (if visible).
    - Inserts/Prepends a chat element into the target folder's list if that folder is currently visible in the sidebar.
    - Updates counts shown next to folder labels if you display counts.

4) UI: Move context menu & Hyperscript
- UI behavior:
  - Each chat item has a context/menu button -> opens a dropdown with:
    - A list of existing folders (rendered from `GET /folders`)
    - "Recent" option to unassign
    - "Create new folder" field inline (text input + create button)
  - Selecting a folder calls `PATCH /chat/{conv_id}/folder` with `{ folder_id }` via HTMX (`hx-patch`) OR sends a small AJAX/HTMX request and expects OOB sidebar partial updates.
- Hyperscript usage (for local interactions):
  - Use Hyperscript to:
    - Toggle the dropdown: `on click toggle .open` or `on click find .move-menu toggle` (avoid dot notation issues per project rules).
    - Bind the inline "Create new folder" input so pressing Enter triggers a `POST /folders` (HTMX).
    - Close the menu after a successful move using Hyperscript or HTMX response handling: use `hx-on` or `on htmx:afterOnLoad` to remove `.open`.
  - Example behaviors (descriptive):
    - Menu open/close: `on click add .open to my.closest('.chat-item') then add event listener outside click to remove .open` — implement with Hyperscript idioms already used in the project.
    - Inline create: input has `hx-post="/folders" hx-vals='{"name": this.value}' hx-target="#oob-folder-list" hx-swap="outerHTML swap:oob"` plus `hx-ext="json-enc"` if needed for JSON encoding.
- Accessibility:
  - Ensure menu is keyboard accessible and focus is moved appropriately.

5) HTMX & OOB flow examples
- When user selects "Move to Folder A" on chat X:
  - Client sends `PATCH /chat/{X}/folder` with `folder_id=A` (HTMX).
  - Server performs update and returns:
    - `204` or small JSON confirming success (HTMX will process).
    - In addition, return OOB fragments:
      - `#sidebar-recent` outerHTML replacement (to remove chat X if visible)
      - `#folder-A-list` outerHTML replacement (to insert chat X into folder A if visible)
      - Optionally update `#sidebar-folders` full fragment
- If the user is currently viewing a folder page:
  - And the chat is moved into that folder -> the main message list may need insertion. Provide an endpoint or OOB partial to insert the chat in the main container as well.

6) Edge cases & rules
- Moving between folders:
  - Always atomically update `conv.folder_id`. Return the updated conversation and updated sidebar fragments so client displays the change.
  - Ensure duplicate moves (race) are handled: use server-side last-write-wins semantics, with timestamps to detect stale update attempts and return 409 if necessary.
- Deleting folders:
  - Default behavior: set `folder_id = None` for all contained chats and return updated sidebar fragments.
  - Optional flag `delete_chats=true`: delete contained chats — require strong confirmation in UI (two-step modal).
  - If a folder being viewed is deleted and the user is on `/folder/{id}`, respond with a redirect or message to navigate back to Recent or homepage.
- Rename collisions:
  - If unique folder names are required, validate on `POST`/`PATCH` and return 400 on conflicts.
- Data integrity:
  - Validate `folder_id` on `PATCH /chat/{conv}/folder` — return 404 if folder doesn't exist (unless `null`).
  - When deleting a folder, ensure database transaction-style behavior (change contained chats & remove folder) or equivalent atomic update.
- Concurrency:
  - Add a `updated_at` timestamp to conversation metadata; use optimistic concurrency (if desired) for move operations.
- Performance:
  - If there are many conversations in a folder, load only the first N in the sidebar, with a "Show more" action.

7) Migration plan
- Add `folder_id` field to persisted conversations, defaulting to `null` for existing entries.
- Create folders table/collection as needed.
- Provide a one-off script to migrate any external metadata into the new folder structure if the user already has categorization.

8) Testing
- Unit tests:
  - Folder create / rename / delete flows.
  - Move chat to folder; verify folder counts, `folder_id`, and partials returned.
  - Deleting folder with `reassign=true` and `delete_chats=true`.
- Integration tests:
  - Sidebar partial OOB replacement after folder actions.
  - Hyperscript menu open/close and inline create flows (could be done with headless browser tests).
- Manual test checklist:
  - Create folder, rename, delete (reassign and delete-contained).
  - Move chat from Recent -> Folder A -> Folder B -> Recent.
  - Reload page during streaming generation: ensure `streaming` messages with `folder_id` render correctly and sidebar remains consistent.

9) Implementation checklist (ordered)
- [ ] Add `Folder` Pydantic model and `folder_id` field to `ChatEntry` (1 day)
- [ ] Update storage layer and migration script to add `folder_id` to existing items (0.5 day)
- [ ] Add endpoints: `GET /folders`, `POST /folders`, `PATCH /folders/{id}`, `DELETE /folders/{id}`, `PATCH /chat/{id}/folder` (1.5 days)
  - Ensure responses return HTMX-friendly partials or OOB fragments.
- [ ] Create partial `folder_list_partial.html` and update `sidebar.html` and `sidebar_item.html` to render folder groups and move menu (1.5 days)
- [ ] Add Hyperscript interactions for the move menu and inline folder creation (0.5 day)
- [ ] Wire HTMX OOB swaps in backend to update sidebar fragments on folder/chats moves (1 day)
- [ ] Add tests & migration validation (1 day)
- [ ] Manual QA & polish (0.5 day)
- Estimated total: ~7–8 days for a single developer (range depends on current code complexity and persistence layer).

10) UX notes / optional improvements
- Drag-and-drop reordering of chats into folder categories (future).
- Drag to reorder folders (requires `order` field).
- Pinning of folders to top.
- Folder-specific settings: color, emoji icon, privacy flags (future).

Appendix: UI fragment id conventions (examples)
- `#sidebar-recent` — Recent list outer container
- `#sidebar-folders` — Entire folders block
- `#folder-{id}-list` — list container for a specific folder (used for OOB swap)
- `#chat-item-{conv_id}` — chat list item element id for targeted removal/insertion

Final notes
- Keep background generation behavior unchanged; ensure folder metadata is part of conversation records returned by SSE when streaming so a resumed stream renders under the correct folder context.
- Use HTMX OOB swaps to keep SPA behavior consistent and avoid full page reloads.
- Prefer reassigning chats to `null` on folder delete as the safe default; provide an explicit "delete contained chats" option for users that want it.
