# Architecture Refactoring Plan: Modularization & Extensibility

## 1. Executive Summary
The goal of this refactor is to decompose the current monolithic `main.py` into a structured, tiered architecture. This will separate **Data Models**, **Business Logic (Services)**, and **Interface (Routers)**, making the codebase significantly easier for both human developers and AI agents to understand, extend, and maintain.

## 2. Proposed Directory Structure
We will transition from a flat structure to a standard Python package layout:

```text
clean/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application Entry Point (App Init, Middleware, Mounts)
│   ├── config.py            # Configuration & Constants
│   ├── core/                # Core Infrastructure
│   │   ├── __init__.py
│   │   └── templates.py     # Centralized Jinja2 Template config
│   ├── models/              # Data Definitions (Pydantic & Internal)
│   │   ├── __init__.py
│   │   ├── dtos.py          # Data Transfer Objects (Forms, JSON bodies)
│   │   └── schemas.py       # Internal Data Structures (Chat, Message)
│   ├── services/            # Business Logic (The "Brain")
│   │   ├── __init__.py
│   │   ├── chat_service.py  # Chat CRUD & State Management (encapsulates global store)
│   │   └── llm_service.py   # AI Generation, Streaming Logic, & Background Tasks
│   └── routers/             # HTTP Endpoints (The "Interface")
│       ├── __init__.py
│       ├── navigation.py    # HTML Page Serving (Sidebar, Root, Chat UI)
│       ├── chat.py          # Chat Actions (Send, Rename, Delete)
│       └── streaming.py     # SSE Endpoints
├── static/                  # Unchanged
├── templates/               # Unchanged
└── requirements.txt
```

## 3. Implementation Phases

### Phase 1: Foundation (Models & Core)
**Objective**: Define *what* data we are working with and *how* we render views.
1.  **Models (`app/models/`)**:
    *   Extract `MessageForm` and `RenameModel` to `dtos.py`.
    *   Define proper `Chat` and `Message` TypedDicts or Pydantic models in `schemas.py` to replace implicit dictionary usage.
2.  **Core (`app/core/`)**:
    *   Move `templates = Jinja2Templates(...)` setup to `templates.py`. This ensures one single source of truth for template configuration.

### Phase 2: Logic Extraction (Services)
**Objective**: Isolate complex logic from HTTP handling.
1.  **Chat Service (`app/services/chat_service.py`)**:
    *   Move the global `chats = {}` dictionary here.
    *   Create a class `ChatRepository` or `ChatService` with methods:
        *   `create_conversation() -> str`
        *   `get_conversation(id) -> Chat`
        *   `append_message(id, role, content) -> Message`
        *   `update_title(id, title)`
        *   `delete_conversation(id)`
        *   `get_recent_conversations()`
2.  **LLM Service (`app/services/llm_service.py`)**:
    *   Move `run_chatbot_logic` (background task) here.
    *   Move `generate_bot_response_stream` (SSE generator) here.
    *   This service should interact with `ChatService` to update history, rather than accessing a global variable directly.

### Phase 3: Routing Architecture
**Objective**: Organize endpoints by domain.
1.  **Navigation (`app/routers/navigation.py`)**:
    *   Handlers for `GET /`, `GET /chat/{id}`, `GET /sidebar`, `GET /chat/{id}/history`.
2.  **Chat Actions (`app/routers/chat.py`)**:
    *   Handlers for `POST /chat/{id}/send-message`, `PATCH /chat/{id}`, `DELETE /chat/{id}`.
    *   Inject `ChatService` as a dependency.
3.  **Streaming (`app/routers/streaming.py`)**:
    *   Handler for `GET /bot-stream`.

### Phase 4: Assembly
1.  **Main Entry (`app/main.py`)**:
    *   Initialize `FastAPI`.
    *   Mount `StaticFiles` from `/static`.
    *   Include routers: `app.include_router(navigation.router)`, etc.
    *   Configure middleware (if any).

## 4. Benefits for AI Agents
*   **Reduced Context Load**: An agent working on "fixing the sidebar" only needs to read `navigation.py` and `sidebar.html`, not the entire backend.
*   **Clear Boundaries**: If an agent is asked to "switch the LLM provider", they know exactly where to go (`llm_service.py`) without risking breaking the HTTP routing.
*   **Explicit Typing**: Moving to Pydantic models (`schemas.py`) helps agents understand the shape of data instantly, reducing hallucinated attribute errors.
