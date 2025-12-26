# Implementation Plan: Dynamic Provider & Model Dropdowns

This plan outlines the steps to upgrade the model selection system to load configuration from `providers_config.json` and implement a two-step selection process (Provider -> Model).

## 1. Backend: Configuration & State

### 1.1 Load Configuration
- **File**: `main.py`
- **Action**: 
### Step 1: Backend Setup (`main.py`)
- **JSON Loading**:
    - Function `load_providers_config()`:
        - Read `providers_config.json`.
        - **Critical**: The provided JSON has trailing commas (e.g., line 128 `],`). use `json.loads` inside a try/except block. If standard JSON fails, read file as string, use `re.sub(r',(\s*?[\]}])', r'\1', content)` to remove trailing commas before parsing.
    - Store in global `PROVIDERS_CONFIG`.
    - Create a helper `get_provider_models(provider_name)` returns the list `available_models`.

- **State Updates**: 
    - `chats[conv_id]` structure:
      ```python
      {
          "provider": "groq", # New field
          "model": "llama-3.1-70b-versatile",
          # ... existing fields
      }
      ```
    - `MessageForm`: Update to accept `provider: str = Form(...)` and `model: str = Form(...)`.

- **New/Updated Routes**:
    1.  **`GET /partials/model-options`**:
        - Params: `provider: str`, `current_model: str = None`.
        - Logic: Fetch models from config for `provider`.
        - Template: Render *just* the list of `<button>` elements for the model dropdown.
    2.  **`PATCH /chat/{conv_id}/provider`**:
        - Body: `ProviderModel` (pydantic).
        - Logic: Only update `chats[id]["provider"]`. Reset `chats[id]["model"]` to that provider's `default_model`.
        - Response: Re-render the *entire* `model_dropdown.html` partial to update both buttons.
    3.  **`PATCH /chat/{conv_id}/model`**:
        - Body: `SetModelModel` (pydantic).
        - Logic: Update `chats[id]["model"]`.
        - Response: Re-render `model_dropdown.html`.

### Step 2: Template Architecture (`templates/model_dropdown.html`)
- **Layout**: 
    - `<div class="flex items-center gap-2">` wrapper.
    - **Dropdown 1 (Provider)**:
        - Button shows `config[current_provider].name`.
        - On Click: Toggle `#provider-menu`.
        - Menu Items: Loop `PROVIDERS_CONFIG`.
        - **Action**:
            - *Existing Chat*: `hx-patch="/chat/{id}/provider"` target `#model-dropdown-container`.
            - *New Chat*: Hyperscript logic.
                - `set #selected-provider-input.value to '{{ key }}'`
                - `put '{{ name }}' into #provider-btn-text`
                - Trigger an HTMX get to `/partials/model-options` to refresh the *second* dropdown's content.
    - **Dropdown 2 (Model)**:
        - Button shows `current_model`.
        - On Click: Toggle `#model-menu`.
        - Content Container: `<div id="model-list-container">`.
        - Default Content: Rendered server-side for current state.
        
### Step 3: "New Chat" Interactivity Details
- **Problem**: Changing provider client-side must update the model list client-side without persisting to DB.
- **Solution**:
    - The Provider buttons in "New Chat" mode will have:
      `hx-get="/partials/model-options?provider={{ key }}"`
      `hx-target="#model-list-container"`
    - Hyperscript on Provider Button:
      ```hyperscript
      on click 
        add .hidden to #provider-menu
        set #selected-provider-input.value to '{{ key }}'
        set localStorage.lastSelectedProvider to '{{ key }}'
        put '{{ name }}' into #provider-btn-span
      ```
    - **Hidden Inputs**:
      - Separate inputs for provider and model in `chat_input_field.html`.

### Step 4: LocalStorage & Initialization
- **`templates/model_dropdown.html` Script Block**:
    - Check `localStorage.lastSelectedProvider`.
    - If it exists and we are in "New Chat" mode:
      1. Update hidden input `#selected-provider-input`.
      2. Update Provider Button text.
      3. **Crucial**: Trigger an HTMX request to fetch the correct model list for this cached provider.
      
## 3. Implementation Steps

1.  **Backend Config**: Implement `load_config()` in `main.py`.
2.  **Endpoints**: Add `/partials/model-options` and update `PATCH` routes.
3.  **Template**: Rewrite `model_dropdown.html` to support the two-column layout.
4.  **New Chat Logic**: Ensure `chat_input_field.html` hidden inputs support both fields (`provider` and `model`).
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
*Status: Ready for Review*
