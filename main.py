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
async def send_message(form_data: Annotated[MessageForm, Depends()]):
    # form_data.message
    for file in form_data.files:
        if file.size > 0:
            print(f"Processing file: {file.filename} ({file.content_type})")
            # content = await file.read() 
    
    return HTMLResponse(content="", status_code=200)