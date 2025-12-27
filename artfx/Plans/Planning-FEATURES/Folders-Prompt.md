Create a detailed plan (Folders-PLAN.md) for implementing a structured system to organize chat entries using folders (chat containers) by implementing the following:

1. **Data Model**: Define a Pydantic model for chat entries with fields:
   - `id: str`
   - `title: str`
   - `messages: list[dict]`
   - `timestamp: datetime`
   - `provider: str`
   - `model: str`
   - `inference_parameters: dict`
   - `folder_id: str | None` (references the folder the chat belongs to, `None` if unsorted)
   - And whatever other fields you see mandatory
```
inference_parameters = {
  "context_length": 262144,
  "max_completion_tokens": 16384,
  ..
}
```

2. **Folder Management**:
   - Support creation, renaming, and deletion of folders.
   - Each folder has a unique `id` and `name`.

3. **UI Integration**:
   - Add a context menu on each chat entry with a dropdown listing all available folders.
   - On selection, update the chat's `folder_id` to move it into the chosen folder.

4. **Behavior**:
   - Chats with `folder_id: None` appear in the "Recent"  section.
   - Once assigned, the chat is removed from the unorganized list and displayed under the target folder.

Implement the data schema and specify how folder actions are reflected in the UI and data flow.

Details how existing partials will be updated and what new changes that must be implemented, and potential new partials that must be created.
Also detail how to handle edge cases, such as moving chats between folders, deleting folders (and reassigning or deleting contained chats), and ensuring data integrity.
Also detail how to handle the UI using hyperscript. 



---

Created detailed plan for adding folders (chat containers) to organize chats (where each folder can contain multiple chats),
Where we should add an entry (drop down menue) to the context menu to select one of the available folder to move the chat entry to. 
When a chat entry is is assigned to a folder it should move from the current un-organized messages of chats to the selected folder.

First we must a create a data model for the chats entries using pydantic. To represent a chat in the database, with fields such as id, title, messages, timestamp, provider, model, folder_id (category) ...

---


Create a structured system to organize chats using folders (chat containers), where each folder can hold multiple chat entries. Implement a context menu option (move to folder) that allows users to move individual chat entries into any existing folder. When a chat is assigned to a folder, it should be removed from the main unorganized chat list and appear exclusively within the target folder. Ensure seamless navigation and clear visual indication of folder associations.
