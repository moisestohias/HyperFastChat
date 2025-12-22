# Hyperscript Development Rules & Best Practices

This guide provides explicit rules for integrating **Hyperscript** with **HTMX** and **Jinja2**. These rules prevent common syntax errors caused by multi-line strings, special characters, and race conditions during partial swaps.

---

### 1. Externalize Complex Logic
**Issue**: Writing complex loops, conditionals, or DOM manipulations inside the HTML `_=""` attribute is brittle and prone to "Uncaught Syntax Error: Expected ')'" failures.
**Rule**: If logic exceeds one line or involves DOM creation, move it to a global JavaScript function.
- **❌ BROKEN**: `_="on load if x then do A else do B end for item in items ..."`
- **✅ FIXED**: `_="on load myJSFunction(me)"`
- **Helper**: Define functions on `window` in a dedicated `/static/utils.js` file.

### 2. Pass Multi-line Data via Data Attributes
**Issue**: Passing Jinja2 variables like `{{ message }}` directly into Hyperscript literals (e.g., `writeText('{{ message }}')`) will fail if the message contains newlines, single quotes, or backslashes.
**Rule**: Never put raw multi-line template variables inside Hyperscript strings. Store them in `data-*` attributes first.
- **❌ BROKEN**: `_="on click call navigator.clipboard.writeText('{{ message }}')"`
- **✅ FIXED**: 
  ```html
  <div data-content="{{ message }}" 
       _="on click copyToClipboard(my.getAttribute('data-content'))">
  ```

### 3. Avoid String Filtering Inside Attributes
**Issue**: Using Jinja filters like `|e`, `|tojson`, or `|safe` inside a Hyperscript attribute often results in nested quote conflicts that are impossible for the browser to parse.
**Rule**: Use standard HTML data-attributes to hold the value. The browser automatically handles the encoding/decoding of the attribute value.
- **How To**: Just use `<div data-msg="{{ message }}">` and access it via `my.dataset.msg` or `my.getAttribute('data-msg')`.

### 4. Implement Library Availability Fallbacks
**Issue**: When HTMX swaps in a new partial, the `on load` event triggers immediately. If libraries like `marked.js` or `katex` are being loaded asynchronously, the script will crash.
**Rule**: JavaScript helper functions should include a small retry/timeout loop to check for the existence of required global objects.
- **Example Pattern**:
  ```javascript
  window.render = (el) => {
    if (!window.marked) return setTimeout(() => window.render(el), 50);
    el.innerHTML = marked.parse(el.innerText);
  }
  ```

### 5. Use Relative Selectors for Component Logic
**Issue**: Hand-coding IDs (e.g., `#message-1`) makes templates non-reusable and prone to collisions during HTMX swaps.
**Rule**: Use Hyperscript's contextual keywords to resolve elements relative to the trigger.
- **Keywords**:
  - `me` / `my`: The current element.
  - `closest .className`: Traverses up the DOM.
  - `next .className`: Finds the next sibling.
  - `previous <div/>`: Finds the previous matching tag.

### 6. Clean Syntax for Global Calls
**Rule**: In Hyperscript, global functions can be called directly. The `call` and `window.` keywords are usually optional but can clarify scope.
- **Preferred**: `_="on click myFunction(me)"`
- **Explicit**: `_="on click call window.myFunction(me)"` (Use this if `myFunction` conflicts with a Hyperscript keyword).

### 7. Quote Escape in HTML Attributes
**Rule**: When you *must* use nested quotes in a Hyperscript attribute, use `&quot;` or `&apos;` to prevent the browser from closing the `_=""` attribute prematurely.
- **Example**: `set btn.innerHTML to '<svg fill=&quot;none&quot; ...>'`
