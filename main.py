import uuid
import asyncio

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated

from fastapi.staticfiles import StaticFiles
import html as html_module
import json
from LLMConnect.api_client_factory import APIClientFactory, Provider

templates = Jinja2Templates(directory="templates")
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for conversations
chats = {}

def load_providers_config():
    with open("LLMConnect/providers_config.json", "r") as f:
        return json.load(f)

PROVIDERS_CONFIG = load_providers_config()
default_provider = list(PROVIDERS_CONFIG.keys())[1] # groq
default_model = PROVIDERS_CONFIG[default_provider]["default_model"]

# A class to acts like a Pydantic model but works with Forms
class MessageForm:
    def __init__(
        self,
        message: str = Form(...),
        files: list[UploadFile] = File(default=[]),
        provider: str = Form(default_provider),
        model: str = Form(default_model)
    ):
        self.message = message
        self.files = files
        self.provider = provider
        self.model = model

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "conversation_id": "new",
        "history": [],
        "stream_id": str(uuid.uuid4())[:8],
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": default_provider,
        "current_model": PROVIDERS_CONFIG[default_provider]["default_model"]
    })

@app.get("/chat/{conv_id}", response_class=HTMLResponse)
async def get_chat(request: Request, conv_id: str):
    # Initialize conversation if it doesn't exist
    if conv_id not in chats:
        chats[conv_id] = {
            "title": "Untitled",
            "provider": default_provider,
            "model": PROVIDERS_CONFIG[default_provider]["default_model"],
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                }
            ]
        }
    
    # Get messages for rendering (skipping system message for UI)
    ui_messages = [msg for msg in chats[conv_id]["messages"] if msg["role"] != "system"]
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "conversation_id": conv_id,
        "history": ui_messages,
        "stream_id": str(uuid.uuid4())[:8],
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": chats[conv_id].get("provider", default_provider),
        "current_model": chats[conv_id].get("model", "")
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
            "title": title,
            "provider": form_data.provider,
            "model": form_data.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."}
            ]
        }

    if actual_conv_id not in chats:
        return HTMLResponse(content="Conversation not found", status_code=404)

    import base64
    processed_files = []
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
            "active": True
        })
        # We'll use hx-swap-oob to prepend the new conversation to the sidebar list
        response_content += f'<div id="sidebar-list" hx-swap-oob="afterbegin">{sidebar_item_html}</div>'
    
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
        stream = await client.chat(history_to_send, stream=True)
        
        async for chunk in stream:
            accumulated += chunk
            assistant_msg["content"] = accumulated
            # Yield control back to the event loop
            await asyncio.sleep(0)
            
        assistant_msg["status"] = "complete"
            
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
    
    # Send the 'done' event with action buttons
    escaped_message = html_module.escape(final_content).replace('\n', '&#10;').replace('\r', '').replace('"', '&quot;')
    
    # UI Index for this bot response
    bot_msg_index = len([m for m in messages if m["role"] != "system"]) - 1
    
    # We include IDs to target for editing logic
    done_html = f'''
    <button class="action-btn" title="Copy" data-message="{escaped_message}" _="on click copyMessage(me, my.getAttribute('data-message'))">📋</button>
    <button class="action-btn" title="Edit" _="on click
            add .hidden to #message-bubble-{bot_msg_index}
            add .hidden to my parentElement
            remove .hidden from #edit-container-{bot_msg_index}
            focus() on #edit-textarea-{bot_msg_index}">✏️</button>
    <button class="action-btn" title="Regenerate">♻️</button>
    <button class="action-btn" title="Thumbs Up" _="on click toggle .text-green-500">👍</button>
    <button class="action-btn" title="Thumbs Down" _="on click toggle .text-red-500">👎</button>
    '''
    
    yield f"event: done\ndata: {json.dumps(done_html)}\n\n"


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

    model_dropdown_html = templates.get_template("model_dropdown.html").render({
        "request": request,
        "conversation_id": conv_id,
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": chats[conv_id].get("provider", default_provider),
        "current_model": chats[conv_id].get("model", "")
    })
    
    return HTMLResponse(content=history_html + f'<div id="chat-form-container" hx-swap-oob="innerHTML">{input_field_html}</div>' + f'<div id="model-dropdown-container" hx-swap-oob="innerHTML">{model_dropdown_html}</div>')

@app.delete("/chat/{conv_id}")
async def delete_chat(conv_id: str):
    if conv_id in chats:
        del chats[conv_id]
    return HTMLResponse(content="")

from pydantic import BaseModel

class RenameModel(BaseModel):
    title: str

class EditMessageModel(BaseModel):
    content: str

class SetModelModel(BaseModel):
    model: str

class SetProviderModel(BaseModel):
    provider: str

@app.get("/partials/model-options", response_class=HTMLResponse)
async def get_model_options(request: Request, provider: str, current_model: str = None):
    if provider not in PROVIDERS_CONFIG:
        return HTMLResponse(content="Invalid Provider", status_code=400)
    
    models = PROVIDERS_CONFIG[provider]["available_models"]
    
    # We create a simple list of buttons for the model dropdown
    # This is used by the New Chat state to refresh options
    return templates.TemplateResponse("model_options_list.html", {
        "request": request,
        "models": models,
        "current_model": current_model,
        "conversation_id": "new" 
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
    return HTMLResponse(content=new_title)

@app.patch("/chat/{conv_id}/provider", response_class=HTMLResponse)
async def set_provider(request: Request, conv_id: str, data: SetProviderModel):
    if conv_id not in chats:
        return HTMLResponse(content="Not Found", status_code=404)
    
    if data.provider not in PROVIDERS_CONFIG:
        return HTMLResponse(content="Invalid Provider", status_code=400)
    
    chats[conv_id]["provider"] = data.provider
    # Reset to default model for this provider
    chats[conv_id]["model"] = PROVIDERS_CONFIG[data.provider]["default_model"]
    
    return templates.TemplateResponse("model_dropdown.html", {
        "request": request,
        "conversation_id": conv_id,
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": chats[conv_id]["provider"],
        "current_model": chats[conv_id]["model"]
    })

@app.patch("/chat/{conv_id}/model", response_class=HTMLResponse)
async def set_model(request: Request, conv_id: str, data: SetModelModel):
    if conv_id not in chats:
        return HTMLResponse(content="Not Found", status_code=404)
    
    # Validation: model should exist in current provider's list
    provider = chats[conv_id].get("provider", default_provider)
    if data.model not in PROVIDERS_CONFIG[provider]["available_models"]:
         return HTMLResponse(content="Invalid Model", status_code=400)

    chats[conv_id]["model"] = data.model
    
    return templates.TemplateResponse("model_dropdown.html", {
        "request": request,
        "conversation_id": conv_id,
        "providers_config": PROVIDERS_CONFIG,
        "current_provider": provider,
        "current_model": data.model
    })

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
    chats[conv_id]["messages"] = messages[:backend_index + 1]
    
    if role == "user":
        # Add a new streaming assistant placeholder
        chats[conv_id]["messages"].append({
            "role": "assistant",
            "content": "",
            "status": "streaming"
        })
        asyncio.create_task(run_chatbot_logic(conv_id))
    
    # Return full history to refresh the view
    ui_messages = [msg for msg in chats[conv_id]["messages"] if msg["role"] != "system"]
    return templates.TemplateResponse("chat_history_list.html", {
        "request": request,
        "history": ui_messages,
        "conversation_id": conv_id
    })

@app.get("/sidebar", response_class=HTMLResponse)
async def get_sidebar(request: Request, current_id: str = None):
    conv_list = [{"id": cid, "title": data.get("title", "Untitled")} for cid, data in reversed(list(chats.items()))]
    return templates.TemplateResponse("sidebar.html", {
        "request": request,
        "conversations": conv_list,
        "current_id": current_id
    })