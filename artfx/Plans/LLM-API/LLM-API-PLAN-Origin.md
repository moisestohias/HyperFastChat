# LLM-API Integration Plan: LLMConnect

This plan outlines the steps to integrate the `LLMConnect` library into the existing chat application, replacing the current simulated echo logic with real-world LLM capabilities.

## 1. Library Refactoring
The `LLMConnect` library has been decoupled from its original environment-specific dependencies to ensure compatibility with a standard FastAPI web server.

- **Dependency Removal**: Removed all logic related to external session tracking and platform-specific file persistence from `LLMConnect/top.py`.
- **Memory-Based State**: The library now relies exclusively on in-memory message history passed during client initialization, aligning with the FastAPI `chats` state management.
- **Factory Update**: Refactored `APIClientFactory` to remove all legacy parameters, streamlining it for web integration.

## 2. API Key Management
The `APIClientFactory` expects API keys to be available via environment variables (e.g., `AIMLAPI_API`, `GROQ_API_KEY`).

- Create a `.env` file in the project root with the necessary keys.
- Use `python-dotenv` in `main.py` to load these configuration values at startup.

## 3. Client Initialization & Management
The integration will use the `APIClientFactory` to dynamically create asynchronous clients based on the user's provider and model selection.

### Integration Strategy
- Implement a helper `get_llm_client(conv_id)` in `main.py` that:
    1. Retrieves the current provider and model from the `chats[conv_id]` metadata.
    2. Instantiates a provider-specific `AsyncAPIClient` via the factory.

## 4. Message Flow & State Synchronization
The application's global `chats` dictionary remains the source of truth for conversation history.

### Workflow:
1. **Message Submission**: `/chat/{conv_id}/send-message` appends the user content and an empty assistant placeholder to the history.
2. **Background Task**: `run_chatbot_logic(conv_id)` is triggered.
3. **Client Setup**: The task initializes the `AsyncAPIClient` with history from `chats[conv_id]["messages"]`.
4. **Streaming Execution**: Calls `await client.chat(user_msg, stream=True)` to obtain an async generator.
5. **UI Update**: Tokens are written to the `assistant` message in the shared state as they arrive from the LLM.
6. **Completion**: The message status is updated to `complete` once the stream finishes.

## 5. Continuity & UX Preservation
The existing SSE polling mechanism (`/bot-stream`) automatically reflects backend changes in the UI.

- **Seamless Transition**: The polling logic remains unchanged, as it only monitors the `assistant` message content in `chats`.
- **Session Resilience**: Reloading the page during generation re-establishes the SSE connection, which continues polling the shared state updated by the background task.

## 6. Actionable Implementation Steps

### Phase 1: Environment Setup
- [ ] Implement `.env` file for API keys.
- [ ] Add `python-dotenv` to the project and initialize in `main.py`.

### Phase 2: Core Logic Replacement
- [ ] Update `run_chatbot_logic` in `main.py` to use `APIClientFactory`.
- [ ] Replace token simulation loop with the `AsyncAPIClient.chat` streaming loop.
- [ ] Implement error handling within the background task to update UI status on failure.

### Phase 3: Validation
- [ ] Verify dynamic model switching via the UI dropdown.
- [ ] Test end-to-end streaming with live LLM responses.
- [ ] Ensure persistence across page reloads during active generation.
