import uuid
import asyncio
import json

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from fastapi.staticfiles import StaticFiles
from LLMConnect.api_client_factory import APIClientFactory, Provider, PROVIDER_CONFIGS
from datetime import datetime
from typing import Annotated

templates = Jinja2Templates(directory="templates")
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Data Models ---
from models import *

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    model_info = next((m for m in PROVIDERS_CONFIG[default_provider]["models"] if m["id"] == PROVIDERS_CONFIG[default_provider]["default_model"]), None)
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "conversation_id": "new",
        "history": [],
        "stream_id": str(uuid.uuid4())[:8],
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": default_provider,
        "current_model": PROVIDERS_CONFIG[default_provider]["default_model"],
        "current_model_info": model_info,
        "inference_params": InferenceParameters().dict()
    })

@app.get("/chat/{conv_id}", response_class=HTMLResponse)
async def get_chat(request: Request, conv_id: str):
    # Initialize conversation if it doesn't exist
    if conv_id not in chats:
        chats[conv_id] = {
            "id": conv_id,
            "title": "Untitled",
            "provider": default_provider,
            "model": PROVIDERS_CONFIG[default_provider]["default_model"],
            "messages": [
                {
                    "role": "system",
                    "content": DEFAULT_SYSTEM_PROMPT
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "folder_id": None
        }
    
    # Get messages for rendering (skipping system message for UI)
    ui_messages = [msg for msg in chats[conv_id]["messages"] if msg["role"] != "system"]
    
    current_chat = chats[conv_id]
    current_provider = current_chat.get("provider", default_provider)
    current_model_id = current_chat.get("model", "")
    
    # Get current model info from config
    model_info = None
    if current_provider in PROVIDERS_CONFIG:
        model_info = next((m for m in PROVIDERS_CONFIG[current_provider]["models"] if m["id"] == current_model_id), None)

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "conversation_id": conv_id,
        "history": ui_messages,
        "stream_id": str(uuid.uuid4())[:8],
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": current_provider,
        "current_model": current_model_id,
        "current_model_info": model_info,
        "inference_params": current_chat.get("inference_parameters", {})
    })

@app.post("/chat/{conv_id}/send-message")
async def send_message(request: Request, conv_id: str, form_data: Annotated[MessageForm, Depends()]):
    is_new = False
    actual_conv_id = conv_id
    
    if conv_id == "new":
        is_new = True
        actual_conv_id = str(uuid.uuid4())
        # Generate title from first few words
        title = " ".join(form_data.message.split()[:5])
        if len(form_data.message.split()) > 5:
            title += "..."
        
        chats[actual_conv_id] = {
            "id": actual_conv_id,
            "title": title,
            "provider": form_data.provider,
            "model": form_data.model,
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT}
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "folder_id": None
        }

    if actual_conv_id not in chats:
        return HTMLResponse(content="Conversation not found", status_code=404)

    processed_files = []
    if form_data.files:
      import base64
      for file in form_data.files:
          if file.size > 0:
              content = await file.read()
              url = "#"
              if file.content_type.startswith("image/"):
                  base64_image = base64.b64encode(content).decode("utf-8")
                  url = f"data:{file.content_type};base64,{base64_image}"
              
              processed_files.append({
                  "name": file.filename,
                  "type": file.content_type,
                  "url": url
              })
      
    # Update conversation history
    chats[actual_conv_id]["messages"].append({
        "role": "user",
        "content": form_data.message,
        "files": processed_files
    })

    chats[actual_conv_id]["messages"].append({
        "role": "assistant",
        "content": "",
        "status": "streaming"
    })
    write_db_to_disk() # temp only

    # Calculate msg_index for the user message
    # It's at len(messages) - 2 because we just appended user and assistant
    user_msg_index = len(chats[actual_conv_id]["messages"]) - 2

    # Render user message
    user_html = templates.get_template("chat_response.html").render({
        "request": request,
        "sender": "user",
        "message": form_data.message,
        "files": processed_files,
        "msg_index": user_msg_index,
        "conversation_id": actual_conv_id
    })
    
    stream_id = str(uuid.uuid4())[:8]
    
    # Render streaming bot placeholder
    bot_msg_index = len(chats[actual_conv_id]["messages"]) - 1
    bot_trigger_html = templates.get_template("chat_stream.html").render({
        "request": request,
        "conversation_id": actual_conv_id,
        "stream_id": stream_id,
        "msg_index": bot_msg_index
    })
    
    asyncio.create_task(run_chatbot_logic(actual_conv_id))
    
    response_content = user_html + bot_trigger_html
    headers = {}
    
    if is_new:
        # Push new URL and trigger sidebar update
        headers["HX-Push-Url"] = f"/chat/{actual_conv_id}"
        sidebar_item_html = templates.get_template("sidebar_item.html").render({
            "request": request,
            "conv_id": actual_conv_id,
            "title": chats[actual_conv_id]["title"],
            "active": True,
            "all_folders": [f for f in folders.values()]
        })
        # We'll use hx-swap-oob to prepend the new conversation to the sidebar list
        response_content += f'<div id="sidebar-list" hx-swap-oob="afterbegin">{sidebar_item_html}</div>'

        # Also update the input form to point to the new conversation ID (fix for forking bug)
        input_field_html = templates.get_template("chat_input_field.html").render({
            "request": request,
            "conversation_id": actual_conv_id,
            "current_provider": chats[actual_conv_id]["provider"],
            "current_model": chats[actual_conv_id]["model"]
        })
        response_content += f'<div id="chat-form-container" hx-swap-oob="innerHTML">{input_field_html}</div>'

        # Update right sidebar for the new conversation
        right_sidebar_content = templates.get_template("right_sidebar.html").render({
            "request": request,
            "conversation_id": actual_conv_id,
            "providers_config": PROVIDERS_CONFIG,
            "current_provider": chats[actual_conv_id]["provider"],
            "current_model": chats[actual_conv_id]["model"],
            "inference_params": chats[actual_conv_id].get("inference_parameters", {})
        })
        response_content += f'<div id="right-sidebar" hx-swap-oob="innerHTML">{right_sidebar_content}</div>'
    
    return HTMLResponse(content=response_content, headers=headers)

async def run_chatbot_logic(conv_id: str):
    """
    Background task that interacts with LLM providers via LLMConnect.
    Updates the conversation history in real-time as tokens are received.
    """
    if conv_id not in chats:
        return
    
    messages = chats[conv_id]["messages"]
    # Target assistant message is the last message in history (the empty placeholder)
    assistant_msg = next((m for m in reversed(messages) if m["role"] == "assistant"), None)
    
    if not assistant_msg:
        return

    # Simulation setup
    provider_name = chats[conv_id].get("provider", default_provider)
    model_name = chats[conv_id].get("model")

    print(f"\n{'*'*60}")
    print(f"[CHATBOT] Generating response for conversation: {conv_id}")
    print(f"[CHATBOT] Using Provider: {provider_name}")
    print(f"[CHATBOT] Using Model ID: {model_name}")
    print(f"{'*'*60}\n")
    
    try:
        provider = Provider(provider_name)
    except ValueError:
        assistant_msg["content"] = f"Error: Unsupported provider '{provider_name}'"
        assistant_msg["status"] = "error"
        return

    # Initialize LLMConnect client
    try:
        client = APIClientFactory.create_async_client(
            provider=provider,
            model=model_name
        )
    except Exception as e:
        assistant_msg["content"] = f"Error initializing client: {str(e)}"
        assistant_msg["status"] = "error"
        return

    # Prepare historical context (everything except the current streaming placeholder)
    history_to_send = []
    for m in messages:
        if m is assistant_msg:
            continue
        history_to_send.append({"role": m["role"], "content": m["content"]})
    
    try:
        accumulated = ""
        # The chat method is flexible - if passed a list, it treats it as full history
        params = chats[conv_id].get("inference_parameters", {})
        
        stream = await client.chat(
            history_to_send, 
            stream=True,
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 0.95),
            max_tokens=params.get("max_tokens", 4096)
        )
        
        async for chunk in stream:
            accumulated += chunk
            assistant_msg["content"] = accumulated
            # Yield control back to the event loop
            await asyncio.sleep(0)
            
        assistant_msg["status"] = "complete"
        write_db_to_disk() # temp only
    except Exception as e:
        assistant_msg["content"] = f"Error during generation: {str(e)}"
        assistant_msg["status"] = "error"
    finally:
        await client.close()

async def generate_bot_response_stream(conv_id: str):
    """
    SSE stream generator that reflects the current backend state.
    It watches the conversation history and yields updates as they occur.
    """
    if conv_id not in chats:
        yield f"event: error\ndata: Conversation not found\n\n"
        return
    
    # Find the target assistant message in the shared state
    messages = chats[conv_id]["messages"]
    assistant_msg = next((m for m in reversed(messages) if m["role"] == "assistant"), None)
    
    if not assistant_msg:
        yield f"event: error\ndata: Message not found\n\n"
        return

    last_sent_content = None
    
    # Loop while the backend is still generating
    while assistant_msg.get("status") == "streaming":
        current_content = assistant_msg["content"]
        
        # Only send an update if the content has changed
        if current_content != last_sent_content:
            safe_data = json.dumps(current_content)
            yield f"event: token\ndata: {safe_data}\n\n"
            last_sent_content = current_content
            
        await asyncio.sleep(0.05) # Poll the shared state
    
    # Final token update to ensure full content is delivered
    final_content = assistant_msg["content"]
    yield f"event: token\ndata: {json.dumps(final_content)}\n\n"
    
    # UI Index for this bot response
    bot_msg_index = len([m for m in messages if m["role"] != "system"]) - 1
    
    # Send the 'done' event with JSON payload
    payload = {
        "status": "done",
        "conversation_id": conv_id,
        "msg_index": bot_msg_index,
        "content": final_content
    }
    yield f"event: done\ndata: {json.dumps(payload)}\n\n"


@app.get("/chat/{conv_id}/bot-stream")
async def bot_stream(request: Request, conv_id: str):
    """SSE endpoint for streaming bot responses token by token."""
    return StreamingResponse(
        generate_bot_response_stream(conv_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.get("/chat/{conv_id}/history", response_class=HTMLResponse)
async def get_chat_history(request: Request, conv_id: str):
    """Returns only the chat history partial for HTMX SPA navigation."""
    if conv_id not in chats:
        return HTMLResponse(content="Conversation not found", status_code=404)
    
    ui_messages = [msg for msg in chats[conv_id]["messages"] if msg["role"] != "system"]
    
    history_html = templates.get_template("chat_history_list.html").render({
        "request": request,
        "history": ui_messages,
        "conversation_id": conv_id
    })

    input_field_html = templates.get_template("chat_input_field.html").render({
        "request": request,
        "conversation_id": conv_id,
        "current_provider": chats[conv_id].get("provider", default_provider),
        "current_model": chats[conv_id].get("model", "")
    })

    # Update right sidebar content
    provider = chats[conv_id].get("provider", default_provider)
    model_id = chats[conv_id].get("model", "")
    model_info = None
    if provider in PROVIDERS_CONFIG:
        model_info = next((m for m in PROVIDERS_CONFIG[provider]["models"] if m["id"] == model_id), None)

    right_sidebar_html = templates.get_template("right_sidebar.html").render({
        "request": request,
        "conversation_id": conv_id,
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": provider,
        "current_model": model_id,
        "current_model_info": model_info,
        "inference_params": chats[conv_id].get("inference_parameters", {})
    })

    return HTMLResponse(content=history_html + 
                        f'<div id="chat-form-container" hx-swap-oob="innerHTML">{input_field_html}</div>' + 
                        f'<div id="right-sidebar" hx-swap-oob="innerHTML">{right_sidebar_html}</div>')


@app.patch("/chat/{conv_id}/message/{msg_index}", response_class=HTMLResponse)
async def edit_message(request: Request, conv_id: str, msg_index: int, data: EditMessageModel):
    if conv_id not in chats:
        return HTMLResponse(content="Conversation not found", status_code=404)
    
    messages = chats[conv_id]["messages"]
    # UI index 0 is backend index 1 (skipping system)
    backend_index = msg_index + 1
    
    if backend_index < 1 or backend_index >= len(messages):
        return HTMLResponse(content="Invalid message index", status_code=400)
    
    # Update message and remove subsequent ones
    messages[backend_index]["content"] = data.content
    role = messages[backend_index]["role"]
    write_db_to_disk()

    ## Disable discarding previous generated message for not
    # chats[conv_id]["messages"] = messages[:backend_index + 1]
    # if role == "user":
    #     # Add a new streaming assistant placeholder
    #     chats[conv_id]["messages"].append({
    #         "role": "assistant",
    #         "content": "",
    #         "status": "streaming"
    #     })
    #     asyncio.create_task(run_chatbot_logic(conv_id))
    
    # Return full history to refresh the view
    ui_messages = [msg for msg in chats[conv_id]["messages"] if msg["role"] != "system"]
    return templates.TemplateResponse("chat_history_list.html", {
        "request": request,
        "history": ui_messages,
        "conversation_id": conv_id
    })


#  Provider/Model selection --- 
@app.get("/partials/model-list", response_class=HTMLResponse)
async def get_model_list_partial(request: Request, provider: str, conversation_id: str = "new"):
    if provider not in PROVIDERS_CONFIG:
        return HTMLResponse(content="Invalid Provider", status_code=400)
    
    models = PROVIDERS_CONFIG[provider]["models"]
    current_model = ""
    if conversation_id != "new" and conversation_id in chats:
        current_model = chats[conversation_id].get("model", "")

    return templates.TemplateResponse("right_sidebar_model_list.html", {
        "request": request,
        "models": models,
        "current_model": current_model,
        "conversation_id": conversation_id,
        "provider": provider
    })

@app.get("/models/{provider}/{model_id:path}", response_class=HTMLResponse)
async def get_model_details(request: Request, provider: str, model_id: str):
    if provider not in PROVIDERS_CONFIG:
        return HTMLResponse(content="Provider not found", status_code=404)
    
    # URL decode the model_id in case it has special characters
    from urllib.parse import unquote
    model_id = unquote(model_id)
    
    model = next((m for m in PROVIDERS_CONFIG[provider]["models"] if m["id"] == model_id), None)
    if not model:
        print(f"[DEBUG] Model not found: {model_id}")
        print(f"[DEBUG] Available models: {[m['id'] for m in PROVIDERS_CONFIG[provider]['models']]}")
        return HTMLResponse(content="Model not found", status_code=404)
    
    return templates.TemplateResponse("model_details_card.html", {
        "request": request,
        "model": model,
        "provider": provider
    })

@app.patch("/chat/{conv_id}/model", response_class=HTMLResponse)
async def set_model(request: Request, conv_id: str, data: SetModelModel):
    # Special case for "new" conversation - just return success
    # The actual model will be set when the first message is sent
    if conv_id == "new":
        print(f"\n{'='*60}")
        print(f"[MODEL SELECTION] Conversation: new (pre-creation)")
        print(f"[MODEL SELECTION] Selected Model: {data.model_id}")
        print(f"[MODEL SELECTION] This will be used when conversation is created")
        print(f"{'='*60}\n")
        return HTMLResponse(content="OK")
    
    if conv_id not in chats:
        return HTMLResponse(content="Not Found", status_code=404)
    
    provider = chats[conv_id].get("provider", default_provider)
    model_info = next((m for m in PROVIDERS_CONFIG[provider]["models"] if m["id"] == data.model_id), None)
    
    if not model_info:
         return HTMLResponse(content="Invalid Model", status_code=400)

    # DEBUG: Print model selection
    print(f"\n{'='*60}")
    print(f"[MODEL SELECTION] Conversation: {conv_id}")
    print(f"[MODEL SELECTION] Provider: {provider}")
    print(f"[MODEL SELECTION] Previous Model: {chats[conv_id].get('model', 'None')}")
    print(f"[MODEL SELECTION] New Model: {data.model_id}")
    print(f"[MODEL SELECTION] Model Name: {model_info['name']}")
    print(f"{'='*60}\n")

    chats[conv_id]["model"] = data.model_id
    
    # When switching model, also reset parameters to defaults if they match the model
    # (Optional, but good for UX)
    # chats[conv_id]["inference_parameters"] = model_info["default_parameters"].copy()
    
    write_db_to_disk()
    
    # Return empty response since UI is updated via Hyperscript
    return HTMLResponse(content="OK")

@app.patch("/chat/{conv_id}/provider", response_class=HTMLResponse)
async def set_provider(request: Request, conv_id: str, data: SetProviderModel):
    if conv_id not in chats:
        return HTMLResponse(content="Not Found", status_code=404)
    
    if data.provider_id not in PROVIDERS_CONFIG:
        return HTMLResponse(content="Invalid Provider", status_code=400)
    
    chats[conv_id]["provider"] = data.provider_id
    # Reset to default model for this provider
    new_model_id = PROVIDERS_CONFIG[data.provider_id]["default_model"]
    chats[conv_id]["model"] = new_model_id
    
    write_db_to_disk()
    
    # Trigger a full reload of the sidebar content for this chat
    sidebar_content = templates.get_template("right_sidebar.html").render({
        "request": request,
        "conversation_id": conv_id,
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": data.provider_id,
        "current_model": new_model_id,
        "inference_params": chats[conv_id].get("inference_parameters", {})
    })
    
    return HTMLResponse(content=sidebar_content)


@app.patch("/chat/{conv_id}/inference-params", response_class=HTMLResponse)
async def update_inference_params(conv_id: str, data: InferenceParamsModel):
    if conv_id not in chats:
        return HTMLResponse(status_code=404)
    
    params = chats[conv_id].setdefault("inference_parameters", {})
    for field, value in data.dict(exclude_none=True).items():
        params[field] = value
    
    write_db_to_disk()
    return HTMLResponse(content="OK")

@app.post("/chat/{conv_id}/inference-params/reset")
async def reset_inference_params(request: Request, conv_id: str):
    if conv_id not in chats:
        return HTMLResponse(status_code=404)
        
    provider = chats[conv_id].get("provider")
    model_id = chats[conv_id].get("model")
    
    model = next((m for m in PROVIDERS_CONFIG[provider]["models"] if m["id"] == model_id), None)
    if not model:
        return HTMLResponse(content="Model not found", status_code=404)

    chats[conv_id]["inference_parameters"] = model["default_parameters"].copy()
    write_db_to_disk()
    
    return templates.TemplateResponse("inference_params_form.html", {
        "request": request,
        "conversation_id": conv_id,
        "params": chats[conv_id]["inference_parameters"],
        "supported_parameters": model.get("supported_parameters", [])
    })

@app.get("/partials/model-options", response_class=HTMLResponse)
async def get_model_options(request: Request, provider: str, current_model: str = None):
    if provider not in PROVIDERS_CONFIG:
        return HTMLResponse(content="Invalid Provider", status_code=400)
    
    models = PROVIDERS_CONFIG[provider]["models"]
    
    # This is used by the New Chat state to refresh options
    return templates.TemplateResponse("model_options_list.html", {
        "request": request,
        "models": models,
        "current_model": current_model,
        "conversation_id": "new" 
    })

# Side bar--- 
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
        for cid, data in reversed(list(chats.items()))
        if data.get("folder_id") is None
    ]
    
    return templates.TemplateResponse("sidebar.html", {
            "request": request,
            "folders": folder_list,
            "conversations": recent_chats,
            "current_id": current_id,
            "all_folders": folder_list  # For move-to-folder submenu
        })

@app.patch("/chat/{conv_id}/rename", response_class=HTMLResponse)
async def rename_chat(conv_id: str, data: RenameModel):
    if conv_id not in chats:
        return HTMLResponse(content="Not Found", status_code=404)
    
    # Truncate to 10 words
    words = data.title.split()
    new_title = " ".join(words[:10])
    if len(words) > 10:
        new_title += "..."
        
    chats[conv_id]["title"] = new_title
    write_db_to_disk()
    return HTMLResponse(content=new_title)

@app.delete("/chat/{conv_id}")
async def delete_chat(conv_id: str):
    if conv_id in chats:
        del chats[conv_id]
        write_db_to_disk()
    return HTMLResponse(content="")

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
        remaining_folders = [f for f in folders.values()]
        for cid in affected_chats:
            chat_html = templates.get_template("sidebar_item.html").render({
                "request": request,
                "conv_id": cid,
                "title": chats[cid]["title"],
                "active": False,
                "all_folders": remaining_folders
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
        "conversations": folder_chats,
        "all_folders": [f for f in folders.values()]
    })

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
        "active": False,
        "all_folders": [f for f in folders.values()] # Need folders for context menu in new location
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