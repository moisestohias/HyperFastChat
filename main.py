import uuid
import asyncio

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated

from fastapi.staticfiles import StaticFiles

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
    return RedirectResponse(url=f"/chat/{uuid.uuid4()}", status_code=303)

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
        "history": ui_messages
    })

@app.post("/chat/{conv_id}/send-message")
async def send_message(request: Request, conv_id: str, form_data: Annotated[MessageForm, Depends()]):
    if conv_id not in chats:
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
    
    # Update conversation history with user message
    chats[conv_id]["messages"].append({
        "role": "user",
        "content": form_data.message
    })

    # Render user message
    user_html = templates.get_template("chat_response.html").render({
        "request": request,
        "sender": "user",
        "message": form_data.message,
        "files": processed_files
    })
    
    # Generate a unique stream ID for this response
    stream_id = str(uuid.uuid4())[:8]
    
    # Return user message and the streaming bot trigger
    bot_trigger_html = templates.get_template("chat_stream.html").render({
        "request": request,
        "conversation_id": conv_id,
        "stream_id": stream_id
    })
    
    return HTMLResponse(content=user_html + bot_trigger_html)

async def generate_bot_response_stream(conv_id: str):
    """
    Async generator that yields SSE events with accumulated tokens.
    Each event contains the full message so far, enabling live rendering.
    """
    import html as html_module
    import json
    
    if conv_id not in chats:
        yield f"event: error\ndata: Conversation not found\n\n"
        return
    
    # Find the last message from user to echo it (simulating bot response)
    messages = chats[conv_id]["messages"]
    user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "Hello!")
    
    # Simulate token-by-token generation
    # In real implementation, this would be replaced with LLM streaming
    full_response = user_message
    accumulated = ""
    
    # Simulate some "thinking" delay
    await asyncio.sleep(0.3)
    
    # Split response into tokens (words for simulation)
    tokens = full_response.split(" ")
    
    for i, token in enumerate(tokens):
        # Add space between tokens (except for first token)
        if accumulated:
            accumulated += " "
        accumulated += token
        
        # SSE data must be single line - encode newlines
        # Use JSON encoding to safely handle all special characters
        safe_data = json.dumps(accumulated)
        yield f"event: token\ndata: {safe_data}\n\n"
        
        # Simulate token generation delay
        await asyncio.sleep(0.05)
    
    # Update conversation history with complete message
    chats[conv_id]["messages"].append({
        "role": "assistant",
        "content": accumulated
    })
    
    # Yield final 'done' event with action buttons HTML (single line for SSE)
    escaped_message = html_module.escape(accumulated).replace('\n', '&#10;').replace('"', '&quot;')
    done_html = f'<div class="message-actions opacity-100 pointer-events-auto"><button class="action-btn" title="Copy" data-message="{escaped_message}" _="on click copyMessage(me, my.getAttribute(\'data-message\'))">📋</button><button class="action-btn" title="Regenerate">♻️</button><button class="action-btn" title="Thumbs Up" _="on click toggle .text-green-500">👍</button><button class="action-btn" title="Thumbs Down" _="on click toggle .text-red-500">👎</button></div>'
    
    yield f"event: done\ndata: {done_html}\n\n"


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


@app.get("/chat/{conv_id}/bot-response")
async def bot_response(request: Request, conv_id: str):
    """Legacy non-streaming endpoint (kept for compatibility)."""
    if conv_id not in chats:
        return HTMLResponse(content="Conversation not found", status_code=404)
    
    # Find the last message from user to echo it
    messages = chats[conv_id]["messages"]
    user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "Hello!")
    
    await asyncio.sleep(0.5)
    
    bot_message = user_message
    
    # Update conversation history
    chats[conv_id]["messages"].append({
        "role": "assistant",
        "content": bot_message
    })

    return templates.TemplateResponse("chat_response.html", {
        "request": request,
        "sender": "bot",
        "message": bot_message,
        "timestamp": "Bot Response"
    })