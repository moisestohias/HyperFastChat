# Hyperscript & Tailwind Implementation Case Study: Key Mistakes & Prevention Rules

This document outlines critical failures encountered during the implementation of the Chat App's sidebar and state management. Follow these rules to prevent recurring syntax errors and runtime failures.

## 1. Tailwind Arbitrary Values & Hyperscript DOT Notation
**Mistake**: Attempting to use Tailwind's arbitrary value brackets (e.g., `.w-[260px]`) within Hyperscript's shorthand selector syntax.
- **Example of Failure**: `add .w-[260px] to #sidebar`
- **Result**: `Expected 'end' but found '['`
- **Rule**: **NEVER** use Tailwind classes containing brackets (`[` or `]`) in Hyperscript's dot notation. Hyperscript's parser interprets brackets as attribute or property accessors.
- **How to Fix**: Use custom CSS classes for layout transitions. 
  - Define `.sidebar-w-expanded { width: 260px; }` in your CSS.
  - Use `add .sidebar-w-expanded to #sidebar` in Hyperscript.

## 2. Advanced CSS Pseudo-Selectors
**Mistake**: Using complex CSS pseudo-selectors like `:not()` combined with Hyperscript keywords.
- **Example of Failure**: `remove .active from .item:not(me.parentElement)`
- **Result**: `r.apply is not a function` (Parser/Runtime mismatch)
- **Rule**: Keep selectors simple. Hyperscript excels at sequential logic; use it instead of complex CSS filters.
- **How to Fix**: Break the logic into two clear steps:
  1. `remove .active from .items`
  2. `add .active to my parentElement`

## 3. Event Naming & Semantic Accuracy
**Mistake**: Using non-standard or deprecated event expressions for common UI patterns.
- **Example of Failure**: `on click outside`
- **Result**: `Unexpected Token: outside`
- **Rule**: Always use the modern, standard Hyperscript event modifiers for boundary detection.
- **How to Fix**: Use `on click elsewhere` to detect clicks outside an element (e.g., for closing dropdowns or context menus).

## 4. DOM Property Referencing (Lexical Scope)
**Mistake**: Referencing DOM properties like `parentElement` or `next` without explicit ownership keywords.
- **Example of Failure**: `send event to parentElement`
- **Result**: `parentElement is null` (Interpreted as an undefined local variable).
- **Rule**: In Hyperscript, DOM properties belonging to the current element must be prefixed with `my`.
- **How to Fix**: Use `my parentElement`, `my nextElementSibling`, or `me.parentElement`.

## 5. Class Manipulation Keywords
**Mistake**: Forgetting that Hyperscript requires the `class` keyword when dealing with quoted strings or dynamic classes, while allowing the dot `.` for literals.
- **Ambiguity**: `add 'my-class' to me` vs `add .my-class to me`.
- **Rule**: If a class name contains special characters and *must* be quoted, you must use the `class` keyword.
- **How to Fix**: Use `add class 'special-char-[class]' to target`. However, referring to **Rule 1**, the best practice is to avoid special characters in manipulated classes entirely by using custom CSS abstractions.
 
## 6. Scope & Referencing
**Mistake**: Mixing `me`, `my`, and `my parentElement` in ways that confuse the lexical scope, especially within nested templates.
- **Rule**: Be explicit about the target element to avoid ambiguity during HTMX swaps.
- **How to Fix**: 
  - Use `me` to refer to the element currently executing the event.
  - Use `my` as a possessive (e.g., `my style.height` or `my parentElement`).
  - Use IDs for global targets (e.g., `#sidebar`) and relative references for local UI clusters.

## 7. Focus & Command-First Syntax
**Mistake**: Starting a line with a selector or a naked method call like `#id.focus()`.
- **Example of Failure**: `#rename-input.focus()`
- **Result**: `Unexpected Token: #` (Hyperscript expects a command keyword at the start of a line).
- **Rule**: Every line in a Hyperscript block must begin with a valid command (e.g., `add`, `remove`, `set`, `call`). Note that `focus` is not a command.
- **How to Fix**: Use the `call` command to invoke the native DOM `.focus()` method: `call #selector.focus()`.

## 8. Multi-Token Selectors & Selector Ambiguity
**Mistake**: Using space-separated descendant selectors directly in commands like `add`, `remove`, or `toggle`.
- **Example of Failure**: `remove .hidden from closest .message-container .message-actions`
- **Result**: `Unexpected Token: .message-actions` (The parser fails at the space).
- **Rule**: Avoid multi-token (ancestor/descendant) space-separated selectors in commands. Hyperscript expects a single target reference.
- **How to Fix**: Use explicit scoping keywords to find descendants:
  - Use the `in` keyword: `remove .hidden from <.message-actions/> in #message-id`
  - Use relative navigation: `add .hidden to my parentElement`

## 9. Native DOM Methods & The `call` Keyword
**Mistake**: Invoking native JavaScript DOM methods (like `scrollIntoView`, `getBoundingClientRect`, `scrollTo`) as if they were Hyperscript commands.
- **Example of Failure**: `wait 10ms then scrollIntoView({behavior:'smooth'})`
- **Result**: `'scrollIntoView' is null` (Interpreted as an undefined local variable).
- **Rule**: Any native DOM method not natively handled as a command **MUST** be invoked via the `call` keyword and prefixed with an element reference (`me` or `my`).
- **How to Fix**: 
  - `call my.scrollIntoView({behavior:'smooth'})`
  - `call <.target/>.getBoundingClientRect()`

## 10. Tailwind Slash Notation (Opacity/Spacing)
**Mistake**: Using Tailwind classes that contain slashes (e.g., `.bg-zinc-700/50` or `.p-2/5`) within Hyperscript's shorthand dot notation.
- **Example of Failure**: `add .bg-zinc-700/50 to me`
- **Result**: `Unexpected Token: /` (The parser treats `/` as a mathematical operator, not part of the class name).
- **Rule**: **NEVER** use dot notation for classes containing slashes. 
- **How to Fix**:
  1. Use the `class` keyword with quotes: `add class 'bg-zinc-700/50' to me`.
  2. Better: Avoid slashes in manipulated classes by using a solid color class or a custom CSS abstraction (e.g., `add .bg-zinc-700 to me`).
