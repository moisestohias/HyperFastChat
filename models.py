from pydantic import BaseModel, Field
from fastapi import UploadFile, File, Form
from datetime import datetime
from typing import Optional
import json

# --- temp fix
from LLMConnect.api_client_factory import PROVIDER_CONFIGS

# In-memory storage
chats: dict[str, dict] = {}
folders: dict[str, dict] = {}
DB_PATH = "db.json"

def read_db_from_disk():
    try:
        with open(DB_PATH, "r") as f:
            data = json.load(f)
            # Handle old format where it was just the chats dict
            if isinstance(data, dict) and "chats" in data:
                return data.get("chats", {}), data.get("folders", {})
            return data, {} # Old format
    except (FileNotFoundError, json.JSONDecodeError):
        return {}, {}

chats, folders = read_db_from_disk()

def write_db_to_disk():
    with open(DB_PATH, "wt") as f:
        json.dump({"chats": chats, "folders": folders}, f, indent=2, default=str)
# ---
from dataclasses import asdict
# Convert ProviderConfigs to dict for compatibility with existing template logic
PROVIDERS_CONFIG = {p.value: asdict(config) for p, config in PROVIDER_CONFIG_S.items()} if 'PROVIDER_CONFIG_S' in locals() else {p.value: asdict(config) for p, config in PROVIDER_CONFIGS.items()}


default_provider = list(PROVIDERS_CONFIG.keys())[1] # groq
default_model = PROVIDERS_CONFIG[default_provider]["default_model"]
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."

# ---

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

class InferenceParameters(BaseModel):
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: Optional[int] = None
    max_tokens: int = 4096
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

class Conversation(BaseModel):
    id: str
    title: str = "Untitled"
    messages: list[dict] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str
    model: str
    inference_parameters: InferenceParameters = Field(default_factory=InferenceParameters)
    folder_id: Optional[str] = None
    is_pinned: bool = False
    is_archived: bool = False

class Folder(BaseModel):
    id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    color: Optional[str] = None
    icon: Optional[str] = "folder"
    sort_order: int = 0

class InferenceParamsModel(BaseModel):
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

class RenameModel(BaseModel):
    title: str

class CreateFolderModel(BaseModel):
    name: str

class RenameFolderModel(BaseModel):
    name: str

class MoveChatModel(BaseModel):
    folder_id: Optional[str] = None  # None means "move to Recent/unsorted"

class SetModelModel(BaseModel):
    model_id: str

class SetProviderModel(BaseModel):
    provider_id: str

class EditMessageModel(BaseModel):
    content: str