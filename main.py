from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated

templates = Jinja2Templates(directory="templates")
app = FastAPI()

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
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/send-message")
async def send_message(request: Request, form_data: Annotated[MessageForm, Depends()]):
    processed_files = []
    for file in form_data.files:
        if file.size > 0:
            processed_files.append({
                "name": file.filename,
                "type": file.content_type,
                "url": "#"
            })
    
    # Render user message
    user_html = templates.get_template("chat_response.html").render({
        "request": request,
        "sender": "user",
        "message": form_data.message,
        "files": processed_files
    })
    
    # Render bot echo response
    bot_html = templates.get_template("chat_response.html").render({
        "request": request,
        "sender": "bot",
        "message": f"Echo: {form_data.message}",
        "files": processed_files,
        "timestamp": "Bot Response"
    })
    
    return HTMLResponse(content=user_html + bot_html)