Refact @index.html into partials, specifically base.html and chat_input_field.html, 
Note, currently we don't have response template to send back response to use, So, Add to add chat_response.html template and chat.html that contains common elements between   

Refactor `@index.html` into reusable partials: create `base.html` for shared layout structure, `chat_input_field.html` for the input component, and introduce `chat_response.html` as a template for rendering responses. Additionally, create `chat.html` to encapsulate common elements shared across chat-related pages, ensuring a modular and maintainable structure.

---
for now, for every request the system must respond by echoing back the request content, implement this

---

Great work, now there are two issues we need to solve:
1. The images are not displayed in the messages (currently the alt text is displayed)
2. new lines are not cupated, for input text containing multiple lines the entire text get joined inot a single long line (in both user messages and bot responses)
Fix these

---

Update chat.html to place the chat input field "Input Area" in a fixed position at the bottom of the viewport so it is always visible, even when the chat history becomes long and scrolls. The message list should scroll independently, but the input bar should never scroll out of view.
