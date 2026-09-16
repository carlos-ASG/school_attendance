---
name: alpine
description: Use when writing Alpine.js markup or JS — x-data, x-show, x-if, x-bind (:), x-on (@), x-model, x-for, x-transition, x-ref/$refs, $dispatch, $store, $watch, x-cloak, x-teleport, Alpine.data()/Alpine.store() — or when the user mentions Alpine, adding interactivity to Django/HTMX/cotton templates, or Alpine/HTMX interop in this repo.
license: MIT
---

# Alpine.js

Alpine adds reactivity directly in HTML: declare state with `x-data`, then read
and mutate it from other directives. Everything depends on an `x-data`
ancestor. Official docs: https://alpinejs.dev

Alpine is already loaded in this repo via the shadcn/django + cotton setup
(co-load `django-cotton` for component syntax, `django6-htmx` for fragments).
Never add a second copy of Alpine or call `Alpine.start()` more than once.

## Core model

```html
<div x-data="{ open: false }">
    <button @click="open = ! open">Toggle</button>
    <div x-show="open">Content...</div>
</div>
```

- State lives in `x-data` (an inline JS object or a named component registered
  with `Alpine.data()`).
- Child scopes inherit parent scope (nested `x-data` shadows like JS closures).
- Every reactive directive below re-runs when the state it reads changes.

## Directive cheat sheet

| Goal                                        | Directive                                   |
| ------------------------------------------- | ------------------------------------------- |
| Local component state                        | `x-data="{ open: false }"`                  |
| Init logic on load (fetch, listeners)        | `x-init="..."` or `init()` in the data object |
| Toggle visibility (stays in DOM)             | `x-show="open"`                             |
| Toggle visibility (add/remove DOM node)      | `<template x-if="open">…</template>`        |
| Render list                                  | `<template x-for="item in items" :key="item.id">` |
| Bind attribute / class / style               | `:class="open && 'hidden'"`                 |
| Listen to events                             | `@click="save"` (modifiers: `.prevent`, `.stop`, `.outside`, `.window`, `.debounce.500ms`, `.once`, …) |
| Two-way input binding                        | `x-model="name"` (`.lazy`, `.number`, `.debounce`) |
| Set text / HTML                              | `x-text="title"` / `x-html="html"` (trusted only) |
| Animate show/hide                            | `x-transition` (helpers or CSS-class syntax) |
| Direct DOM access                            | `x-ref="el"` + `$refs.el`                   |
| Watch state changes                          | `$watch('open', v => …)` (lazy, old value) / `x-effect="…"` (immediate, no old value) |
| Global cross-component state                 | `Alpine.store('x', {...})` + `$store.x`     |
| Component-to-component events                | `$dispatch('event', data)` + `@event.window` |
| Wait for DOM update                          | `$nextTick(() => …)`                        |
| Reusable component with `x-model` API        | `x-modelable="count"`                       |
| Unique IDs in repeated components            | `x-id="['name']"` + `$id('name')`           |
| Modals / break out of z-index                | `<template x-teleport="body">`              |
| Prevent flash before Alpine loads            | `x-cloak` (+ `[x-cloak] { display: none !important; }` CSS) |
| Exclude subtree from Alpine                  | `x-ignore`                                  |

## Detailed references

| Topic                                                        | File                            |
| ------------------------------------------------------------ | ------------------------------- |
| Install, state (local/global), templating, events, lifecycle | `references/essentials.md`      |
| Core directives: data, init, show, if, bind, on, text, html, model, modelable, for | `references/directives-core.md` |
| Other directives: transition, effect, ignore, ref, cloak, teleport, id | `references/directives-advanced.md` |
| All magics: $el, $refs, $store, $watch, $dispatch, $nextTick, $root, $data, $id | `references/magics.md` |
| Events modifier reference (prevent/stop/outside/window/debounce/…) | covered in `references/directives-core.md` (x-on) |

## Examples

| Example                                                          | File                     |
| ---------------------------------------------------------------- | ------------------------ |
| Dropdown + modal (show/if, outside click, transition, teleport)   | `examples/dropdown.md`   |
| Global store + reusable `Alpine.data` component                   | `examples/store-components.md` |

## Gotchas

- **`x-if` and `x-for` must live on `<template>` tags** whose content has
  exactly **one root element**.
- **`x-transition` only works with `x-show`, never `x-if`.**
- **Flash of unstyled content**: any `x-show`/`x-text` element that should start
  hidden needs `x-cloak` plus the `[x-cloak] { display: none !important; }` CSS
  rule.
- **`$refs` is static in V3** — no dynamic `:x-ref` inside `x-for`; the literal
  expression string becomes the ref name.
- **`$watch` infinite loop**: mutating the watched property inside its own
  callback errors out.
- **CDN script needs `defer`**; register `Alpine.data`/`Alpine.store` inside
  `alpine:init` (or between `import` and `Alpine.start()` in a bundle).
- **Alpine + HTMX interop**: Alpine scans the page once at load —
  HTMX-swapped fragments containing `x-data` are *not* initialized
  automatically. Hook `htmx:load` and call `Alpine.initTree(e.detail.elt)` (see
  the `django6-htmx` skill for fragment workflows).
- **`x-html` is XSS-prone** — only for trusted, never user-provided content.
- Alpine expressions are evaluated in markup — keep them small; move logic to
  `Alpine.data` components when inline expressions get long.
