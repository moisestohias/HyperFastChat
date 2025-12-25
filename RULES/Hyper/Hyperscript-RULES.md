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
- **Rule**: Every line in a Hyperscript block must begin with a valid command (e.g., `add`, `remove`, `focus`, `call`).
- **How to Fix**: Use the structured `focus()` command: `focus() on #selector`.

