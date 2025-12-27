# Folder System Implementation Plan

## Table of Contents
1. [Overview](#overview)
2. [Data Models](#data-models)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Templates](#frontend-templates)
5. [UI/UX Flow](#uiux-flow)
6. [Edge Cases & Data Integrity](#edge-cases--data-integrity)
7. [Implementation Phases](#implementation-phases)

---

## Overview

This document outlines the complete implementation plan for organizing chat entries using **folders** (chat containers). The system allows users to:
- Create, rename, and delete folders
- Move chats between folders via a context menu
- View unsorted chats in a "Recent" section
- View folder contents in collapsible accordion sections

### Current State
- Chats are stored in a flat `chats` dictionary in `main.py`
- Each chat has: `title`, `provider`, `model`, `messages`
- Sidebar displays all chats in a single "Recent" list
- Context menu exists with Delete, Rename, Pin, Archive actions

### Target State
- Chats have a `folder_id` field (nullable)
- Folders are stored in a separate `folders` dictionary
- Sidebar shows:
  - **Folders section**: Collapsible accordion of user-created folders
  - **Recent section**: Unsorted chats (`folder_id: None`)
- Context menu includes "Move to Folder" submenu with folder list

---

## Data Models

### 1. Conversation (Chat) Model

Update the existing chat structure with additional fields for comprehensive tracking:

```python
# in main.py (or models.py if extracted)
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class InferenceParameters(BaseModel):
    """Parameters controlling LLM inference behavior."""
    context_length: int = 262144
    max_completion_tokens: int = 16384
    temperature: float = 0.7
    top_p: float = 0.95
    # Add more as needed

class Conversation(BaseModel):
    """Complete chat conversation model with folder organization."""
    id: str = Field(..., description="Unique UUID for the conversation")
    title: str = Field(default="Untitled", description="User-visible title, truncated to 10 words")
    messages: list[dict] = Field(default_factory=list, description="List of message objects")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last modification timestamp")
    provider: str = Field(..., description="LLM provider name (e.g., 'groq', 'cerebras')")
    model: str = Field(..., description="Specific model identifier")
    inference_parameters: InferenceParameters = Field(default_factory=InferenceParameters)
    folder_id: Optional[str] = Field(default=None, description="Reference to parent folder, None if unsorted")
    is_pinned: bool = Field(default=False, description="Whether this chat is pinned to top")
    is_archived: bool = Field(default=False, description="Whether this chat is archived")
```

### 2. Folder Model

```python
class Folder(BaseModel):
    """Folder container for organizing conversations."""
    id: str = Field(..., description="Unique UUID for the folder")
    name: str = Field(..., description="User-visible folder name")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    color: Optional[str] = Field(default=None, description="Optional hex color for folder icon")
    icon: Optional[str] = Field(default="folder", description="Icon identifier")
    sort_order: int = Field(default=0, description="Manual sort position")
```

### 3. Data Storage Structure

```python
# Updated in-memory storage
chats: dict[str, Conversation] = {}   # conv_id -> Conversation
folders: dict[str, Folder] = {}       # folder_id -> Folder

# db.json structure (updated)
{
  "chats": {
    "uuid-1": {
      "id": "uuid-1",
      "title": "My Chat",
      "messages": [...],
      "timestamp": "2025-12-27T10:00:00Z",
      "updated_at": "2025-12-27T10:30:00Z",
      "provider": "groq",
      "model": "llama-3.3-70b",
      "inference_parameters": {
        "context_length": 262144,
        "max_completion_tokens": 16384
      },
      "folder_id": "folder-uuid-1",  // or null for unsorted
      "is_pinned": false,
      "is_archived": false
    }
  },
  "folders": {
    "folder-uuid-1": {
      "id": "folder-uuid-1",
      "name": "Work Projects",
      "created_at": "2025-12-25T08:00:00Z",
      "updated_at": "2025-12-26T15:00:00Z",
      "color": "#3B82F6",
      "icon": "folder",
      "sort_order": 0
    }
  }
}
```

---

## Backend Implementation

### 1. Updated Core Imports & Storage (`main.py`)

```python
# Line 20-26 - Update storage initialization
chats: dict = {}
folders: dict = {}
DB_PATH = "db.json"

def read_db_from_disk():
    with open(DB_PATH) as f:
        data = json.load(f)
        return data.get("chats", {}), data.get("folders", {})

chats, folders = read_db_from_disk()

def write_db_to_disk():
    with open(DB_PATH, "wt") as f:
        json.dump({"chats": chats, "folders": folders}, f, indent=2, default=str)
```

### 2. New Pydantic Models for API

```python
# Add after line 468 (existing RenameModel)

class CreateFolderModel(BaseModel):
    name: str

class RenameFolderModel(BaseModel):
    name: str

class MoveChatModel(BaseModel):
    folder_id: Optional[str] = None  # None means "move to Recent/unsorted"
```

### 3. New Folder Endpoints

```python
# -------------------------
# FOLDER MANAGEMENT ROUTES
# -------------------------

@app.post("/folders", response_class=HTMLResponse)
async def create_folder(request: Request, data: CreateFolderModel):
    """Create a new folder and return the updated folders section."""
    folder_id = str(uuid.uuid4())
    folders[folder_id] = {
        "id": folder_id,
        "name": data.name.strip()[:50],  # Limit name length
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "color": None,
        "icon": "folder",
        "sort_order": len(folders)
    }
    write_db_to_disk()
    
    # Return new folder item for OOB injection
    folder_html = templates.get_template("folder_item.html").render({
        "request": request,
        "folder": folders[folder_id],
        "conversations": []  # New folder has no chats
    })
    return HTMLResponse(
        content=f'<div id="folders-list" hx-swap-oob="beforeend">{folder_html}</div>',
        status_code=201
    )


@app.patch("/folders/{folder_id}", response_class=HTMLResponse)
async def rename_folder(folder_id: str, data: RenameFolderModel):
    """Rename an existing folder."""
    if folder_id not in folders:
        return HTMLResponse(content="Folder not found", status_code=404)
    
    folders[folder_id]["name"] = data.name.strip()[:50]
    folders[folder_id]["updated_at"] = datetime.utcnow().isoformat()
    write_db_to_disk()
    
    return HTMLResponse(content=folders[folder_id]["name"])


@app.delete("/folders/{folder_id}", response_class=HTMLResponse)
async def delete_folder(request: Request, folder_id: str, action: str = "unassign"):
    """
    Delete a folder with configurable behavior for contained chats.
    
    Query params:
        action: "unassign" (default) - Move chats to Recent
                "delete" - Delete all chats in folder
    """
    if folder_id not in folders:
        return HTMLResponse(content="Folder not found", status_code=404)
    
    affected_chats = [cid for cid, chat in chats.items() if chat.get("folder_id") == folder_id]
    
    if action == "delete":
        # Delete all chats in this folder
        for cid in affected_chats:
            del chats[cid]
    else:
        # Unassign: move chats to Recent
        for cid in affected_chats:
            chats[cid]["folder_id"] = None
    
    del folders[folder_id]
    write_db_to_disk()
    
    # Return OOB swap to remove folder from DOM and optionally add chats to Recent
    response_html = ""
    if action == "unassign":
        for cid in affected_chats:
            chat_html = templates.get_template("sidebar_item.html").render({
                "request": request,
                "conv_id": cid,
                "title": chats[cid]["title"],
                "active": False
            })
            response_html += f'<div id="sidebar-list" hx-swap-oob="afterbegin">{chat_html}</div>'
    
    return HTMLResponse(content=response_html)


@app.get("/folders/{folder_id}/chats", response_class=HTMLResponse)
async def get_folder_chats(request: Request, folder_id: str):
    """Get all chats within a folder for lazy-loading accordion content."""
    if folder_id not in folders:
        return HTMLResponse(content="Folder not found", status_code=404)
    
    folder_chats = [
        {"id": cid, "title": chat["title"]}
        for cid, chat in chats.items()
        if chat.get("folder_id") == folder_id
    ]
    
    return templates.TemplateResponse("folder_chats_list.html", {
        "request": request,
        "conversations": folder_chats
    })
```

### 4. Move Chat Endpoint

```python
@app.patch("/chat/{conv_id}/folder", response_class=HTMLResponse)
async def move_chat_to_folder(request: Request, conv_id: str, data: MoveChatModel):
    """
    Move a chat to a folder or to Recent (folder_id=None).
    Returns OOB swaps to update the sidebar DOM.
    """
    if conv_id not in chats:
        return HTMLResponse(content="Conversation not found", status_code=404)
    
    if data.folder_id is not None and data.folder_id not in folders:
        return HTMLResponse(content="Folder not found", status_code=404)
    
    old_folder_id = chats[conv_id].get("folder_id")
    new_folder_id = data.folder_id
    
    # No change needed
    if old_folder_id == new_folder_id:
        return HTMLResponse(content="")
    
    chats[conv_id]["folder_id"] = new_folder_id
    chats[conv_id]["updated_at"] = datetime.utcnow().isoformat()
    write_db_to_disk()
    
    # Build OOB response for DOM manipulation
    chat_html = templates.get_template("sidebar_item.html").render({
        "request": request,
        "conv_id": conv_id,
        "title": chats[conv_id]["title"],
        "active": False
    })
    
    response_parts = []
    
    # 1. Remove from old location (old folder or Recent)
    response_parts.append(f'<template id="side-item-{conv_id}" hx-swap-oob="delete"></template>')
    
    # 2. Add to new location
    if new_folder_id is None:
        # Moving to Recent
        response_parts.append(f'<div id="sidebar-list" hx-swap-oob="afterbegin">{chat_html}</div>')
    else:
        # Moving to a folder
        response_parts.append(f'<div id="folder-chats-{new_folder_id}" hx-swap-oob="afterbegin">{chat_html}</div>')
    
    return HTMLResponse(content="".join(response_parts))
```

### 5. Updated Sidebar Endpoint

```python
@app.get("/sidebar", response_class=HTMLResponse)
async def get_sidebar(request: Request, current_id: str = None):
    """Returns the full sidebar with folders and recent chats."""
    
    # Build folder list with their chat counts
    folder_list = []
    for fid, folder in folders.items():
        folder_chats = [cid for cid, chat in chats.items() if chat.get("folder_id") == fid]
        folder_list.append({
            "id": fid,
            "name": folder["name"],
            "color": folder.get("color"),
            "chat_count": len(folder_chats),
            "sort_order": folder.get("sort_order", 0)
        })
    folder_list.sort(key=lambda f: f["sort_order"])
    
    # Build recent (unsorted) chat list
    recent_chats = [
        {"id": cid, "title": data.get("title", "Untitled")}
        for cid, data in chats.items()
        if data.get("folder_id") is None
    ]
    recent_chats.reverse()  # Newest first
    
    return templates.TemplateResponse("sidebar.html", {
        "request": request,
        "folders": folder_list,
        "conversations": recent_chats,
        "current_id": current_id,
        "all_folders": folder_list  # For move-to-folder submenu
    })
```

---

## Frontend Templates

### 1. Updated `sidebar.html`

Create a new sidebar structure with folders section:

```html
<aside id="sidebar"
    class="h-screen bg-[#0d0d0d] flex-shrink-0 flex flex-col border-r border-gray-800 transition-all duration-300 ease-in-out relative z-40 {{ 'sidebar-w-expanded' if not collapsed else 'sidebar-w-collapsed' }}"
    _="on load 
          if localStorage.sidebarStatus is 'collapsed' 
            add .sidebar-w-collapsed to me 
            remove .sidebar-w-expanded from me
            send collapsed to #sidebar-content">

    <div id="sidebar-content"
        class="h-full flex flex-col overflow-hidden {{ 'opacity-0 pointer-events-none' if collapsed else 'opacity-100' }}"
        _="on collapsed 
            add .opacity-0 .pointer-events-none to me 
            remove .opacity-100 from me
          on expanded 
            add .opacity-100 to me 
            remove .opacity-0 .pointer-events-none from me">

        <!-- Top Section: New Chat -->
        <div class="p-3">
            <a href="/"
                class="flex items-center gap-3 w-full px-3 py-3 rounded-xl border border-gray-800 hover:bg-gray-800/50 transition-all text-gray-200 group">
                <svg class="w-5 h-5 text-gray-400 group-hover:text-blue-400" fill="none" stroke="currentColor"
                    viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span class="text-sm font-medium">New Chat</span>
            </a>
        </div>

        <!-- Folders Section -->
        <div class="flex flex-col px-3 gap-1">
            <div class="flex items-center justify-between px-3 mt-2">
                <span class="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Folders</span>
                <button id="create-folder-btn"
                    class="p-1 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
                    title="Create Folder"
                    _="on click
                        remove .hidden from #new-folder-input
                        focus() on #new-folder-input input">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                </button>
            </div>
            
            <!-- New Folder Input (hidden by default) -->
            <div id="new-folder-input" class="hidden px-2 mb-2">
                <input type="text" name="name" placeholder="Folder name..."
                    class="w-full bg-zinc-800 text-sm text-white px-3 py-2 rounded-lg border border-blue-500 outline-none"
                    hx-post="/folders"
                    hx-trigger="keyup[key=='Enter']"
                    hx-ext="json-enc"
                    _="on keyup[key=='Escape'] 
                        add .hidden to #new-folder-input
                        set my value to ''
                      on htmx:afterRequest
                        add .hidden to #new-folder-input
                        set my value to ''">
            </div>
            
            <!-- Folders List -->
            <div id="folders-list" class="space-y-1 max-h-[30vh] overflow-y-auto custom-scrollbar">
                {% for folder in folders %}
                {% include "folder_item.html" %}
                {% endfor %}
            </div>
        </div>

        <!-- Divider -->
        <div class="h-px bg-gray-800 mx-6 my-3"></div>

        <!-- Recent (Unsorted) Section -->
        <div class="flex-1 flex flex-col overflow-hidden">
            <div class="text-[10px] font-bold text-gray-500 uppercase tracking-widest px-6 mb-2">Recent</div>
            <div id="sidebar-list" class="flex-1 overflow-y-auto px-3 space-y-1 custom-scrollbar">
                {% for conv in conversations %}
                {% with conv_id=conv.id, title=conv.title, active=(current_id == conv.id) %}
                {% include "sidebar_item.html" %}
                {% endwith %}
                {% endfor %}
            </div>
        </div>
    </div>
</aside>
```

### 2. New `folder_item.html`

Collapsible folder accordion item:

```html
<div id="folder-{{ folder.id }}" 
    class="group rounded-lg transition-all duration-200"
    data-folder-id="{{ folder.id }}">
    
    <!-- Folder Header -->
    <div class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-zinc-800/50 cursor-pointer transition-colors"
        _="on click
            toggle .hidden on #folder-chats-{{ folder.id }}
            toggle .rotate-90 on #folder-chevron-{{ folder.id }}">
        
        <!-- Chevron -->
        <svg id="folder-chevron-{{ folder.id }}"
            class="w-3 h-3 text-gray-500 transition-transform duration-200"
            fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
        
        <!-- Folder Icon (colored if set) -->
        <svg class="w-4 h-4 {{ 'text-blue-400' if folder.color else 'text-gray-400' }}" 
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
            {% if folder.color %}style="color: {{ folder.color }}"{% endif %}>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        
        <!-- Folder Name -->
        <span id="folder-name-{{ folder.id }}" class="flex-1 text-sm text-gray-300 truncate">
            {{ folder.name }}
        </span>
        
        <!-- Chat Count Badge -->
        <span class="text-xs text-gray-500 bg-zinc-800 px-1.5 py-0.5 rounded-full">
            {{ folder.chat_count }}
        </span>
        
        <!-- Folder Context Menu Trigger -->
        <div class="folder-menu-trigger opacity-0 group-hover:opacity-100 transition-opacity">
            <button class="p-1 hover:bg-zinc-700 rounded text-gray-400 hover:text-white"
                _="on click
                    halt default
                    halt bubbling
                    toggle .hidden on next .folder-context-menu">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM18 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
            </button>
            
            <!-- Folder Context Menu -->
            <div class="folder-context-menu hidden absolute right-2 mt-1 w-36 bg-zinc-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden z-50"
                _="on click elsewhere add .hidden to me">
                
                <button class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-zinc-700 transition-colors"
                    _="on click
                        remove .hidden from #folder-rename-{{ folder.id }}
                        add .hidden to #folder-name-{{ folder.id }}
                        focus() on #folder-rename-{{ folder.id }}
                        add .hidden to my parentElement">
                    Rename
                </button>
                
                <button hx-delete="/folders/{{ folder.id }}?action=unassign"
                    hx-target="#folder-{{ folder.id }}"
                    hx-swap="outerHTML"
                    hx-confirm="Move all chats to Recent and delete this folder?"
                    class="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-400/10 transition-colors">
                    Delete (Keep Chats)
                </button>
                
                <button hx-delete="/folders/{{ folder.id }}?action=delete"
                    hx-target="#folder-{{ folder.id }}"
                    hx-swap="outerHTML"
                    hx-confirm="This will permanently delete the folder AND all chats inside. Are you sure?"
                    class="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-red-500/10 transition-colors">
                    Delete All
                </button>
            </div>
        </div>
    </div>
    
    <!-- Folder Rename Input (hidden) -->
    <input type="text" id="folder-rename-{{ folder.id }}" value="{{ folder.name }}"
        class="hidden w-full bg-zinc-800 text-sm text-white px-3 py-1 mx-3 rounded border border-blue-500 outline-none"
        hx-patch="/folders/{{ folder.id }}"
        hx-trigger="keyup[key=='Enter']"
        hx-target="#folder-name-{{ folder.id }}"
        hx-swap="innerHTML"
        hx-ext="json-enc"
        _="on keyup[key=='Escape'] or blur
            add .hidden to me
            remove .hidden from #folder-name-{{ folder.id }}
          on htmx:afterRequest
            add .hidden to me
            remove .hidden from #folder-name-{{ folder.id }}">
    
    <!-- Folder Chats Container (collapsible, lazy-loaded) -->
    <div id="folder-chats-{{ folder.id }}" 
        class="hidden pl-6 pr-2 space-y-1"
        hx-get="/folders/{{ folder.id }}/chats"
        hx-trigger="intersect once"
        hx-swap="innerHTML">
        <!-- Chats will be loaded here -->
        <div class="text-xs text-gray-600 py-2 animate-pulse">Loading...</div>
    </div>
</div>
```

### 3. New `folder_chats_list.html`

Template for folder chat items:

```html
{% for conv in conversations %}
{% with conv_id=conv.id, title=conv.title, active=False %}
{% include "sidebar_item.html" %}
{% endwith %}
{% endfor %}

{% if not conversations %}
<div class="text-xs text-gray-600 py-2 px-3 italic">No chats in this folder</div>
{% endif %}
```

### 4. Updated `sidebar_item.html`

Add "Move to Folder" submenu to context menu:

```html
<div id="side-item-{{ conv_id }}"
    class="group relative flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 bg-zinc-900 {{ 'bg-zinc-800 text-white' if active else 'text-gray-400 hover:bg-zinc-800/50 hover:text-gray-200' }}"
    data-conv-id="{{ conv_id }}">

    <!-- Title Area (View/Edit) -->
    <div class="flex-1 min-w-0 relative">
        <!-- View Mode: Title Button -->
        <button id="title-btn-{{ conv_id }}" hx-get="/chat/{{ conv_id }}/history" hx-target="#new-messages"
            hx-swap="innerHTML" hx-push-url="/chat/{{ conv_id }}"
            class="w-full text-left text-sm truncate pr-6 focus:outline-none" _="on click
                   remove .bg-zinc-800 .text-white from .group
                   add .bg-zinc-800 .text-white to my parentElement.parentElement">
            {{ title }}
        </button>

        <!-- Edit Mode: Inline Input -->
        <input type="text" name="title" id="rename-input-{{ conv_id }}" value="{{ title }}"
            class="hidden w-full bg-zinc-800 text-sm text-white px-2 py-0.5 rounded border border-blue-500 outline-none"
            hx-patch="/chat/{{ conv_id }}/rename" hx-trigger="keyup[key=='Enter']" hx-target="#title-btn-{{ conv_id }}"
            hx-swap="innerHTML" hx-ext="json-enc" _="on keyup[key=='Escape'] or blur
                 if not #title-btn-{{ conv_id }}.classList.contains('hidden') halt end
                 add .hidden to me
                 remove .hidden from #title-btn-{{ conv_id }}
               on htmx:afterRequest
                 add .hidden to me
                 remove .hidden from #title-btn-{{ conv_id }}
                 set #title-btn-{{ conv_id }}.innerHTML to my value">
    </div>

    <!-- Context Menu Trigger (...) -->
    <div class="context-trigger-container absolute right-2 opacity-0 group-hover:opacity-100 transition-opacity z-50" _="on menuOpened add .opacity-100 .pointer-events-auto to me
            on menuClosed remove .opacity-100 .pointer-events-auto from me">
        <button class="p-1 hover:bg-zinc-700 rounded-md text-gray-400 hover:text-white" _="on click
                 toggle .hidden on next .context-menu
                 if (next .context-menu).classList.contains('hidden')
                   send menuClosed to my parentElement
                 else
                   send menuOpened to my parentElement
                 end
                 halt">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                    d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM18 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
        </button>

        <!-- Context Menu Dropdown -->
        <div class="context-menu hidden absolute right-0 mt-2 w-44 bg-zinc-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden"
            _="on click elsewhere
                 add .hidden to me
                 send menuClosed to my parentElement">
            
            <!-- Move to Folder Submenu -->
            <div class="relative group/move">
                <button class="w-full flex items-center justify-between px-4 py-2 text-sm text-gray-300 hover:bg-zinc-700 transition-colors"
                    _="on click
                        toggle .hidden on next .folder-submenu
                        halt">
                    <span>Move to Folder</span>
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                </button>
                
                <!-- Folder Submenu -->
                <div class="folder-submenu hidden absolute left-full top-0 ml-1 w-40 bg-zinc-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden max-h-60 overflow-y-auto"
                    _="on click elsewhere add .hidden to me">
                    
                    <!-- Move to Recent (None) -->
                    <button hx-patch="/chat/{{ conv_id }}/folder"
                        hx-vals='{"folder_id": null}'
                        hx-ext="json-enc"
                        hx-swap="none"
                        class="w-full text-left px-4 py-2 text-sm text-blue-400 hover:bg-zinc-700 transition-colors border-b border-gray-800">
                        📥 Recent (Unsorted)
                    </button>
                    
                    <!-- Dynamic folder list (injected via context) -->
                    {% for folder in all_folders %}
                    <button hx-patch="/chat/{{ conv_id }}/folder"
                        hx-vals='{"folder_id": "{{ folder.id }}"}'
                        hx-ext="json-enc"
                        hx-swap="none"
                        class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-zinc-700 transition-colors flex items-center gap-2">
                        <span style="color: {{ folder.color or '#9CA3AF' }}">📁</span>
                        <span class="truncate">{{ folder.name }}</span>
                    </button>
                    {% endfor %}
                    
                    {% if not all_folders %}
                    <div class="px-4 py-2 text-xs text-gray-500 italic">No folders yet</div>
                    {% endif %}
                </div>
            </div>
            
            <div class="h-px bg-gray-800"></div>
            
            <button hx-delete="/chat/{{ conv_id }}" hx-target="#side-item-{{ conv_id }}" hx-swap="outerHTML"
                class="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-400/10 transition-colors">
                Delete
            </button>
            <button class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-zinc-700 transition-colors" _="on click
                   add .hidden to #title-btn-{{ conv_id }}
                   remove .hidden from #rename-input-{{ conv_id }}
                   focus() on #rename-input-{{ conv_id }}
                   add .hidden to my parentElement
                   send menuClosed to my parentElement.parentElement">
                Rename
            </button>
            <button
                class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-zinc-700 transition-colors rounded">Pin</button>
            <button
                class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-zinc-700 transition-colors rounded">Archive</button>
        </div>
    </div>
</div>
```

---

## UI/UX Flow

### 1. Creating a Folder
```
User clicks [+] next to "Folders" header
  ↓
Input field slides in with border highlight
  ↓
User types folder name, presses Enter
  ↓
POST /folders with JSON body {name: "..."}
  ↓
Server creates folder, returns OOB swap
  ↓
New folder appears in folders list (accordion collapsed)
  ↓
Input field hides and clears
```

### 2. Moving a Chat to a Folder
```
User hovers over chat item, clicks (...) menu
  ↓
Context menu appears with "Move to Folder" option
  ↓
User hovers/clicks "Move to Folder"
  ↓
Submenu appears with: [📥 Recent] + [📁 Folder1] + [📁 Folder2] ...
  ↓
User clicks target folder
  ↓
PATCH /chat/{conv_id}/folder with JSON {folder_id: "..."}
  ↓
Server updates chat, returns OOB swaps:
  - Delete from current location
  - Insert into target location
  ↓
Chat moves in DOM without page reload
```

### 3. Deleting a Folder
```
User clicks (...) on folder header
  ↓
Folder context menu appears
  ↓
User clicks "Delete (Keep Chats)" or "Delete All"
  ↓
Confirmation dialog appears (hx-confirm)
  ↓
DELETE /folders/{folder_id}?action=unassign|delete
  ↓
Server:
  - If unassign: Updates all chats folder_id=None
  - If delete: Removes all chats
  - Removes folder
  ↓
Returns OOB swaps:
  - Remove folder from DOM
  - If unassign: Add chats to Recent section
```

### 4. Hyperscript Interaction Patterns

```hyperscript
-- Folder Accordion Toggle --
on click
    toggle .hidden on #folder-chats-{folderId}
    toggle .rotate-90 on #folder-chevron-{folderId}

-- Submenu Positioning --
on click
    toggle .hidden on next .folder-submenu
    -- Position submenu to avoid overflow
    if my getBoundingClientRect().right + 180 > window.innerWidth
        add .right-full .left-auto to next .folder-submenu
    end
    halt

-- Close all menus on outside click --
on click elsewhere
    add .hidden to .context-menu
    add .hidden to .folder-submenu
    send menuClosed
```

---

## Edge Cases & Data Integrity

### 1. Moving Chats Between Folders

**Scenario**: User moves chat from Folder A to Folder B
```
Precondition: chat.folder_id = "folder-a"
Action: PATCH /chat/{id}/folder {folder_id: "folder-b"}
Result:
  - chat.folder_id = "folder-b"
  - DOM: Remove #side-item-{id} from #folder-chats-folder-a
  - DOM: Prepend #side-item-{id} to #folder-chats-folder-b
Postcondition: Chat appears only in Folder B
```

**Edge Case**: Target folder doesn't exist
```
Response: 404 "Folder not found"
UI: No DOM changes, show toast notification
```

### 2. Deleting a Folder with Chats

**Option A: Keep Chats (action=unassign)**
```
1. Query all chats where folder_id = target_folder_id
2. Set folder_id = None for each
3. Delete folder from folders dict
4. OOB: Remove folder element from DOM
5. OOB: Prepend each chat to #sidebar-list (Recent)
```

**Option B: Delete All (action=delete)**
```
1. Query all chats where folder_id = target_folder_id
2. Delete each chat from chats dict
3. Delete folder from folders dict
4. OOB: Remove folder element from DOM
5. No need to move chats (they're deleted)
```

### 3. Concurrent Modifications

**Scenario**: Two tabs open, user moves chat in Tab 1
```
Tab 1: Moves chat to Folder B → DOM updates
Tab 2: Still shows chat in original location

Mitigation:
- Server is source of truth (chats dict)
- On next sidebar load (page refresh or navigation), state syncs
- Future: WebSocket broadcast for real-time sync
```

### 4. Folder Name Validation

```python
# In create_folder and rename_folder endpoints
name = data.name.strip()
if not name:
    return HTMLResponse(content="Folder name required", status_code=400)
if len(name) > 50:
    name = name[:50]
# Duplicate names are allowed (use ID for uniqueness)
```

### 5. Orphaned Chats (folder_id points to deleted folder)

```python
# On startup / periodic cleanup
def validate_folder_references():
    for conv_id, chat in chats.items():
        if chat.get("folder_id") and chat["folder_id"] not in folders:
            chat["folder_id"] = None  # Reset to Recent
    write_db_to_disk()
```

### 6. Empty Folders

- Empty folders are allowed and displayed normally
- "No chats in this folder" message shown when expanded
- User can delete empty folders

### 7. New Chat Creation in Folder Context

**Future Enhancement**: If user creates a new chat while viewing a folder:
```
Option A: New chat goes to Recent (current behavior)
Option B: New chat inherits current folder context
         (requires passing folder_id in chat creation)
```

---

## Implementation Phases

### Phase 1: Data Model Migration (Backend)
1. Update `read_db_from_disk()` and `write_db_to_disk()` for new structure
2. Add `folders` dict initialization
3. Add `folder_id` field to chat creation logic
4. Migrate existing chats (set `folder_id = None`)

**Files Modified**:
- `main.py` (lines 20-29, chat creation logic)

### Phase 2: Folder CRUD Endpoints
1. Add Pydantic models (`CreateFolderModel`, `RenameFolderModel`, `MoveChatModel`)
2. Implement `POST /folders` (create)
3. Implement `PATCH /folders/{id}` (rename)
4. Implement `DELETE /folders/{id}` (delete with action param)
5. Implement `GET /folders/{id}/chats` (lazy load)
6. Implement `PATCH /chat/{id}/folder` (move chat)

**Files Modified**:
- `main.py` (add ~100 lines of new endpoints)

### Phase 3: Updated Sidebar Endpoint
1. Update `GET /sidebar` to include folders list
2. Pass `all_folders` context variable for move submenu
3. Build separate `recent_chats` list

**Files Modified**:
- `main.py` (`get_sidebar` function)

### Phase 4: Frontend Templates
1. Update `sidebar.html` with folders section
2. Create `folder_item.html` template
3. Create `folder_chats_list.html` template
4. Update `sidebar_item.html` with move submenu

**Files Created**:
- `templates/folder_item.html`
- `templates/folder_chats_list.html`

**Files Modified**:
- `templates/sidebar.html`
- `templates/sidebar_item.html`

### Phase 5: CSS & Animations
1. Add folder accordion animations
2. Add submenu positioning styles
3. Ensure scrollbar styles apply to folder lists

**Files Modified**:
- `static/style.css`

### Phase 6: Testing & Edge Cases
1. Test folder CRUD operations
2. Test chat movement between folders
3. Test folder deletion (both options)
4. Test concurrent access scenarios
5. Validate data integrity on startup

---

## Summary

| Component | Action | Priority |
|-----------|--------|----------|
| `main.py` storage | Update for folders dict | P0 |
| `main.py` endpoints | Add 5 new routes | P0 |
| `sidebar.html` | Major restructure | P0 |
| `folder_item.html` | Create new | P0 |
| `folder_chats_list.html` | Create new | P1 |
| `sidebar_item.html` | Add move submenu | P0 |
| `style.css` | Add accordion styles | P2 |
| Data validation | Add startup check | P2 |

**Estimated Effort**: 4-6 hours of focused development
**Risk Areas**: OOB swap complexity, submenu positioning edge cases
