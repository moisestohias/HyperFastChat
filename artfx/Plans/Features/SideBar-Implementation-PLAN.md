# Sidebar Implementation Plan

## 1. Project Scope & Objectives
The goal is to enhance the user experience by adding a persistent, collapsible sidebar for conversation management. Key objectives include:
- **Conversation History**: Display all past chats in a sidebar that persists across browsing.
- **Lazy Creation**: Only generate a conversation UUID and update the URL after the first message is sent.
- **Dynamic Interaction**: Load chat history instantly without full page reloads.
- **Management Features**: Implement a context menu for each conversation, starting with "Delete" functionality.
- **Visual Excellence**: Maintain a premium, dark-themed, glassmorphic aesthetic.

## 2. Structural & UI/UX Changes

### 2.1 Sidebar Component
- **State**: Collapsed/Expanded toggled via Hyperscript.
- **Visual Logic (Tailwind)**:
  - **Expanded**: Sidebar has `w-[260px]`, content visible, toggle icon shifts or rotates.
  - **Collapsed**: Sidebar has `w-0` or `hidden` (on mobile) or a narrow `w-16` strip. Content inside is hidden (`opacity-0`).
  - **Toggle Trigger**: A persistent icon button in the top-left area. When collapsed, this icon is the only sidebar-related element visible, or it sits atop the main chat area.
- **Layout**: 
  - **Top Section**: "New Chat" button and primary actions.
  - **Middle Section (at ~30% height)**: Empty container for future Folders/Projects/Pinned features.
  - **Bottom Section**: Recent conversation list.
- **Transitions**: Smooth `transition-all duration-300` for width and `transition-opacity` for interior text.
- **Entries**: 
  - Hover triggers for the "..." context menu button.
  - Selected state styling to indicate the active conversation.

### 2.2 Context Menu
- **Trigger**: Click on the "..." icon.
- **Actions**: Delete (implemented), Share, Pin, Archive (placeholders).
- **Design**: Floating menu with subtle animations and blur effects.

### 2.3 Main Chat Container
- Shifted layout to accommodate the sidebar.
- Responsive design: Sidebar should transition to an overlay on mobile or collapse completely.

## 3. Implementation Steps

### Phase 1: Backend Infrastructure
1.  **Data Structure Update**: 
    - Add `title` and `created_at` fields to the `chats` dictionary entries.
2.  **New Endpoints**:
    - `GET /conversations`: Returns the HTML for the sidebar list.
    - `GET /chat/{conv_id}/content`: Returns only the chat history partial (no base layout).
    - `DELETE /chat/{conv_id}`: Removes the conversation and returns an OOB update to remove the item from the sidebar.
3.  **Route Logic Refactoring**:
    - `/`: Render a landing state with `conversation_id=None` or `new`.
    - `/chat/{conv_id}/send-message`: If `conv_id` is "new", generate a UUID, create the chat entry, and return `HX-Push-Url` along with an OOB update for the sidebar.

### Phase 2: Frontend Implementation (HTML & CSS)
1.  **`templates/sidebar.html`**: Create the main sidebar structure.
2.  **`templates/sidebar_item.html`**: Fragment for a single conversation entry.
3.  **`templates/base.html` / `templates/chat.html`**: 
    - Refactor to include a flex layout: `[Sidebar] [Main Content]`.
    - Add logic to load `/conversations` on page load.
4.  **`static/style.css`**:
    - Sidebar transition animations.
    - Context menu positioning and styling.
    - Collapsed vs. Expanded utility classes.

### Phase 3: Persistence & Interactivity (Hyperscript)
1.  **Sidebar Toggle**: 
    - Use Hyperscript to toggle a `.sidebar-collapsed` class on the body or a wrapper.
    - Example: `on click toggle .w-0 .w-[260px] on #sidebar then toggle .hidden on .sidebar-label`
    - Logic to persist state: `on load if localStorage.sidebarStatus is 'collapsed' add .sidebar-collapsed to #sidebar`.
2.  **Toggle Button**: A fixed-position icon at the top-left (e.g., a "hamburger" or "sidebar" icon) that serves as the universal toggle.
3.  **Chat Loading**: Update sidebar items to use `hx-get` targeting `#chat-messages` (or a sub-container) with `hx-push-url="true"`.
4.  **Context Menu Logic**: Handle click outside to close and placement next to the trigger using Hyperscript's `outside` event.

## 4. Technical Deliverables
- **Codebase Integration**: No breaking changes to the current streaming architecture.
- **Title Generation**: Automated title extraction from the first user message.
- **Delete Logic**: Backend removal followed by frontend DOM removal via HTMX.

## 5. Timeline & Priorities
1.  **P0**: Sidebar structure and persistence of existing chats.
2.  **P0**: Lazy creation and URL updating on first message.
3.  **P1**: Chat history loading via HTMX (SPA-like navigation).
4.  **P1**: Context menu and Delete functionality.
5.  **P2**: Visual polish and micro-animations.
