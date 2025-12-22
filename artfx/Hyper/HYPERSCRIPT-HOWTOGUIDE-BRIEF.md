# Hyperscript Development Rules & Best Practices

To prevent syntax errors and runtime failures with Hyperscript, follow these rules:

### 1. Externalize Complex Logic
**Rule**: Never put multi-line logic or complex `if/for` loops inside a `_=""` attribute.
**How To**: Move the logic to a global function in a `.js` file and call it from Hyperscript:
`_="on load renderMessage(me)"`

### 2. Handle Multi-line Strings via Data Attributes
**Rule**: Do not pass Jinja2 variables (like `{{ message }}`) directly into Hyperscript string literals.
**How To**: Store the data in a `data-*` attribute and retrieve it using `.getAttribute()`:
`<button data-content="{{ msg }}" _="on click callJS(my.getAttribute('data-content'))">`

### 3. Use Safe String Passing
**Rule**: Avoid `{{ message|e }}` or `{{ message|tojson }}` inside Hyperscript attributes as they often conflict with the attribute's own quotes.
**How To**: Use the Data Attribute rule (Rule #2) combined with standard HTML entity escaping.

### 4. Prefer `renderMessage` Fallbacks
**Rule**: Do not assume external libraries (Marked, KaTeX) are ready at the exact moment of a partial swap.
**How To**: Implement a retry/timeout mechanism in the JS helper function to wait for `window.marked` or `window.hljs` to be defined before execution.

### 5. Relative DOM References
**Rule**: Avoid hardcoded IDs for components that repeat (like chat messages).
**How To**: Use Hyperscript's relative selectors like `me`, `my`, `closest`, or `next`:
`_="on click toggle .active on closest .bubble"`

### 6. Clean Syntax for Method Calls
**Rule**: Avoid the `call` keyword for simple global function calls if it's not strictly necessary.
**How To**: Use `on event functionName(args)` instead of `on event call functionName(args)`.
