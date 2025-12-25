import uuid
import asyncio

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated

from fastapi.staticfiles import StaticFiles
import html as html_module
import json

templates = Jinja2Templates(directory="templates")
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for conversations
chats = {}

# A class to acts like a Pydantic model but works with Forms
class MessageForm:
    def __init__(
        self,
        message: str = Form(...),
        files: list[UploadFile] = File(default=[]) 
    ):
        self.message = message
        self.files = files

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "conversation_id": "new",
        "history": [],
        "stream_id": str(uuid.uuid4())[:8]
    })

@app.get("/chat/{conv_id}", response_class=HTMLResponse)
async def get_chat(request: Request, conv_id: str):
    # Initialize conversation if it doesn't exist
    if conv_id not in chats:
        chats[conv_id] = {
            "model": "model-name",
            "model_attributes": {
                "temperature": 0.9,
                "top_p": 0.95,
                "max_tokens": 150
            },
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
        "stream_id": str(uuid.uuid4())[:8]
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
            "model": "model-name",
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

    # Render user message
    user_html = templates.get_template("chat_response.html").render({
        "request": request,
        "sender": "user",
        "message": form_data.message,
        "files": processed_files
    })
    
    stream_id = str(uuid.uuid4())[:8]
    
    # Render streaming bot placeholder
    bot_trigger_html = templates.get_template("chat_stream.html").render({
        "request": request,
        "conversation_id": actual_conv_id,
        "stream_id": stream_id
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
    Background task that simulates LLM generation independently of the UI state.
    Updates the conversation history in real-time.
    """
    if conv_id not in chats:
        return
    
    messages = chats[conv_id]["messages"]
    assistant_msg = next((m for m in reversed(messages) if m["role"] == "assistant"), None)
    user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "Hello!")
    
    # Simulate generation
    full_response = user_message
    accumulated = ""
    tokens = full_response.split(" ")
    
    # Simulate thinking
    await asyncio.sleep(0.3)
    
    for token in tokens:
        if accumulated:
            accumulated += " "
        accumulated += token
        
        # Update shared state
        if assistant_msg:
            assistant_msg["content"] = accumulated
            
        # Simulate token delay
        await asyncio.sleep(0.05)
    
    # Mark as complete when finished
    if assistant_msg:
        assistant_msg["status"] = "complete"

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
    done_html = f'<div class="message-actions flex gap-2 opacity-100 pointer-events-auto"><button class="action-btn" title="Copy" data-message="{escaped_message}" _="on click copyMessage(me, my.getAttribute(\'data-message\'))">📋</button><button class="action-btn" title="Regenerate">♻️</button><button class="action-btn" title="Thumbs Up" _="on click toggle .text-green-500">👍</button><button class="action-btn" title="Thumbs Down" _="on click toggle .text-red-500">👎</button></div>'
    
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
    })

    
    input_field_html = templates.get_template("chat_input_field.html").render({
        "request": request,
        "conversation_id": conv_id
    })
    
    return HTMLResponse(content=history_html + f'<div id="chat-form-container" hx-swap-oob="innerHTML">{input_field_html}</div>')

@app.delete("/chat/{conv_id}")
async def delete_chat(conv_id: str):
    if conv_id in chats:
        del chats[conv_id]
    return HTMLResponse(content="")

from pydantic import BaseModel

class RenameModel(BaseModel):
    title: str

@app.patch("/chat/{conv_id}", response_class=HTMLResponse)
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

@app.get("/sidebar", response_class=HTMLResponse)
async def get_sidebar(request: Request, current_id: str = None):
    conv_list = [{"id": cid, "title": data.get("title", "Untitled")} for cid, data in reversed(list(chats.items()))]
    return templates.TemplateResponse("sidebar.html", {
        "request": request,
        "conversations": conv_list,
        "current_id": current_id
    })