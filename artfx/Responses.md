I've fixed the "double scrollbar" issue and improved the rendering of long equations and code blocks.

## What caused the issue:
- *Body Scrollbar*: The browser's default scrollbar was appearing on the body because the chat container was slightly competing for height, or content was leaking out. I've now enforced `overflow: hidden` on the html and body levels to ensure only the chat area scrolls.
- *Width Overflow*: Wide LaTeX equations ($$ ... $$) or long code blocks were pushing the message bubble's width beyond the chat area, which triggered a horizontal scrollbar on the entire message window.

## Improvements Made:
- **Enforced Viewport Bounds**: The application is now strictly bounded to the screen height (100vh), preventing the outer "ghost" scrollbar.
- **Localized Overflow**: Wide math equations and code blocks now have their own horizontal scrollbars inside the message bubble. This keeps the chat window clean while allowing you to scroll through long formulas.
- **Consistent Styling**: Applied the custom dark scrollbar style to the code and math blocks as well, so the UI feels cohesive.
Text Wrapping: Added overflow-wrap: break-word to ensure that even long strings of text without spaces won't break the layout.
You don't need to change any CDN links; the logic I placed in `chat_response.html` previously will now work even better with these global styles in place.