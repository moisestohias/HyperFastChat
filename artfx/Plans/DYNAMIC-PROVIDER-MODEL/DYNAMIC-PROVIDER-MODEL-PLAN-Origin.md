# Implementation Plan: Dynamic Provider & Model Dropdowns

This plan outlines the steps to upgrade the model selection system to load configuration from `providers_config.json` and implement a two-step selection process (Provider -> Model).

## 1. Backend: Configuration & State

### 1.1 Load Configuration
- **File**: `main.py`
- **Action**: 
    - At the module level (or app startup), read `providers_config.json`.
    - Parse it into a global `PROVIDERS_CONFIG` dictionary.
    - Validate/Clean the JSON (handle potential trailing commas if necessary, or assume valid).

### 1.2 Update State Management
- **Chats Dictionary**: 
    - Update the chat object structure to store `provider` in addition to `model`.
    - Example: `chats[conv_id] = { "provider": "groq", "model": "llama-3.1-70b", ... }`.
- **Defaults**:
    - When creating a chat, if no provider is specified, pick the first available or a specific default (e.g., `aimlapi`).
    - Use `default_model` from the provider config when switching providers if no specific model is requested.

### 1.3 Endpoints
- **GET `/partials/model-options`**:
    - Query Params: `provider`, `current_model` (optional).
    - Returns: HTML for the Model dropdown list (buttons) populated from the config.
    - Usage: Used by the "New Chat" state to dynamically update options without persisting.
- **PATCH `/chat/{conv_id}/provider`**:
    - Body: `{"provider": "groq"}`.
    - Logic: Update chat's provider, reset chat's model to provider's default.
    - Returns: Updated `model_dropdown.html` (both dropdowns) reflecting the new state.
- **PATCH `/chat/{conv_id}/model`**:
    - Logic: Update chat's model.
    - Returns: Updated `model_dropdown.html` (to reflect selected state).

## 2. Frontend: UI Components

### 2.1 Refactor `templates/model_dropdown.html`
- **Structure**:
    - Split into two distinct sections/buttons within the container:
        1.  **Provider Selector**: Shows current provider name.
        2.  **Model Selector**: Shows current model name.
    - Container should be flex: `flex items-center gap-2`.

- **Dropdown Logic (Hyperscript)**:
    - Maintain standard "click" -> "toggle .hidden" logic for menus.
    - Ensure clicking one closes the other (exclusive open).

### 2.2 Provider Menus
- **Provider Menu**:
    - Iterates over `PROVIDERS_CONFIG.keys()`.
    - **Existing Chat**: `hx-patch="/chat/{id}/provider"`.
    - **New Chat**: 
        - Hyperscript/HTMX hybrid:
        - Use `hx-get="/partials/model-options?provider={{ key }}"` targeting `#model-list-container`.
        - Hyperscript to update the visible button text and `localStorage.lastProvider`.

### 2.3 Model Menus
- **Model Menu**:
    - Container `#model-list-container`.
    - Populated dynamically.
    - **Existing Chat**: `hx-patch="/chat/{id}/model"`.
    - **New Chat**:
        - Hyperscript to update hidden input `#selected-model-input`.
        - Update visible button text.
        - Update `localStorage.lastModel`.

## 3. Implementation Steps

1.  **Backend Config**: Implement `load_config()` in `main.py`.
2.  **Endpoints**: Add `/partials/model-options` and update `PATCH` routes.
3.  **Template**: Rewrite `model_dropdown.html` to support the two-column layout.
4.  **New Chat Logic**: Ensure `chat_input_field.html` hidden inputs support both fields (maybe just model is enough if model implies provider? No, better to send both to avoid ambiguity).
    - *Correction*: If `SUPPORTED_MODELS` is no longer a flat global, we must send provider + model or ensure model IDs are globally unique. The config shows overlapping names? No, mostly scoped. But safer to send `provider` and `model`.
    - **Action**: Add `<input type="hidden" name="provider">` to `chat_input_field.html`.

## 4. Updates to Persistence (LocalStorage)
- We need to store:
    - `lastSelectedProvider`
    - `lastSelectedModel`
- On load (New Chat):
    - Read `lastSelectedProvider`.
    - If valid, render that provider selected.
    - Fetch/Render model list for that provider.
    - Select `lastSelectedModel` if it exists in that list, else default.

## 5. Constraint Checklist & Rules
- **Minimize JS**: Use HTMX for fetching lists. Use Hyperscript for UI toggles.
- **Provider Config**: Load once at startup.
- **Hyperscript Rules**: 
    - No slashed classes in dot notation (use `class '...'`).
    - Use `on click elsewhere`.

---
*Status: Planned*
