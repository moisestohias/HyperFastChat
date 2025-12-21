import uuid
import asyncio

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
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
    
    # Return user message and a trigger for the bot response
    # This delegates the bot logic to a separate request to allow for async delay
    bot_trigger_html = f"""
    <div hx-get="/chat/{conv_id}/bot-response" 
         hx-trigger="load" 
         hx-swap="outerHTML">
         <div class="flex items-center gap-2 text-gray-400 text-sm animate-pulse ml-2 mb-4">
            <div class="w-2 h-2 bg-gray-400 rounded-full"></div>
            <span>Thinking...</span>
         </div>
    </div>
    """
    
    return HTMLResponse(content=user_html + bot_trigger_html)

async def generate_bot_response(conv_id: str):
    """ Delegated bot logic: waits 1 second, updates history, and returns the response. """
    await asyncio.sleep(1)
    if conv_id not in chats:
        return None
        
    # Find the last message from user to echo it
    messages = chats[conv_id]["messages"]
    user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "Hello!")
    
    bot_message = user_message
    
    # Update conversation history with assistant message
    chats[conv_id]["messages"].append({
        "role": "assistant",
        "content": bot_message
    })
    
    return bot_message

@app.get("/chat/{conv_id}/bot-response")
async def bot_response(request: Request, conv_id: str):
    bot_message = await generate_bot_response(conv_id)
    
    if bot_message is None:
        return HTMLResponse(content="Conversation not found", status_code=404)

    return templates.TemplateResponse("chat_response.html", {
        "request": request,
        "sender": "bot",
        "message": bot_message,
        "timestamp": "Bot Response"
    })