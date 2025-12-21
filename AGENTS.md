# Comprehensive Context Document: File Upload Chat Application

## Project Overview

This is a lightweight file upload chat application built with FastAPI that allows users to send messages combined with file attachments. The application features a modern chat-like interface with real-time file preview capabilities and uses HTMX for seamless client-server interactions without traditional page reloads.

## Purpose and Functionality

The application serves as a simple chat UI that enables users to:
- Type and send text messages
- Upload various file types (images, PDFs, etc.)
- View live previews of selected files before sending
- Process both message content and file uploads on the backend

## File Structure

```
clean/
├── main.py          # Backend FastAPI application
└── templates/
    └── index.html   # Frontend chat interface
```

The project follows a simple two-tier structure with a clear separation between backend logic (Python/FastAPI) and frontend presentation (HTML/CSS/JS).

## Backend Architecture (main.py)

### Key Components
- **UploadFile/File**: FastAPI's file upload utilities
- **Form**: For handling form data

### Endpoints
- **Message Endpoint (`/send-message`)**
   - Accepts POST requests with multipart form data
   - Extracts both text message and file attachment
   - Processes and logs message content and file metadata
   - Returns empty HTML response to clear the form

### File Processing Logic
- Handles optional file uploads (can process requests with or without files)
- Reads file content into memory for processing
- Logs detailed information about received files (filename, size)

## Frontend Architecture (index.html)

### Technology Stack
- Backend: FastAPI & Jinja2Templates
- TailwindCSS
- **HTMX**
- **Hyperscript**: JavaScript-like scripting language for DOM manipulation


### Core Features

1. **Auto-expanding Textarea**
   - Dynamically adjusts height based on content
   - Implements Enter key submission (Shift+Enter for new line)
   - Clean, minimalist design with transparent background

2. **File Upload System**
   - Drag-and-drop inspired file selection
   - Real-time preview for image files
   - Visual representation for non-image files
   - Ability to remove selected files before submission

3. **Dynamic Form Handling**
   - Uses HTMX for asynchronous form submission
   - Automatically clears form fields after successful submission
   - Maintains clean user experience without page refreshes

4. **Responsive Design**
   - Dark-themed interface optimized for chat applications
   - Mobile-responsive layout
   - Accessible color scheme and contrast ratios

## Key API Endpoints

### POST /send-message
- **Purpose**: Handles form submissions containing messages and files
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `message` (Form field): Text content of the user's message
  - `file` (File upload): Optional file attachment
- **Response**: Empty HTML content with status 200
- **Functionality**: Logs message and file information to console

## Deployment and Usage Notes

DO NOT run the server, the user is running the server, he will provide feedback.
