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
    
    # Return user message and a trigger for the bot response
    # This initiates a stream via SSE
    bot_trigger_html = f"""
    <div hx-ext="sse" sse-connect="/chat/{conv_id}/bot-stream" sse-swap="message" hx-swap="none"
         class="flex flex-col gap-2 mb-4 items-start w-full"
         _="on htmx:sseMessage(data) call processStreamToken(me, data)
            on htmx:sseAfterMessage if data is '[DONE]' 
              get #chatForm then remove @disabled from it
              get #sendButton then remove .opacity-50 from it then set @disabled to false
            ">
         
         <div class="bg-gray-800 text-gray-100 rounded-t-2xl rounded-br-2xl p-2 shadow-md max-w-[80%] ml-2 border border-gray-700">
             <div class="thinking-indicator flex items-center gap-2 text-gray-400 text-sm animate-pulse mb-1">
                <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>Thinking...</span>
             </div>
             <div class="streaming-content text-sm leading-relaxed whitespace-pre-wrap"></div>
         </div>

         <!-- Message Actions (hidden during stream) -->
         <div class="message-actions hidden ml-2">
             <button class="action-btn" title="Copy" 
                     _="on click copyMessage(me, my.closest('.message-actions').previousElementSibling.querySelector('.streaming-content').dataset.message)">📋</button>
             <button class="action-btn" title="Regenerate">♻️</button>
             <button class="action-btn" title="Thumbs Up" _="on click toggle .text-green-500">👍</button>
             <button class="action-btn" title="Thumbs Down" _="on click toggle .text-red-500">👎</button>
         </div>
    </div>
    """


    
    return HTMLResponse(content=user_html + bot_trigger_html)

@app.get("/chat/{conv_id}/bot-stream")
async def bot_stream(conv_id: str):
    async def event_generator():
        if conv_id not in chats:
            yield "event: message\ndata: Conversation not found\n\n"
            return

        messages = chats[conv_id]["messages"]
        user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "Hello!")
        
        # Initialize assistant message in history immediately
        # This ensures that even if the connection is cut, the message is saved.
        # It also allows for persistence across reloads.
        chats[conv_id]["messages"].append({
            "role": "assistant",
            "content": ""
        })
        msg_index = len(chats[conv_id]["messages"]) - 1
        
        full_response = ""
        # Simulate thinking
        await asyncio.sleep(0.5)
        
        # Split into tokens (characters and spaces) for a smooth typing effect
        import re
        tokens = re.findall(r'\S+|\s+', user_message)
        
        for token in tokens:
            full_response += token
            # Update history incrementally
            chats[conv_id]["messages"][msg_index]["content"] = full_response
            
            # Escape newlines for SSE data field
            safe_token = token.replace("\n", "\\n")
            yield f"event: message\ndata: {safe_token}\n\n"
            await asyncio.sleep(0.02) # Slightly faster for better feel
        
        # Signal end of stream
        yield "event: message\ndata: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/chat/{conv_id}/bot-response")
async def bot_response(request: Request, conv_id: str):
    """ Fallback non-streaming endpoint. """
    if conv_id not in chats:
        return HTMLResponse(content="Conversation not found", status_code=404)
        
    messages = chats[conv_id]["messages"]
    bot_message = next((m["content"] for m in reversed(messages) if m["role"] == "assistant"), "...")

    return templates.TemplateResponse("chat_response.html", {
        "request": request,
        "sender": "bot",
        "message": bot_message,
        "timestamp": "Bot Response"
    })