## How-To:

## Resolving Double Scrollbars and Layout Shifts
### Context & Background
In dynamic chat applications (FastAPI + HTMX), double scrollbars typically emerge when Markdown/LaTeX rendering (marked.js, KaTeX) generates elements that exceed the viewport or their parent container's dimensions. 

#### Common Triggers:
1. **Viewport Leakage**: If the root `html/body` is not locked to `100vh`, the browser adds a global scrollbar when the inner chat container's height fluctuates during message insertion.
2. **Width Expansion**: Multi-line LaTeX block equations (`$$`) and `<pre>` code blocks often have fixed or "min-content" widths that push the chat bubble beyond the parent's `max-width`, triggering horizontal scrollbars on the entire message area instead of just the bubble.
3. **Tailwind Reset**: Tailwind CSS cancels default browser text wrapping and list styling, which can cause unexpected overflow if not explicitly handled in Markdown containers.

---

### Technical Implementation Rules

#### 1. Viewport Lockdown
- **Rule**: Lock the root container to prevent the browser "ghost" scrollbar.
- **How-To**: 
  - Apply `overflow: hidden; height: 100vh;` to `html` and `body`.
  - Use a full-height wrapper: `<div class="h-screen flex flex-col overflow-hidden">`.

#### 2. Contained Component Scrolling
- **Rule**: Restrict scrolling to the specific message list area only.
- **How-To**:
  - The message list div MUST have `flex-1` and `overflow-y-auto`.
  - All other UI elements (header, input bar) should have fixed or intrinsic heights.

#### 3. Horizontal Overflow Defense
- **Rule**: Force wide elements (Math/Code) to scroll *inside* their own blocks.
- **How-To**:
  - Apply `max-width: 100%`, `overflow-x: auto`, and `overflow-y: hidden` to `.katex-display` and `pre` tags.
  - Set `white-space: normal` on the inner `.katex` container to allow internal wrapping if possible, but rely on `overflow-x` for strict containment.

#### 4. Text Wrapping & Breaking
- **Rule**: Prevent long continuous strings (URLs, unspaced text) from breaking layout.
- **How-To**:
  - Use `overflow-wrap: break-word`, `word-wrap: break-word`, and `word-break: break-word` on the `.markdown-content` container.

#### 5. Unified Dark Mode Scrollbars
- **Rule**: Prevent "white flash" default scrollbars on math/code blocks.
- **How-To**:
  - Define a global `.custom-scrollbar` utility for `::-webkit-scrollbar` and apply it to the main chat list AND all `pre/.katex-display` blocks.
  - Set `scrollbar-width: thin` for Firefox support.
