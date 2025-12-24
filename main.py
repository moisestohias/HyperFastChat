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
        "history": ui_messages,
        "stream_id": str(uuid.uuid4())[:8]
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
    
    # Update conversation history with user message and files
    chats[conv_id]["messages"].append({
        "role": "user",
        "content": form_data.message,
        "files": processed_files
    })

    # Add a placeholder assistant message that will be updated during streaming
    chats[conv_id]["messages"].append({
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
    
    # Generate a unique stream ID for this response
    stream_id = str(uuid.uuid4())[:8]
    
    # Return user message and the streaming bot trigger
    bot_trigger_html = templates.get_template("chat_stream.html").render({
        "request": request,
        "conversation_id": conv_id,
        "stream_id": stream_id
    })
    
    # Start the generation in the background so it's not tied to this request or the next SSE request
    asyncio.create_task(run_chatbot_logic(conv_id))
    
    return HTMLResponse(content=user_html + bot_trigger_html)

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
    done_html = f'''
    <button class="action-btn" title="Copy" data-message="{escaped_message}"
        _="on click copyMessage(me, my.getAttribute(\'data-message\'))">
        <span class="material-symbols-rounded">content_copy</span>
    </button>
    <button class="action-btn" title="Regenerate">
        <span class="material-symbols-rounded">refresh</span>
    </button>
    <button class="action-btn" title="Helpful" _="on click toggle .text-blue-600">
        <span class="material-symbols-rounded">thumb_up</span>
    </button>
    <button class="action-btn" title="Not Helpful" _="on click toggle .text-red-600">
        <span class="material-symbols-rounded">thumb_down</span>
    </button>
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