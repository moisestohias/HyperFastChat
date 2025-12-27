# TailwindCSS & Layout Strategy: Implementation Rules

This document outlines standard procedures for solving layout and stacking issues encountered with TailwindCSS, especially when integrated with dynamic elements and Hyperscript.

## 1. Escaping Clipping Contexts (Overflow vs. Positioning)
**Problem**: Children with `position: absolute` (like submenus or tooltips) are invisible or cut off when a parent container has `overflow: hidden`, `overflow: auto`, or `overflow: scroll`.
**Rule**: If a child must extend beyond the parent boundary, the parent **MUST** have `overflow: visible`. 
**How to Fix**:
- Change `overflow-hidden` to `overflow-visible` on the immediate parent.
- If the parent *must* remain scrollable (e.g., a sidebar), the child **MUST** use `position: fixed` instead of `position: absolute`.

## 2. Fixed Positioning & Dynamic Anchoring
**Problem**: Using `position: fixed` escapes the overflow clipping but removes the element from the document flow, causing it to lose its relative alignment to the trigger button.
**Rule**: Use Hyperscript to dynamically calculate and set the `top` or `left` properties of fixed elements upon interaction.
**How to Fix**:
```html
<!-- Trigger Button -->
<button _="on click 
             set submenu to next .submenu 
             measure me 
             set submenu.style.top to (it.top as String) + 'px'
             toggle .hidden on submenu">
  Open Menu
</button>

<!-- Fixed Submenu -->
<div class="submenu hidden fixed left-[245px] z-[60]">...</div>
```

## 3. Stacking Contexts (Z-Index Hierarchy)
**Problem**: Dropdowns or fixed overlays appear behind other UI components (like the main chat window or headers).
**Rule**: Always define a clear z-index hierarchy. overlays should exceed the highest base UI layer.
**How to Fix**:
- Sidebar: `z-40`
- Persistent Toggles/Headers: `z-50`
- Context Menus/Popovers: `z-[60]` (Use Tailwind arbitrary values for high-specificity layering).

## 4. Hyperscript & Tailwind Class Syntax
**Problem**: Hyperscript's shorthand dot notation (`add .bg-black/50`) fails on Tailwind classes containing slashes (opacity), dots, or brackets (arbitrary values).
**Rule**: NEVER use dot notation for complex Tailwind classes in Hyperscript.
**How to Fix**:
- **Incorrect**: `add .bg-zinc-700/50 to me`
- **Correct**: `add class 'bg-zinc-700/50' to me`
- **Better**: Use simple semantic classes and move complex styles to `static/style.css`.

## 5. Preventing Interaction Bubbling
**Problem**: Clicking a button inside a clickable container (e.g., a rename button inside a folder header) triggers the parent's event (e.g., collapsing the folder).
**Rule**: Use `halt` or `stopPropagaton` on all interactive sub-elements.
**How to Fix**:
- In Hyperscript: Use the `halt` keyword on the child event.
- In HTML: Add `_="on click halt"` to any button or input nested within a larger clickable area.

## 6. Layout Transitions & Arbitrary Values
**Problem**: Hyperscript parser errors when using arbitrary values in commands like `add .w-[260px]`.
**Rule**: Abstract layout states into dedicated CSS classes.
**How to Fix**:
- Target CSS: `.sidebar-expanded { width: 260px; }`
- Hyperscript: `toggle .sidebar-expanded on #sidebar`
